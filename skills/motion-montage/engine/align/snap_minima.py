#!/usr/bin/env python3
"""Refine word boundaries inside each phrase by snapping them to the nearest
energy dip in the real voice (the short gap between two words).
python3 snap_minima.py in.json voice.wav out.json"""
import json, sys
import numpy as np
import librosa
from scipy.signal import argrelextrema

wj, wav, outp = sys.argv[1:4]
d = json.load(open(wj, encoding="utf-8")); W = d["words"]
y, sr = librosa.load(wav, sr=16000, mono=True)
hop = 0.005
rms = librosa.feature.rms(y=y, frame_length=320, hop_length=80)[0]
db = 20 * np.log10(rms + 1e-9)
db_s = np.convolve(db, np.ones(5) / 5, mode="same")
mins = argrelextrema(db_s, np.less_equal, order=6)[0]
peak = np.percentile(db_s, 90)
# a usable dip: at least 9 dB below the local level around it
def depth(i):
    a, b = max(0, i - 30), min(len(db_s), i + 30)
    return min(db_s[a:i + 1].max(), db_s[i:b].max()) - db_s[i]
cand = np.array([i for i in mins if depth(i) >= 9])
ct = cand * hop
snapped = 0
for k in range(len(W) - 1):
    a, b = W[k], W[k + 1]
    if b["s"] - a["e"] >= 0.12:      # a real pause, already anchored
        continue
    bnd = (a["e"] + b["s"]) / 2
    lo = max(a["s"] + 0.08, bnd - 0.2); hi = min(b["e"] - 0.08, bnd + 0.2)
    sel = ct[(ct > lo) & (ct < hi)]
    if len(sel):
        # prefer the deepest dip, weighted toward the estimate
        best = min(sel, key=lambda x: abs(x - bnd) * 20 - depth(int(round(x / hop))))
        a["e"] = round(float(best) - 0.01, 3); b["s"] = round(float(best) + 0.01, 3)
        snapped += 1
for k in range(1, len(W)):
    if W[k]["s"] < W[k - 1]["s"] + 0.06:
        W[k]["s"] = round(W[k - 1]["s"] + 0.06, 3)
    W[k - 1]["e"] = round(min(W[k - 1]["e"], W[k]["s"]), 3)
d["words"] = W; d["backend"] += "+dip-snap"
json.dump(d, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{snapped} word boundaries snapped to energy dips (of {len(W)-1}); {len(cand)} dips found")
