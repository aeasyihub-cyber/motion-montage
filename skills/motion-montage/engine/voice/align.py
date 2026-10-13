#!/usr/bin/env python3
"""motion-montage · align.py — put YOUR script's words on the voice's clock.

  python3 align.py --words words.json --script script.txt --out timeline.json

script.txt: one line per sentence/beat, exactly as written. Optional markers:
  #hook  This video never touched an editing app.     ← names the line start as marker "hook"
  Words in *stars* are recorded as emphasis (key words for highlights).

Output timeline.json (consumed by MM.loadTimeline):
  { "words":[{"w","s","e","line","emph"}], "lines":[{"text","s","e","key"}],
    "markers":{"hook":0.21,...}, "diffs":[...], "duration": voice_end }
Any difference between what was said and what was written is listed in "diffs" —
REPORT IT to the user. Captions must follow what was actually SAID.
"""
import argparse, json, re, difflib

norm = lambda s: re.sub(r'[^\w]+', '', s.lower(), flags=re.UNICODE)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--words', required=True); p.add_argument('--script', required=True); p.add_argument('--out', default='timeline.json')
    a = p.parse_args()
    heard = json.load(open(a.words, encoding='utf-8'))['words']
    lines, script_words = [], []
    for li, raw in enumerate(l for l in open(a.script, encoding='utf-8').read().splitlines() if l.strip()):
        m = re.match(r'^#(\w+)\s+(.*)$', raw.strip())
        key, text = (m.group(1), m.group(2)) if m else (None, raw.strip())
        lines.append(dict(text=text.replace('*', ''), key=key))
        for tok in text.split():
            script_words.append(dict(w=tok.replace('*', ''), line=li, emph=tok.startswith('*')))

    A = [norm(w['w']) for w in script_words]
    B = [norm(w['w']) for w in heard]
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
    out, diffs = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                sw, hw = script_words[i1 + k], heard[j1 + k]
                out.append(dict(w=sw['w'], s=hw['s'], e=hw['e'], line=sw['line'], emph=sw['emph']))
        else:
            said = ' '.join(h['w'] for h in heard[j1:j2]); wrote = ' '.join(s['w'] for s in script_words[i1:i2])
            diffs.append(dict(op=op, wrote=wrote, said=said, at=heard[j1]['s'] if j1 < len(heard) else None))
            # captions follow the voice: keep heard words, attach to nearest script line
            line = script_words[min(i1, len(script_words) - 1)]['line'] if script_words else 0
            for h in heard[j1:j2]:
                out.append(dict(w=h['w'], s=h['s'], e=h['e'], line=line, emph=False))
    out.sort(key=lambda w: w['s'])
    markers = {}
    for li, L in enumerate(lines):
        ws = [w for w in out if w['line'] == li]
        L['s'] = ws[0]['s'] if ws else None
        L['e'] = ws[-1]['e'] if ws else None
        L['said'] = ' '.join(w['w'] for w in ws)
        if L['key'] and L['s'] is not None: markers[L['key']] = L['s']
    tl = dict(words=out, lines=lines, markers=markers, diffs=diffs, duration=round(out[-1]['e'], 3) if out else 0)
    json.dump(tl, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # also as a script the composition can load over file:// (no fetch needed)
    js = a.out[:-5] + '.js' if a.out.endswith('.json') else a.out + '.js'
    open(js, 'w', encoding='utf-8').write('window.TIMELINE = ' + json.dumps(tl, ensure_ascii=False) + ';\n')
    print(f'{len(out)} words, {len(lines)} lines → {a.out}')
    if diffs:
        print(f'⚠ {len(diffs)} difference(s) between script and voice (captions follow the voice):')
        for d in diffs: print(f"   {d['op']:8} wrote “{d['wrote']}”  said “{d['said']}”  @ {d['at']}")
    gaps = [(out[i]['e'], out[i + 1]['s']) for i in range(len(out) - 1) if out[i + 1]['s'] - out[i]['e'] > 0.6]
    if gaps:
        print('ℹ pauses > 0.6 s (natural scene-cut points): ' + ', '.join(f'{a:.2f}–{b:.2f}' for a, b in gaps))


if __name__ == '__main__':
    main()
