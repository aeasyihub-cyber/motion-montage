#!/usr/bin/env python3
"""motion-montage · qc_video.py — objective checks on a finished render. The critic's instruments.

  python3 qc_video.py final.mp4 [--timeline timeline.json] [--cues out/cues.json] [--dead 0.7] [--lufs -14]
                     [--sheet sheet.png]  [--json report.json]

Measures and judges:
  • format          resolution, fps, duration, codec
  • loudness        integrated LUFS, true peak                          (target −14 ±1 LUFS, TP ≤ −1)
  • DEAD AIR        any stretch where the picture is frozen > --dead s  (the #1 "amateur" tell)
  • black frames    unintended blacks
  • cut rhythm      detected cuts, average shot length, longest static shot
  • sync            each cue / scene cut vs nearest spoken word onset   (want ≤ 0.05 s)
  • contact sheet   one frame per second, for the human eye
Exit code 1 if any HARD FAIL.
"""
import argparse, json, re, subprocess, sys


def run(args):
    return subprocess.run(args, capture_output=True, text=True).stderr


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate:format=duration',
                          '-of', 'json', path], capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('video'); p.add_argument('--timeline'); p.add_argument('--cues')
    p.add_argument('--dead', type=float, default=0.7); p.add_argument('--lufs', type=float, default=-14)
    p.add_argument('--sheet'); p.add_argument('--json')
    a = p.parse_args()
    R, fails, warns = {}, [], []

    info = probe(a.video)
    v = next(s for s in info['streams'] if s['codec_type'] == 'video')
    num, den = map(int, v['r_frame_rate'].split('/'))
    R['format'] = dict(w=v['width'], h=v['height'], fps=round(num / den, 3), duration=round(float(info['format']['duration']), 3),
                       audio=any(s['codec_type'] == 'audio' for s in info['streams']))

    # loudness
    if R['format']['audio']:
        e = run(['ffmpeg', '-hide_banner', '-i', a.video, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
        I = re.findall(r'I:\s+(-?[\d.]+) LUFS', e); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', e)
        R['loudness'] = dict(lufs=float(I[-1]) if I else None, true_peak=float(TP[-1]) if TP else None)
        if I and abs(float(I[-1]) - a.lufs) > 1.0: fails.append(f'loudness {I[-1]} LUFS (target {a.lufs} ±1)')
        if TP and float(TP[-1]) > -0.9: fails.append(f'true peak {TP[-1]} dBFS (want ≤ −1)')
    else:
        warns.append('no audio stream')

    # dead air: frozen picture
    e = run(['ffmpeg', '-hide_banner', '-i', a.video, '-an', '-vf', f'freezedetect=n=0.0015:d={a.dead}', '-f', 'null', '-'])
    starts = [float(x) for x in re.findall(r'freeze_start: ([\d.]+)', e)]
    ends = [float(x) for x in re.findall(r'freeze_end: ([\d.]+)', e)]
    dead = [(s, ends[i] if i < len(ends) else R['format']['duration']) for i, s in enumerate(starts)]
    # the final hold (end card) is allowed up to 2.0 s
    dead_bad = [(s, t) for s, t in dead if not (t >= R['format']['duration'] - 0.05 and t - s <= 2.0)]
    R['dead_air'] = [dict(start=round(s, 2), end=round(t, 2), len=round(t - s, 2)) for s, t in dead]
    for s, t in dead_bad:
        fails.append(f'DEAD AIR {s:.2f}–{t:.2f}s ({t - s:.2f}s frozen) — add camera drift, a secondary action, or cut sooner')

    # black frames
    e = run(['ffmpeg', '-hide_banner', '-i', a.video, '-an', '-vf', 'blackdetect=d=0.1:pix_th=0.08', '-f', 'null', '-'])
    blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', e)
    R['black'] = [dict(start=float(s), end=float(t)) for s, t in blacks]
    for s, t in blacks:
        if float(s) > 0.05 and float(t) < R['format']['duration'] - 0.05:
            warns.append(f'black frames {s}–{t}s (intended dip?)')

    # cuts
    e = run(['ffmpeg', '-hide_banner', '-i', a.video, '-an', '-vf', "fps=12,select='gt(scene,0.22)',showinfo", '-f', 'null', '-'])
    raw = [round(float(x), 3) for x in re.findall(r'pts_time:([\d.]+)', e)]
    cuts = []                                   # merge detections inside one transition (< 0.35 s apart)
    for c in raw:
        if cuts and c - cuts[-1][-1] < 0.35: cuts[-1].append(c)
        else: cuts.append([c])
    cuts = [round(sum(g) / len(g), 3) for g in cuts]
    R['cuts'] = cuts
    seg = [b - a_ for a_, b in zip([0] + cuts, cuts + [R['format']['duration']])]
    R['rhythm'] = dict(n_cuts=len(cuts), avg_shot=round(sum(seg) / len(seg), 2), longest_shot=round(max(seg), 2))

    # sync vs voice
    if a.timeline:
        tl = json.load(open(a.timeline, encoding='utf-8'))
        onsets = [w['s'] for w in tl.get('words', [])]
        ends = [w['e'] for w in tl.get('words', [])]
        cues = []
        if a.cues:
            cj = json.load(open(a.cues)); cues = [c for c in (cj['cues'] if isinstance(cj, dict) else cj) if c['type'] in ('pop', 'swish', 'hit', 'whoosh')]
        # each accent type is judged against its own rule (see references/rhythm-editing.md):
        #   pop / hit → word ONSET ±50 ms · swish (strike) → word END ±150 ms
        #   whoosh (cut) → 0–150 ms BEFORE an onset (the cut-ahead rule) · cue with "free":true → skipped
        off, bad = [], []
        for c in cues:
            t = c['t']
            if c.get('free'): continue
            if c['type'] == 'whoosh':
                ahead = [o - t for o in onsets if -0.02 <= o - t <= 0.15]
                d = 0 if ahead else min(abs(t - o) for o in onsets)
                ok = bool(ahead) or d <= 0.05
            elif c['type'] == 'swish':
                d = min(min(abs(t - e) for e in ends), min(abs(t - o) for o in onsets)); ok = d <= 0.15
            else:
                d = min(abs(t - o) for o in onsets); ok = d <= 0.05
            off.append(d)
            if not ok: bad.append((round(t, 2), c['type'], round(d, 2)))
        R['sync'] = dict(events=len(off), in_rule=len(off) - len(bad), worst=round(max(off), 3) if off else 0, off_rule=bad)
        if bad: warns.append(f'{len(bad)} accent(s) outside their sync rule: {bad[:8]} — deliberate? mark the cue {{"free":true}}, else re-time')
        end_voice = tl.get('duration') or (onsets and tl['words'][-1]['e'])
        if end_voice and R['format']['duration'] - end_voice > 2.5:
            warns.append(f'video runs {R["format"]["duration"] - end_voice:.1f}s past the last word (CTA hold should be ~1.2–2 s)')

    if a.sheet:
        rows = max(1, -(-int(R['format']['duration'] + 0.999) // 8))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.video, '-vf', f'fps=1,scale=240:-1,tile=8x{rows}:padding=6:color=0x111111', '-frames:v', '1', a.sheet])
        R['sheet'] = a.sheet

    R['fails'], R['warnings'] = fails, warns
    print(json.dumps(R['format']), '\n', json.dumps(R.get('loudness', {})), '\n', json.dumps(R['rhythm']))
    if 'sync' in R: print(' sync', json.dumps(R['sync']))
    for w in warns: print('  ⚠', w)
    for f in fails: print('  ✗', f)
    print('  ✓ objective QC passed' if not fails else f'  {len(fails)} HARD FAIL(s)')
    if a.json: json.dump(R, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
