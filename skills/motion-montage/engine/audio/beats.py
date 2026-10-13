#!/usr/bin/env python3
"""motion-montage · beats.py — find the beat grid of a music track so cuts land on it.

  python3 beats.py track.mp3 --out beats.json [--bpm-min 70 --bpm-max 180]

Output: {"bpm": 120.2, "beats": [..s], "downbeats": [..s], "onsets": [..s], "drops": [..s]}
  beats      → where to place cuts and hits
  downbeats  → where to change scenes (every bar)
  onsets     → strong transients (accents for pops/scale punches)
  drops      → biggest energy jumps (the payoff moment: hero shot / title slam)
numpy only (spectral-flux onsets + autocorrelation tempo + phase fit).
"""
import argparse, json, subprocess
import numpy as np

SR = 22050
HOP = 256


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def flux(x):
    n = 1024
    win = np.hanning(n)
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(x, (n // 2, n // 2)), n)[::HOP] * win
    mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)) * 10)
    d = np.diff(mag, axis=0, prepend=mag[:1])
    f = np.maximum(d, 0).sum(axis=1)
    f = f - np.convolve(f, np.ones(16) / 16, mode='same')
    return np.maximum(f, 0), mag.sum(axis=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('track'); p.add_argument('--out', default='beats.json')
    p.add_argument('--bpm-min', type=float, default=70); p.add_argument('--bpm-max', type=float, default=180)
    a = p.parse_args()
    x = load(a.track)
    f, energy = flux(x)
    fps = SR / HOP
    ac = np.correlate(f, f, mode='full')[len(f) - 1:]
    lags = np.arange(len(ac))
    lo, hi = int(fps * 60 / a.bpm_max), int(fps * 60 / a.bpm_min)
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60 * fps / lag
    # phase: choose offset maximizing flux on the grid
    best, phase = -1, 0
    for ph in range(lag):
        s = f[ph::lag].sum()
        if s > best: best, phase = s, ph
    beats = np.arange(phase, len(f), lag) / fps
    # downbeat: which of 4 phases has the most energy
    bsum = [f[int(round(b * fps))::lag * 4].sum() if int(round(b * fps)) < len(f) else 0 for b in beats[:4]]
    db0 = int(np.argmax(bsum)) if bsum else 0
    downbeats = beats[db0::4]
    thr = np.percentile(f, 97)
    onsets = [i / fps for i in range(1, len(f) - 1) if f[i] > thr and f[i] >= f[i - 1] and f[i] >= f[i + 1]]
    # drops: energy jump over 2 s windows
    w = int(fps * 2)
    e = np.convolve(energy, np.ones(w) / w, mode='same')
    jump = np.zeros_like(e); jump[w:] = e[w:] - e[:-w]
    drops = []
    for i in np.argsort(jump)[::-1]:
        tt = float(i / fps)
        if jump[i] <= 0 or len(drops) == 3: break
        if all(abs(tt - d) > 4.0 for d in drops): drops.append(tt)
    drops = sorted(round(d, 2) for d in drops)
    out = dict(bpm=round(float(bpm), 2), beats=[round(float(b), 3) for b in beats],
               downbeats=[round(float(b), 3) for b in downbeats], onsets=[round(o, 3) for o in onsets], drops=drops)
    json.dump(out, open(a.out, 'w'), indent=1)
    print(f'{a.track}: {out["bpm"]} BPM, {len(beats)} beats, {len(onsets)} onsets, drops at {drops} → {a.out}')


if __name__ == '__main__':
    main()
