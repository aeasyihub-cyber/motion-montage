#!/usr/bin/env python3
"""Forced alignment without an ASR model (aeneas-style).

Synthesises the known script with eSpeak NG (word marks give word times in the
synthetic audio), then DTW-aligns MFCCs of the synthetic audio against the real
voice and maps each word onto the real clock.

  python3 esalign.py --audio voice.wav --script script.txt --lang ar --out words.json

Output matches transcribe.py: {"words":[{"w","s","e"}], "text", "backend"}.
"""
import argparse, ctypes, json, re
import numpy as np
import librosa
import espeakng_loader

EV_WORD, EV_MARK = 1, 3


class EVENT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("unique_identifier", ctypes.c_uint),
                ("text_position", ctypes.c_int), ("length", ctypes.c_int),
                ("audio_position", ctypes.c_int), ("sample", ctypes.c_int),
                ("user_data", ctypes.c_void_p), ("id", ctypes.c_char_p)]


def script_words(path):
    words = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        raw = re.sub(r"^#\w+\s+", "", raw)
        words += [t.replace("*", "") for t in raw.split()]
    return words


def synth(words, lang):
    lib = ctypes.CDLL(espeakng_loader.get_library_path())
    data = espeakng_loader.get_data_path()
    sr = 0
    for p in (data, str(__import__("pathlib").Path(data).parent)):
        sr = lib.espeak_Initialize(2, 0, p.encode(), 0)
        if sr > 0 and lib.espeak_SetVoiceByName(lang.encode()) == 0:
            break
    if sr <= 0:
        raise SystemExit("espeak init failed")
    pcm, marks = [], {}
    CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.POINTER(EVENT))

    def cb(wav, n, ev):
        if wav and n > 0:
            pcm.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
        i = 0
        while ev[i].type != 0:
            e = ev[i]
            if e.type == EV_MARK and e.id:
                marks[int(e.id.decode())] = e.audio_position / 1000.0
            i += 1
        return 0

    cbf = CB(cb)
    lib.espeak_SetSynthCallback(cbf)
    lib.espeak_SetParameter(1, 150, 0)  # rate (wpm)
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ssml = "<speak>" + " ".join(f'<mark name="{i}"/>{esc(w)}' for i, w in enumerate(words)) + f'<mark name="{len(words)}"/></speak>'
    buf = ssml.encode("utf-8")
    lib.espeak_Synth(buf, len(buf) + 1, 0, 0, 0, 0x01 | 0x10, None, None)  # UTF8 | SSML
    lib.espeak_Synchronize()
    y = np.concatenate(pcm).astype(np.float32) / 32768.0
    return y, sr, marks


def feats(y, sr, hop):
    m = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=int(sr * hop), n_fft=int(sr * hop * 2))[1:]
    m = (m - m.mean(1, keepdims=True)) / (m.std(1, keepdims=True) + 1e-6)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True); ap.add_argument("--script", required=True)
    ap.add_argument("--lang", default="ar"); ap.add_argument("--out", default="words.json")
    ap.add_argument("--hop", type=float, default=0.02)
    a = ap.parse_args()
    words = script_words(a.script)
    ys, srs, marks = synth(words, a.lang)
    sr = 16000
    ys = librosa.resample(ys, orig_sr=srs, target_sr=sr)
    yr, _ = librosa.load(a.audio, sr=sr, mono=True)
    hop = a.hop
    A, B = feats(ys, sr, hop), feats(yr, sr, hop)
    _, wp = librosa.sequence.dtw(X=A, Y=B, metric="cosine", backtrack=True)
    wp = wp[::-1]
    # synth frame -> median real frame
    m = {}
    for i, j in wp:
        m.setdefault(i, []).append(j)
    nA = A.shape[1]
    lut = np.array([np.median(m.get(i, [m[max(k for k in m if k <= i)][-1]])) for i in range(nA)]) * hop
    tmap = lambda t: float(lut[min(int(round(t / hop)), nA - 1)])
    # real energy for snapping
    rms = librosa.feature.rms(y=yr, frame_length=int(sr * 0.02), hop_length=int(sr * 0.01))[0]
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > (np.percentile(db, 50) - 14)
    def snap_start(t):
        k = int(t / 0.01)
        for d in range(0, 25):
            if k + d < len(voiced) and voiced[k + d]:
                return (k + d) * 0.01
        return t
    def snap_end(t, s):
        k = int(t / 0.01)
        for d in range(0, 30):
            if k - d > int(s / 0.01) and voiced[k - d]:
                return (k - d + 1) * 0.01
        return t
    out = []
    for i, w in enumerate(words):
        s0 = tmap(marks.get(i, 0.0))
        e0 = tmap(marks.get(i + 1, marks.get(i, 0.0) + 0.3))
        s = snap_start(s0)
        e = max(s + 0.08, snap_end(e0, s))
        out.append(dict(w=w, s=round(s, 3), e=round(e, 3)))
    for k in range(1, len(out)):  # keep monotonic
        if out[k]["s"] < out[k - 1]["s"] + 0.05:
            out[k]["s"] = round(out[k - 1]["s"] + 0.05, 3)
        out[k - 1]["e"] = round(min(out[k - 1]["e"], out[k]["s"]), 3)
    json.dump(dict(words=out, text=" ".join(words), backend="espeak-dtw"), open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(out)} words, synth {len(ys)/sr:.1f}s, real {len(yr)/sr:.1f}s, last word ends {out[-1]['e']}")


if __name__ == "__main__":
    main()
