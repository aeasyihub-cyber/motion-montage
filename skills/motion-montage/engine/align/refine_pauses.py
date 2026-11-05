#!/usr/bin/env python3
"""Snap DTW word times to the real pauses at punctuation, then re-time the words
between anchors piecewise-linearly.  python3 refine_pauses.py words.json voice.wav out.json"""
import json, re, sys
import numpy as np
import librosa

wj, wav, outp = sys.argv[1:4]
d = json.load(open(wj, encoding="utf-8"))
W = d["words"]
y, sr = librosa.load(wav, sr=16000, mono=True)
hop = 0.01
rms = librosa.feature.rms(y=y, frame_length=320, hop_length=160)[0]
db = 20 * np.log10(rms + 1e-9)
thr = np.percentile(db, 55) - 16
sil = db < thr
# pauses >= 0.14 s
pauses, k = [], 0
while k < len(sil):
    if sil[k]:
        j = k
        while j < len(sil) and sil[j]:
            j += 1
        if (j - k) * hop >= 0.14:
            pauses.append(((k) * hop, j * hop))
        k = j
    else:
        k += 1
print(f"{len(pauses)} pauses found (thr {thr:.1f} dB)")
punct = re.compile(r"[،,.:…؟!]$")
anchors = {}  # word index -> (end_time, next_start)
used = -1
for i, w in enumerate(W[:-1]):
    if not punct.search(w["w"]):
        continue
    t = w["e"]
    best, bd = None, 9
    for pi in range(used + 1, len(pauses)):
        ps, pe = pauses[pi]
        dd = abs(ps - t)
        if ps - t > 1.2:
            break
        if dd < bd:
            best, bd = pi, dd
    if best is not None and bd <= 1.0:
        anchors[i] = pauses[best]
        used = best
# build anchor list of (old_time, new_time) for piecewise remap
pts = [(0.0, 0.0)]
for i, (ps, pe) in sorted(anchors.items()):
    pts.append((W[i]["e"], ps))
    pts.append((W[i + 1]["s"], pe))
pts.append((W[-1]["e"], W[-1]["e"]))
pts = sorted(set(pts))
# enforce monotonic
clean = [pts[0]]
for o, n in pts[1:]:
    if o > clean[-1][0] and n > clean[-1][1]:
        clean.append((o, n))
xo, xn = zip(*clean)
remap = lambda t: float(np.interp(t, xo, xn))
for w in W:
    w["s"], w["e"] = round(remap(w["s"]), 3), round(remap(w["e"]), 3)
for i, (ps, pe) in anchors.items():
    W[i]["e"] = round(ps, 3)
    W[i + 1]["s"] = round(pe, 3)
for k in range(1, len(W)):
    if W[k]["s"] < W[k - 1]["s"] + 0.05:
        W[k]["s"] = round(W[k - 1]["s"] + 0.05, 3)
    W[k - 1]["e"] = round(min(W[k - 1]["e"], W[k]["s"]), 3)
d["words"] = W
d["backend"] += "+pause-snap"
json.dump(d, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(anchors)} punctuation anchors snapped")
