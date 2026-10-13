# Rhythm and editing: what a montage editor actually does

## Retention structure for short-form (15–60 s)

| Window | Job | Tactics |
|---|---|---|
| 0.0–1.5 s **Hook** | Stop the scroll | Frame 0 is already designed. The biggest type of the film. A claim, a number or a contradiction. Motion starts within 3 frames. |
| 1.5–5 s **Promise** | Tell them why they should stay | Name the payoff. The first transition is energetic (whip or zoom). |
| Middle **Proof** | Deliver in beats | One idea per scene, 1.5–3.5 s each. A pattern interrupt every 2–4 s (a colour change, a scale jump, a new element type). |
| Before the payoff **Breath** | Contrast | 0.3–0.6 s of relative stillness, or music drop-out. |
| Payoff | The line they'll remember | The hero treatment: the biggest scale, a sticker or highlight, a boom or hit. |
| Last 2–3 s **CTA** | Act | One instruction, one highlighted word, the handle and logo. Hold 1.2–2 s after the last word. |

## Shot length

- The average shot is 1.5–3 s for social energy and 3–5 s for luxury or calm.
- **Vary the lengths.** Equal lengths feel mechanical. Speed up (shorter shots) into a climax, then a long shot for the payoff.
- In music mode, one scene = 2 or 4 bars at most. Accents can cut on every beat for 1–2 bars at a peak, then release.

## Dead air (instrumented by `qc_video.py`)

A frozen picture for more than 0.7 s is the most reliable "amateur" signal. Fix it, in order of preference:
1. Cut sooner (the scene is too long for its words).
2. Add camera life: a push-in, drift or parallax.
3. Add secondary action: a counter ticking, a waveform reading the voice, chips floating, a cursor blinking.
4. Stagger the reveal across the speech instead of revealing everything at once.

## Cut timing

- Voice mode: cut 0.05–0.12 s before the first word of the new line, or inside a pause longer than 0.35 s.
- Music mode: cut on the beat (snap `at` to the nearest beat in `beats.json`). Scene changes go on downbeats, and the hero goes on the drop.
- Never cut in the middle of a word, and never 1–3 frames off a beat (it reads as a mistake, not a choice).

## Speed ramps (footage)

The classic ramp is 1× → 0.2–0.35× on the hit (0.4–1 s) → 1.5–2.5× out, with eased transitions between speeds (`MM.ramp`).
Ramp into the impact moment (a jump peak, a pour, a product reveal), and land the beat on the slowest frame.

## Pattern library (proven micro-structures)

- **Claim → strike → correction:** "Not *random*… *on the beat*" (`strike` then `swap`).
- **Number reveal:** a 0→N counter with a tick per digit, then a scale pulse at the end and a pop.
- **List of three:** three lines, each with a different proof element (swatch, glyph, timecode). The third gets the accent.
- **Before/after:** split or wipe in the same layout, with only the content changing (a match cut).
- **The voice moment:** the music stops, the waveform reads the real voice, and the big word rises. Use it once per film.
