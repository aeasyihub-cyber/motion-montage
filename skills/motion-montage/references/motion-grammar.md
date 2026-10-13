# Motion grammar: how pros move things

Amateur motion is **linear, simultaneous and endless**. Pro motion is **eased, staggered and finished**.
Every rule below is something an After Effects motion designer does by reflex.

## 1. Easing: choose by intent

| Intent | Curve (`MM.ease.*`) | Duration @60fps | Notes |
|---|---|---|---|
| Something **arrives** | `snap` (0.16,1,0.3,1) / `outExpo` / `outQuart` | 0.35–0.55 s (21–33 f) | Fast start, long silky settle. The default. |
| Something **leaves** | `exit` (0.55,0,1,0.45) / `inCubic` | 0.20–0.35 s | Exits are ~30% shorter than enters. Don't let them linger. |
| Something **travels** on screen | `glide` (0.65,0,0.35,1) / `inOutCubic` | 0.6–3 s | Camera moves, cards repositioning. |
| A **transition** whips | `whip` (0.75,0,0.15,1) | 0.25–0.45 s | Slow, then FAST, then slow. Pair it with motion blur. |
| A **pop / sticker / stamp** | `spring.pop` (k320 d18) | about 0.4 s to settle | One overshoot of about 8–12%. Never a bouncing ball. |
| A **card lands** | `spring.land` (k200 d24) | about 0.5 s | Barely-there overshoot. |
| A **wind-up** | `anticipate` | 2–4 frames back, then go | Only on hero moves (the logo, the CTA word). |

**Never use `linear`** except for constant drifts (a film strip conveyor, a timecode, a slow parallax).

## 2. Stagger and overlap

- Stagger words 0.04–0.08 s, lines 0.10–0.20 s and characters 0.02–0.035 s.
- **Overlapping action:** the next element starts *before* the previous one finishes (offset 25–60% of its duration). Strict sequences feel robotic.
- **Follow-through:** secondary parts settle 3–8 frames after the primary (a shadow, an underline, a label).
- Stagger order carries meaning. `start` reads, `center` explodes or lands, `end` rewinds, `edges` frames.

## 3. Hierarchy of motion (one star per moment)

1. **Hero**: the word being said, or the key visual. It gets the biggest, most distinctive move.
2. **Support**: the other words in the line. They get a shared simple move (rise in a mask).
3. **Ambient**: the camera drift, parallax, grain and a breathing scale of 1 ± 0.004. Always on, never noticeable.

At most **3 elements start moving in the same 100 ms**. If more need to move, stagger them.

## 4. Camera, depth and life

- Put each scene on `[data-depth]` layers: background 0.3–0.6, subject 1, foreground 1.2–1.8. Move the camera with `MM.camera()`, and parallax comes for free.
- Every scene gets at least one camera behaviour: a **push-in** (1.00→1.04–1.08 over the scene, `glide`), a **drift** (`MM.handheld(seed,t,4–8px)`), or a **pan** (±15–60 px). Never a perfectly static frame. Static = "slideshow".
- Use 3D tilt sparingly: devices and cards get `persp:1600, ry ±6–14°`. Don't do flips or spins.

## 5. Motion blur: the single biggest "pro" tell

Real cameras smear fast motion. Code doesn't, unless you make it.
- `render.mjs --shutter 2` (or 4) gives true sub-frame blur for everything. Use it for every final render.
- For specific elements, use `set(el,{mb: MM.blurFrom(fx, fy, t)})` for velocity-based directional blur. Push and whip transitions already do this.
- Text that rises fast inside a mask can take a 4–8 px blur at the start of its move (`rise({blur:6})`).

## 6. Timing to the voice and the beat

- Visual events land **on** a word onset, with a tolerance of ±50 ms. Reveals start 30–60 ms *before* the onset (`onWords` does −0.04 s), so the word is readable as it's heard.
- Scene cuts land 50–120 ms **before** the first word of the new line.
- In music mode, cuts go on beats, scene changes on downbeats and the hero moment on the drop. Use off-beat accents for small pops.
- **Hold before the payoff:** 0.3–0.6 s of relative stillness (only ambient motion) before the key line. Contrast makes it hit.

## 7. Durations cheat sheet (60 fps)

| Thing | Frames | Seconds |
|---|---|---|
| Word reveal | 20–28 | 0.33–0.47 |
| Line stagger | 6–12 | 0.10–0.20 |
| Highlight block wipe | 18–21 | 0.30–0.35 |
| Strike-through | 15–18 | 0.25–0.30 |
| Sticker pop settle | about 24 | about 0.4 |
| Push/whip transition | 18–27 | 0.30–0.45 |
| Panel/slats/sweep transition | 33–42 | 0.55–0.70 |
| Number counter | 45–60 | 0.75–1.0 |
| Title track-in | 60–70 | 1.0–1.2 |
| End-card hold after the last word | 72–120 | 1.2–2.0 |

## 8. Forbidden motion

Bounce-bounce-bounce springs, rotation for its own sake, everything fading in at once, linear slides,
a "typewriter" on headlines, zooms that never end, shake, flicker, strobe, and random jitter (use seeded `drift` only).
