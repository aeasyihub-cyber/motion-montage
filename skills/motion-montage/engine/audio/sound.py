#!/usr/bin/env python3
"""motion-montage · sound.py — sound design in code (numpy only, no samples, no licences).

  python3 sound.py bed   --dur 38 --bpm 96 --out bed.wav [--mute 24.1:27.6] [--key A] [--style pulse|warm|tense]
  python3 sound.py sfx   --cues out/cues.json --out sfx.wav [--dur 38]
  python3 sound.py mix   --voice voice-clean.wav --bed bed.wav --sfx sfx.wav --out mix.wav
                         [--duck 0.6] [--bed-db -16] [--sfx-db -4] [--lufs -14] [--tp -1.5] [--fade 1.2]
  python3 sound.py mux   --video out/video-silent.mp4 --audio mix.wav --out final.mp4
  python3 sound.py audition --out sfx-demo.wav      # hear every SFX type once

Cue types (from MM.cue in the composition):
  whoosh  — scene transitions / pushes / whips (peak lands ON the cut)
  pop     — highlight blocks, stickers, word pops
  swish   — strike-throughs, underlines (marker on paper)
  click   — typing, UI taps (keep very quiet)
  tick    — counters, small UI details
  boom    — the emotional/low moment, title slams (use ≤ 2 per video)
  riser   — 0.8–2 s build INTO a payoff (ends exactly at t)
  shimmer — logo reveal, sparkle of the end card
  hit     — big impact for a hook word (kick + transient)
Each cue may carry {"gain": dB, "dur": s, "pitch": ×}.
"""
import argparse, json, math, subprocess, sys, wave, os, tempfile
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- io
def read_audio(path):
    """Any format → mono float32 @48k via ffmpeg."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def write_wav(path, x, stereo=True):
    x = np.clip(x, -1, 1)
    if stereo and x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2 if pcm.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def db(g):
    return 10 ** (g / 20)


# ---------------------------------------------------------------- dsp helpers
def onepole_lp(x, fc):
    """One-pole low-pass; fc may be an array (time-varying sweep)."""
    if np.isscalar(fc):
        try:
            from scipy.signal import lfilter
            a = math.exp(-2 * math.pi * fc / SR)
            return lfilter([1 - a], [1, -a], x)
        except ImportError:
            pass
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


def bandsweep(x, f_from, f_to):
    n = len(x)
    f = np.geomspace(f_from, f_to, n)
    lo = onepole_lp(x, f * 1.6)
    return lo - onepole_lp(lo, f * 0.6)


def env_ar(n, a, r, curve=3.0):
    """attack fraction a, release fraction r of n samples."""
    t = np.linspace(0, 1, n)
    e = np.ones(n)
    na = max(1, int(n * a))
    e[:na] = np.linspace(0, 1, na) ** 2
    nr = max(1, int(n * r))
    e[-nr:] = np.linspace(1, 0, nr) ** curve
    return e


def sine_sweep(f0, f1, dur, curve='exp'):
    n = int(dur * SR)
    f = np.geomspace(f0, f1, n) if curve == 'exp' else np.linspace(f0, f1, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------------------------------------------------------------- SFX library
def sfx_whoosh(dur=0.5, pitch=1.0):
    n = int(dur * SR)
    x = bandsweep(rng.standard_normal(n), 300 * pitch, 5200 * pitch)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2.2          # peak in the middle → align middle to the cut
    return x * e * 2.2, 0.5                                # (signal, anchor fraction)


def sfx_pop(dur=0.12, pitch=1.0):
    n = int(dur * SR)
    s = sine_sweep(900 * pitch, 220 * pitch, dur) * np.exp(-np.linspace(0, 9, n))
    click = np.zeros(n); click[:96] = rng.standard_normal(96) * np.linspace(1, 0, 96) * 0.4
    return (s * 0.9 + click), 0.0


def sfx_swish(dur=0.24, pitch=1.0):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = x - onepole_lp(x, 2500 * pitch)                    # high-pass: felt-tip on paper
    e = env_ar(n, 0.15, 0.6) * (0.6 + 0.4 * np.sin(np.linspace(0, 3 * np.pi, n)) ** 2)
    return x * e * 0.55, 0.0


def sfx_click(dur=0.025, pitch=1.0):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = x - onepole_lp(x, 3500 * pitch)
    return x * np.exp(-np.linspace(0, 14, n)) * 0.5, 0.0


def sfx_tick(dur=0.06, pitch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1850 * pitch * t) + 0.5 * np.sin(2 * np.pi * 3700 * pitch * t)) * np.exp(-t * 90)
    return s * 0.5, 0.0


def sfx_boom(dur=1.6, pitch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 * pitch + 50 * pitch * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    air = onepole_lp(rng.standard_normal(n), 700) * np.exp(-t * 6) * 0.8
    return (body * 1.0 + air) * 0.95, 0.0


def sfx_hit(dur=0.7, pitch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(50 * pitch + 160 * pitch * np.exp(-t * 30)) / SR) * np.exp(-t * 7)
    snap = rng.standard_normal(n)
    snap = (snap - onepole_lp(snap, 1800)) * np.exp(-t * 38) * 0.7
    return (kick + snap) * 0.9, 0.0


def sfx_riser(dur=1.4, pitch=1.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = bandsweep(rng.standard_normal(n), 200 * pitch, 7000 * pitch) * t ** 2.4 * 1.8
    tone = sine_sweep(180 * pitch, 900 * pitch, dur) * t ** 3 * 0.25
    e = np.ones(n); e[-int(0.02 * SR):] = np.linspace(1, 0, int(0.02 * SR))
    return (noise + tone) * e, 1.0                         # anchor = END of the riser


def sfx_shimmer(dur=1.4, pitch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for i, f in enumerate([1318.5, 1975.5, 2637.0, 3136.0]):
        d = int(i * 0.06 * SR)
        tt = t[: n - d]
        out[d:] += np.sin(2 * np.pi * f * pitch * tt) * np.exp(-tt * 3.2) * (0.5 - i * 0.08)
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 9 * t)
    return out * trem * 0.45, 0.0


SFX = dict(whoosh=sfx_whoosh, pop=sfx_pop, swish=sfx_swish, click=sfx_click, tick=sfx_tick,
           boom=sfx_boom, hit=sfx_hit, riser=sfx_riser, shimmer=sfx_shimmer)
# default level per type, relative (dB). Voice must always win.
SFX_DB = dict(whoosh=-10, pop=-12, swish=-15, click=-24, tick=-20, boom=-6, hit=-8, riser=-12, shimmer=-14)


def render_sfx(cues, dur):
    out = np.zeros(int(dur * SR) + SR)
    last = {}
    for c in cues:
        typ = c['type']
        if typ not in SFX:
            print(f'  ! unknown cue type {typ}', file=sys.stderr); continue
        # de-clutter: same type within 70 ms → skip (prevents machine-gun pops)
        if typ in last and c['t'] - last[typ] < 0.07:
            continue
        last[typ] = c['t']
        kw = {}
        if 'dur' in c: kw['dur'] = c['dur']
        if 'pitch' in c: kw['pitch'] = c['pitch']
        sig, anchor = SFX[typ](**kw)
        start = int(c['t'] * SR - anchor * len(sig))
        g = db(SFX_DB[typ] + c.get('gain', 0))
        a, b = max(0, start), min(len(out), start + len(sig))
        if b > a:
            out[a:b] += sig[a - start: b - start] * g
    return out[: int(dur * SR)]


# ---------------------------------------------------------------- music bed
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def midi_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def render_bed(dur, bpm=96, key='A', style='pulse', mutes=()):
    n = int(dur * SR)
    t = np.arange(n) / SR
    beat = 60 / bpm
    root = 57 + NOTE.get(key, 9) - 9                         # A3 by default
    # minor progression i – VI – III – VII, one chord per bar
    prog = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]]
    bar = beat * 4
    pad = np.zeros(n)
    bass = np.zeros(n)
    for ci in range(int(dur / bar) + 1):
        a, b = int(ci * bar * SR), min(n, int((ci + 1) * bar * SR))
        if a >= n: break
        tt = np.arange(b - a) / SR
        ch = prog[ci % 4]
        seg = np.zeros(b - a)
        for iv in ch:
            f = midi_hz(root + iv)
            for h, amp in [(1, 1), (2, 0.35), (3, 0.12)]:
                seg += np.sin(2 * np.pi * f * h * tt + h) * amp
        att = np.minimum(1, tt / 0.6)
        rel = np.minimum(1, (tt[-1] - tt) / 0.4 + 0.0)
        pad[a:b] += seg * att * np.clip(rel, 0, 1) * 0.06
        fb = midi_hz(root + ch[0] - 12)
        bass[a:b] += np.sin(2 * np.pi * fb * tt) * 0.16 * np.clip(rel, 0, 1)
    pad = onepole_lp(pad, 2200) if style != 'tense' else onepole_lp(pad, 1200)

    kick = np.zeros(n); hats = np.zeros(n); pump = np.ones(n)
    kn = int(0.35 * SR); kt = np.arange(kn) / SR
    k_sig = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-kt * 28)) / SR) * np.exp(-kt * 9)
    hn = int(0.05 * SR); h_sig = rng.standard_normal(hn); h_sig = (h_sig - onepole_lp(h_sig, 7000)) * np.exp(-np.arange(hn) / SR * 80)
    nb = int(dur / beat) + 1
    for i in range(nb):
        s = int(i * beat * SR)
        if s >= n: break
        if style in ('pulse', 'tense'):
            e = min(n, s + kn); kick[s:e] += k_sig[: e - s] * 0.55
            # sidechain pump on everything tonal
            pe = min(n, s + int(beat * SR)); pt = np.arange(pe - s) / SR
            pump[s:pe] = 1 - 0.45 * np.exp(-pt * 9)
        hs = int((i + 0.5) * beat * SR)
        if hs < n:
            e = min(n, hs + hn); hats[hs:e] += h_sig[: e - hs] * 0.07
    bed = (pad + bass) * pump + kick + hats
    # mutes (e.g. the emotional moment) with 0.25 s fades
    g = np.ones(n)
    for a, b in mutes:
        ia, ib = int(a * SR), int(b * SR)
        f = int(0.25 * SR)
        g[max(0, ia - f): ia] = np.minimum(g[max(0, ia - f): ia], np.linspace(1, 0, ia - max(0, ia - f)))
        g[ia:ib] = 0
        g[ib: ib + f] = np.minimum(g[ib: ib + f], np.linspace(0, 1, len(g[ib: ib + f])))
    bed *= g
    return bed / (np.max(np.abs(bed)) + 1e-9) * 0.8


# ---------------------------------------------------------------- mix
def envelope(x, att=0.03, rel=0.25):
    rect = np.abs(x)
    a, r = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    # downsample for speed, then upsample
    hop = 240
    m = rect[: len(rect) // hop * hop].reshape(-1, hop).max(axis=1)
    e = np.zeros_like(m); s = 0.0
    aa, rr = a ** hop, r ** hop
    for i, v in enumerate(m):
        s = aa * s + (1 - aa) * v if v > s else rr * s + (1 - rr) * v
        e[i] = s
    e = np.repeat(e, hop)
    return np.pad(e, (0, len(x) - len(e)), mode='edge')


def loudnorm(inp, out, lufs, tp, fade, dur):
    """Two-pass EBU R128 (accurate on short clips) + a true-peak safety limiter."""
    pre = f'afade=t=out:st={max(0, dur - fade):.3f}:d={fade},' if fade > 0 else ''
    meas = subprocess.run(['ffmpeg', '-hide_banner', '-i', inp, '-af', f'{pre}loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json',
                           '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex('{'): meas.rindex('}') + 1])
    lim = 10 ** ((tp - 0.3) / 20)
    af = (f'{pre}loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:'
          f'measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true,'
          f'aresample=192000,alimiter=limit={lim:.4f}:level=false:attack=1:release=50,aresample={SR}')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', inp, '-af', af, '-ar', str(SR), out], check=True)


def cmd_mix(a):
    voice = read_audio(a.voice) if a.voice else None
    bed = read_audio(a.bed) if a.bed else None
    sfx = read_audio(a.sfx) if a.sfx else None
    n = max(len(x) for x in (voice, bed, sfx) if x is not None)
    if a.dur: n = int(float(a.dur) * SR)
    fit = lambda x: np.zeros(n) if x is None else np.pad(x, (0, max(0, n - len(x))))[:n]
    voice, bed, sfx = fit(voice), fit(bed), fit(sfx)
    if voice.any():
        env = envelope(voice)
        env = env / (np.percentile(env[env > 1e-4], 95) + 1e-9) if (env > 1e-4).any() else env
        duck = 1 - a.duck * np.clip(env, 0, 1)
    else:
        duck = np.ones(n)
    mix = voice * db(0) + bed * db(a.bed_db) * duck + sfx * db(a.sfx_db)
    tmp = tempfile.mktemp(suffix='.wav')
    write_wav(tmp, mix / (np.max(np.abs(mix)) + 1e-9) * 0.7)
    loudnorm(tmp, a.out, a.lufs, a.tp, a.fade, n / SR)
    os.remove(tmp)
    print(f'mix → {a.out}  ({n / SR:.2f}s, target {a.lufs} LUFS)')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('bed'); b.add_argument('--dur', type=float, required=True); b.add_argument('--bpm', type=float, default=96)
    b.add_argument('--key', default='A'); b.add_argument('--style', default='pulse', choices=['pulse', 'warm', 'tense'])
    b.add_argument('--mute', action='append', default=[], help='a:b seconds of silence (repeatable)'); b.add_argument('--out', required=True)
    s = sp.add_parser('sfx'); s.add_argument('--cues', required=True); s.add_argument('--out', required=True); s.add_argument('--dur', type=float)
    m = sp.add_parser('mix')
    for k in ('voice', 'bed', 'sfx', 'dur'): m.add_argument('--' + k)
    m.add_argument('--out', required=True); m.add_argument('--duck', type=float, default=0.6)
    m.add_argument('--bed-db', type=float, default=-16); m.add_argument('--sfx-db', type=float, default=-4)
    m.add_argument('--lufs', type=float, default=-14); m.add_argument('--tp', type=float, default=-1.5); m.add_argument('--fade', type=float, default=1.2)
    x = sp.add_parser('mux'); x.add_argument('--video', required=True); x.add_argument('--audio', required=True); x.add_argument('--out', required=True)
    au = sp.add_parser('audition'); au.add_argument('--out', required=True)
    a = p.parse_args()

    if a.cmd == 'bed':
        mutes = [tuple(map(float, m.split(':'))) for m in a.mute]
        write_wav(a.out, render_bed(a.dur, a.bpm, a.key, a.style, mutes)); print(f'bed → {a.out}')
    elif a.cmd == 'sfx':
        data = json.load(open(a.cues))
        cues = data['cues'] if isinstance(data, dict) else data
        dur = a.dur or (data.get('duration') if isinstance(data, dict) else None) or (max(c['t'] for c in cues) + 2)
        write_wav(a.out, render_sfx(cues, dur)); print(f'sfx → {a.out}  ({len(cues)} cues)')
    elif a.cmd == 'mix':
        cmd_mix(a)
    elif a.cmd == 'mux':
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.video, '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', a.out], check=True)
        print(f'final → {a.out}')
    elif a.cmd == 'audition':
        cues = [{'t': 0.6 + i * 1.3, 'type': k} for i, k in enumerate(SFX)]
        write_wav(a.out, render_sfx(cues, 0.6 + len(SFX) * 1.3 + 1)); print(f'audition → {a.out}: ' + ', '.join(SFX))


if __name__ == '__main__':
    main()
