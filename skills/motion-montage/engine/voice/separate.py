#!/usr/bin/env python3
"""motion-montage · separate.py: pull the voice out of a finished video or mix.

Use it when the user wants an existing video remade and the clean voice file is gone.

  python3 separate.py input.mp4 --out voice.wav [--model UVR-MDX-NET-Voc_FT.onnx]

Backend: sherpa-onnx OfflineSourceSeparation with a UVR MDX vocal model. It runs on the CPU,
and the model downloads from GitHub releases:
  pip install sherpa-onnx soundfile
  https://github.com/k2-fsa/sherpa-onnx/releases/download/source-separation-models/UVR-MDX-NET-Voc_FT.onnx

The audio is processed in 6 s chunks with 0.5 s crossfades, so memory stays under about 2 GB.
The stem with more silent frames is taken to be the voice, and it is written as 48 kHz mono.

Check it afterwards. Old sound effects (whooshes, pops) can bleed into the voice stem.
Find them in the pauses between words (`--report` prints the pauses) and gate them out.
"""
import argparse, gc, os, subprocess, sys, tempfile
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input'); p.add_argument('--out', default='voice.wav')
    p.add_argument('--model', default=os.environ.get('MM_UVR_MODEL', 'UVR-MDX-NET-Voc_FT.onnx'))
    p.add_argument('--chunk', type=float, default=6.0)
    a = p.parse_args()
    try:
        import sherpa_onnx as so, soundfile as sf
    except ImportError:
        sys.exit('pip install sherpa-onnx soundfile')
    if not os.path.exists(a.model):
        sys.exit(f'model not found: {a.model}\n  download: https://github.com/k2-fsa/sherpa-onnx/releases/download/source-separation-models/UVR-MDX-NET-Voc_FT.onnx')
    tmp = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.input, '-vn', '-ac', '2', '-ar', '44100', tmp], check=True)
    x, sr = sf.read(tmp, dtype='float32', always_2d=True); os.remove(tmp)
    cfg = so.OfflineSourceSeparationConfig(model=so.OfflineSourceSeparationModelConfig(
        uvr=so.OfflineSourceSeparationUvrModelConfig(model=a.model), num_threads=os.cpu_count() or 2))
    sp = so.OfflineSourceSeparation(cfg)
    n, W, O = len(x), int(a.chunk * sr), int(0.5 * sr)
    acc, wsum = None, np.zeros(n)
    for s0 in range(0, n, W - O):
        s1 = min(n, s0 + W)
        res = sp.process(sample_rate=sr, samples=np.ascontiguousarray(x[s0:s1].T))
        stems = [np.asarray(s.data).T for s in res.stems]
        if acc is None: acc = [np.zeros((n, st.shape[1])) for st in stems]
        L = s1 - s0; w = np.ones(L)
        if s0 > 0: w[:O] = np.linspace(0, 1, O)
        if s1 < n: w[-O:] = np.linspace(1, 0, O)
        for i, st in enumerate(stems): acc[i][s0:s1] += st[:L] * w[:, None]
        wsum[s0:s1] += w; gc.collect()
        print(f'  {s0 / sr:5.1f}–{s1 / sr:5.1f}s', flush=True)
        if s1 == n: break
    stems = [st / np.maximum(wsum, 1e-6)[:, None] for st in acc]

    def quiet_ratio(st):
        m = st.mean(1); h = sr // 20
        r = np.sqrt((m[: len(m) // h * h].reshape(-1, h) ** 2).mean(1))
        return (20 * np.log10(r + 1e-9) < -45).mean()
    vi = int(np.argmax([quiet_ratio(st) for st in stems]))
    raw = tempfile.mktemp(suffix='.wav')
    sf.write(raw, stems[vi], sr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'highpass=f=70,loudnorm=I=-16:TP=-1.5', '-ac', '1', '-ar', '48000', a.out], check=True)
    os.remove(raw)
    print(f'voice stem #{vi} → {a.out}   (next: transcribe.py, then listen to the pauses for SFX bleed)')


if __name__ == '__main__':
    main()
