#!/usr/bin/env python3
"""motion-montage · envelope.py — per-frame voice loudness for waveforms / audio-reactive motion.

  python3 envelope.py voice-clean.wav --fps 60 --out voice-env.js

Writes `window.VOICE_ENV = [0..1 per frame]` (smoothed RMS, 95th-percentile normalised).
Load it in the composition with <script src="voice-env.js"></script>.
"""
import argparse, json, subprocess
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio'); p.add_argument('--fps', type=int, default=60); p.add_argument('--out', default='voice-env.js')
    a = p.parse_args()
    sr = 48000
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.audio, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    hop = sr // a.fps
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    sm = np.zeros_like(rms); s = 0.0
    for i, v in enumerate(rms):            # fast attack, slower release — reads like a VU meter
        s = v if v > s else s * 0.82 + v * 0.18
        sm[i] = s
    sm = np.clip(sm / (np.percentile(sm, 95) + 1e-9), 0, 1)
    open(a.out, 'w').write('window.VOICE_ENV = ' + json.dumps([round(float(v), 3) for v in sm]) + ';\n')
    print(f'{n} frames → {a.out}')


if __name__ == '__main__':
    main()
