#!/usr/bin/env python3
"""Phrase-to-pause dynamic-programming alignment (no ASR needed).

Splits the script into punctuation phrases, finds the real pauses in the voice,
and picks the monotonic mapping of phrase groups to speech-chunk groups whose
durations best match the letter counts. Words are then spread inside each unit
by letter count. Non-speech tails (laughs, breaths) are left out when a unit is
much longer than its text predicts.
  python3 dp_align.py voice.wav script.txt out.json
"""
import json, math, re, sys
import numpy as np
import librosa

wav, scr, outp = sys.argv[1:4]
words = []
for raw in open(scr, encoding="utf-8").read().splitlines():
    raw = re.sub(r"^#\w+\s+", "", raw.strip())
    if raw:
        toks = [t.replace("*", "") for t in raw.split()]
        for k, t in enumerate(toks):
            words.append(dict(w=t, end=(k == len(toks) - 1) or bool(re.search(r"[،,.:…!؟]$", t))))
letters = lambda w: max(1, len(re.sub(r"[ً-ْـ\W_]", "", w)))
phr, cur = [], []
for i, w in enumerate(words):
    cur.append(i)
    if w["end"]:
        phr.append(cur); cur = []
if cur: phr.append(cur)
PL = [sum(letters(words[i]["w"]) + 1.2 for i in p) for p in phr]

y, sr = librosa.load(wav, sr=16000, mono=True)
hop = 0.01
db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=320, hop_length=160)[0] + 1e-9)
db = np.convolve(db, np.ones(3) / 3, mode="same")
thr = np.percentile(db, 60) - 20
sil = db < thr
seg, k = [], 0                      # speech chunks [s,e]
while k < len(sil):
    if not sil[k]:
        j = k
        while j < len(sil) and not sil[j]: j += 1
        seg.append([k * hop, j * hop]); k = j
    else: k += 1
# merge chunks separated by < 0.16 s (not a real pause)
ch = [seg[0]]
for s, e in seg[1:]:
    if s - ch[-1][1] < 0.16: ch[-1][1] = e
    else: ch.append([s, e])
ch = [c for c in ch if c[1] - c[0] > 0.06]
CD = [e - s for s, e in ch]
rate = sum(CD) / sum(PL)           # seconds per letter-unit
n, m = len(phr), len(ch)
print(f"{n} phrases, {m} speech chunks, rate {rate*1000:.1f} ms/unit")
INF = 1e18
G = 4
dp = np.full((n + 1, m + 1), INF); bk = {}
dp[0, 0] = 0
for i in range(n + 1):
    for j in range(m + 1):
        if dp[i, j] >= INF: continue
        for a in range(1, G + 1):
            if i + a > n: break
            exp_d = sum(PL[i:i + a]) * rate
            for b in range(1, G + 1):
                if j + b > m: break
                act = ch[j + b - 1][1] - ch[j][0]
                c = math.log(act / exp_d) ** 2 * 10 + 0.6 * (a - 1) + 0.9 * (b - 1)
                if act > exp_d * 1.5: c -= min(2.0, (act / exp_d - 1.5)) * 3  # allow non-speech tails
                v = dp[i, j] + c
                if v < dp[i + a, j + b]:
                    dp[i + a, j + b] = v; bk[(i + a, j + b)] = (i, j)
i, j, units = n, m, []
while (i, j) != (0, 0):
    pi, pj = bk[(i, j)]; units.append((pi, i, pj, j)); i, j = pi, pj
units.reverse()
out = [None] * len(words)
for (p0, p1, c0, c1) in units:
    idx = [w for p in phr[p0:p1] for w in p]
    chunks = ch[c0:c1]
    tot = sum(e - s for s, e in chunks)
    need = sum(PL[p0:p1]) * rate
    use = min(tot, need * 1.35)   # leave laughs/breath tails out
    # timeline of speech-only seconds -> real time
    def real(x):
        for s, e in chunks:
            if x <= e - s: return s + x
            x -= e - s
        return chunks[-1][1]
    wts = [letters(words[k]["w"]) + 1.2 for k in idx]; W = sum(wts); x = 0
    for k, wt in zip(idx, wts):
        d = use * wt / W
        out[k] = dict(w=words[k]["w"], s=round(real(x), 3), e=round(real(x + d * 0.98), 3)); x += d
json.dump(dict(words=out, text=" ".join(w["w"] for w in words), backend="dp-phrase"), open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(units)} units; cost {dp[n, m]:.2f}")
