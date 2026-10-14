#!/usr/bin/env python3
"""motion-montage · transcribe.py: voice → word-level timestamps (the clock for the whole edit).

  python3 transcribe.py voice-clean.wav --lang en --out words.json [--model medium]
  python3 transcribe.py voice-clean.wav --parakeet path/to/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8

Backends, tried in this order:
  1. sherpa-onnx Parakeet TDT (with --parakeet DIR). English, very accurate, CPU-only.
     The model downloads from GitHub releases, so it works where Hugging Face is blocked:
       pip install sherpa-onnx soundfile
       https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
  2. faster-whisper: pip install faster-whisper. True word timestamps, many languages.
  3. openai-whisper: pip install openai-whisper (with word_timestamps=True).

Output: {"words":[{"w":"This","s":0.21,"e":0.42}, ...], "text": "...", "backend": "..."}

For Arabic and other RTL languages, pass --lang ar to whisper. Whisper may normalise dialect
spelling, and align.py maps the words back onto YOUR script so the captions show your exact words.
"""
import argparse, json, re, subprocess, sys, tempfile, os


def parakeet(path, lang, model_dir):
    import sherpa_onnx as so, soundfile as sf
    d = model_dir
    r = so.OfflineRecognizer.from_transducer(encoder=f'{d}/encoder.int8.onnx', decoder=f'{d}/decoder.int8.onnx',
                                             joiner=f'{d}/joiner.int8.onnx', tokens=f'{d}/tokens.txt',
                                             model_type='nemo_transducer', num_threads=os.cpu_count() or 2)
    tmp = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', '16000', tmp], check=True)
    x, sr = sf.read(tmp, dtype='float32'); os.remove(tmp)
    st = r.create_stream(); st.accept_waveform(sr, x); r.decode_stream(st)
    toks, ts = st.result.tokens, st.result.timestamps
    words = []
    for i, (t, s) in enumerate(zip(toks, ts)):
        if t.startswith(('▁', ' ')) or not words:
            words.append(dict(w=t.lstrip('▁ '), s=round(s, 3)))
        else:
            words[-1]['w'] += t
    # token timestamps give onsets; estimate each end from the word length, capped by the next onset
    for i, w in enumerate(words):
        nxt = words[i + 1]['s'] if i + 1 < len(words) else w['s'] + 1.0
        n = len(re.sub(r'\W', '', w['w']))
        w['e'] = round(min(nxt - 0.02, w['s'] + 0.12 + 0.075 * n), 3)
    return words


def faster(path, lang, model):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='auto', compute_type='int8')
    segs, _ = m.transcribe(path, language=lang, word_timestamps=True, vad_filter=True, beam_size=5)
    return [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for s in segs for w in (s.words or [])]


def openai(path, lang, model):
    import whisper
    m = whisper.load_model(model)
    r = m.transcribe(path, language=lang, word_timestamps=True)
    return [dict(w=w['word'].strip(), s=round(w['start'], 3), e=round(w['end'], 3))
            for seg in r['segments'] for w in seg.get('words', [])]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio'); p.add_argument('--lang', default=None); p.add_argument('--model', default='medium')
    p.add_argument('--parakeet', help='sherpa-onnx Parakeet model folder (English)')
    p.add_argument('--out', default='words.json')
    a = p.parse_args()
    chain = []
    if a.parakeet: chain.append(('sherpa-onnx parakeet', lambda: parakeet(a.audio, a.lang, a.parakeet)))
    chain += [('faster-whisper', lambda: faster(a.audio, a.lang, a.model)), ('openai-whisper', lambda: openai(a.audio, a.lang, a.model))]
    for name, fn in chain:
        try:
            words = fn()
        except ImportError:
            continue
        json.dump(dict(words=words, text=' '.join(w['w'] for w in words), backend=name), open(a.out, 'w'), ensure_ascii=False, indent=1)
        print(f'{len(words)} words via {name} → {a.out}')
        return
    sys.exit('No ASR backend found. Install one:  pip install faster-whisper   (or sherpa-onnx + --parakeet)')


if __name__ == '__main__':
    main()
