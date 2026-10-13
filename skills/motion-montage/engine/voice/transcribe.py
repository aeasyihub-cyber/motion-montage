#!/usr/bin/env python3
"""motion-montage · transcribe.py — voice → word-level timestamps (the clock of the whole edit).

  python3 transcribe.py voice-clean.wav --lang en --out words.json [--model medium]

Backends, tried in order:
  1. faster-whisper   pip install faster-whisper        (best: true word timestamps)
  2. openai-whisper   pip install openai-whisper         (word_timestamps=True)
Output: {"words":[{"w":"This","s":0.21,"e":0.42}, ...], "text": "...", "backend": "..."}

Arabic / RTL tip: pass --lang ar. Whisper may normalise dialect spelling — align.py
maps it back onto YOUR script so captions show your exact words.
"""
import argparse, json, sys


def faster(path, lang, model):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='auto', compute_type='int8')
    segs, _ = m.transcribe(path, language=lang, word_timestamps=True, vad_filter=True, beam_size=5)
    words = []
    for s in segs:
        for w in s.words or []:
            words.append(dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)))
    return words


def openai(path, lang, model):
    import whisper
    m = whisper.load_model(model)
    r = m.transcribe(path, language=lang, word_timestamps=True)
    return [dict(w=w['word'].strip(), s=round(w['start'], 3), e=round(w['end'], 3))
            for seg in r['segments'] for w in seg.get('words', [])]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio'); p.add_argument('--lang', default=None); p.add_argument('--model', default='medium')
    p.add_argument('--out', default='words.json')
    a = p.parse_args()
    for name, fn in (('faster-whisper', faster), ('openai-whisper', openai)):
        try:
            words = fn(a.audio, a.lang, a.model)
            json.dump(dict(words=words, text=' '.join(w['w'] for w in words), backend=name), open(a.out, 'w'), ensure_ascii=False, indent=1)
            print(f'{len(words)} words via {name} → {a.out}')
            return
        except ImportError:
            continue
    sys.exit('No whisper backend found. Install one:  pip install faster-whisper   (or: pip install openai-whisper)')


if __name__ == '__main__':
    main()
