# Sound design

Half of "pro" is audio. Picture motion without sound feels weightless. Sound without restraint feels cheap.

## Layers (quietest to loudest)

1. **Bed:** the music. Use the user's licensed track, or `sound.py bed` (synthesised: pad + bass + kick + hats with a sidechain pump; styles `pulse | warm | tense`).
2. **SFX:** short accents on visual events, declared with `MM.cue()` in the composition so they're always in sync.
3. **Voice:** always on top and always intelligible.

## SFX map (`sound.py` types → visual events)

| Cue | Visual event | Default level | Anchor |
|---|---|---|---|
| `whoosh` | any travelling transition | −10 dB | peak at the cut centre |
| `pop` | highlight block, sticker, word pop | −12 dB | start |
| `swish` | strike-through, underline | −15 dB | start |
| `click` | typing (each 2–3 chars, not every char) | −24 dB | start |
| `tick` | counters, UI details | −20 dB | start |
| `hit` | hook slam, hero word | −8 dB | start |
| `boom` | the emotional low moment (≤ 2 per film) | −6 dB | start |
| `riser` | 0.8–2 s build INTO a payoff | −12 dB | **end** = payoff time |
| `shimmer` | logo or end-card reveal | −14 dB | start |

Adjust with `{gain, pitch, dur}`. Pitch > 1 = lighter and faster (whips), < 1 = heavier (zooms, big panels).
Restraint: no more than about 1 accent per second on average. The mixer drops repeats of the same type within 70 ms.

## Mix

- **Ducking:** the bed drops about 60% (`--duck 0.6`) under the voice envelope (30 ms attack, 250 ms release).
- **Silence is a tool.** Mute the bed (`--mute a:b`) for the voice moment or before the drop, with 0.25 s fades.
- **Loudness:** −14 LUFS integrated and ≤ −1 dBTP for social (Instagram/TikTok/YouTube normalise to about −14). Broadcast is −23 LUFS (EBU R128) or −24 LKFS (ATSC). `sound.py mix` runs a two-pass loudnorm plus a true-peak limiter.
- **Fade:** 1.0–1.2 s at the end, or end on a hit with a tail.
- Deliver a **no-music version** as well when the platform's trending audio may be used.

## Music-driven edits

`beats.py track.mp3` → `{bpm, beats, downbeats, onsets, drops}`. Put the cut times on beats, scene starts on downbeats,
the hero moment on `drops[0]`, and the pops on `onsets`. The bed's BPM drives `BEAT` in the showreel template.
