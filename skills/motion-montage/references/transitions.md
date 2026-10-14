# Transitions: choose by meaning, not by novelty

A transition is a sentence connector. "And" is a cut. "Meanwhile" is a dissolve. "BUT" is a whip.
`MM.edit(t, S, CUTS)` drives them. Each cut entry looks like `{type, dur, at?, ...opts}`.

| Type | Means | Duration | Options | Sound |
|---|---|---|---|---|
| `cut` | "and", fast rhythm, match cut | 0 | — | an optional tick or hit on beat |
| `panel` | new chapter or colour change (rising sheet) | 0.55–0.7 | `radius` | soft whoosh |
| `wipe` | continuation, list, next point | 0.4–0.6 | `dir` up/down/left/right | swish |
| `push` | "next", sequence, swipe-like | 0.35–0.5 | `dir`, `blur` | whoosh |
| `whip` | contrast, surprise, "but", energy | 0.25–0.35 | `dir`, `zoom` | fast whoosh (pitch 1.3–1.6) |
| `zoom` | diving deeper, "inside this…", focus | 0.45–0.6 | `to`, `from`, `origin` | low whoosh (pitch 0.7) |
| `iris` | reveal from a specific point (a dot, a button) | 0.5–0.7 | `x`, `y` (%) | pop at the start |
| `slats` | graphic / editorial / data | 0.5–0.7 | `n` (5–9), `dir` | whoosh |
| `sweep` | bold brand moment, covering a big change | 0.6–0.8 | `colors:[…]` (1–3), `dir`, `skew` | whoosh. ⚠ its middle frame is pure panel, so content must ride the panel edge or the critic fails it (H8). Prefer `wipe` unless you design that. |
| `stack` | "here's another", cards, app-like | 0.6–0.75 | `radius` | whoosh |
| `dissolve` | time passing, calm, luxury | 0.6–1.2 | `blur` | none, or the music carries it |
| `dip` | full stop, before the logo/end card | 0.6–1.0 | `color` | silence, then a hit |

## Rules

1. **Never use the same transition twice in a row.** A 30–40 s piece uses 3–5 types. One signature type may recur (at most 40% of cuts).
2. **Match energy.** Transition speed follows the music or voice energy. Calm sections get panel, dissolve or wipe. Peaks get whip, zoom or sweep.
3. **Direction is grammar.** Forward in the story = left or up. Back or remembering = right or down. Keep it consistent.
4. **Cut on the word.** `at` = the next line's first word onset − 0.05…0.12 s. In music mode, `at` = a beat time.
5. **Outgoing content leaves first.** Text in scene A starts exiting (`T.exit`) 0.2–0.3 s before the cut, so the transition carries the background, not half-read words.
6. **Mid-transition frames must not be empty.** If both scenes share a background colour, use `push`, `zoom` or `whip` (motion is visible), not `wipe` or `panel` (invisible).
7. **The incoming scene's first element lands within 0.15 s after the transition ends.** Otherwise it reads as dead air.
8. **Motion blur on anything that travels more than 30% of the frame in under 0.5 s** (push and whip do this automatically, and `--shutter 2` makes it real).

## Match cuts (the editor's flex)

There's no engine type for these. They're designed. Two scenes share a shape, colour or position across the cut:
- A circle in A becomes the iris mask of B (`iris` with `x,y` at the circle).
- The highlighted word's yellow block grows to fill the frame and *is* B's background (scale the block 1→40× during the last 0.3 s of A, then hard `cut`).
- The same word occupies the same position in A and B, and only the style changes (a font or colour swap on the cut).

## Sound bridges

- **J-cut:** B's sound (a whoosh tail, a music hit) starts 2–6 frames *before* the picture cut.
- **L-cut:** A's sound tail continues under B.

Put the `whoosh` cue at the cut centre (`at`). Its peak is centred, so it naturally starts early.
