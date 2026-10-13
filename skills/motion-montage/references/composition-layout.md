# Composition and layout

## Safe zones (set `MM.SAFE` to match)

| Format | Frame | Keep text inside | Why |
|---|---|---|---|
| 9:16 Reels/TikTok/Shorts | 1080×1920 | x 60–1020, y 200–1700 | Top: status and username. Bottom 220 px: caption UI and buttons. Right 120 px at y>1100: like/comment rail. |
| 1:1 feed | 1080×1080 | 60–1020 both | Crop safety |
| 4:5 feed | 1080×1350 | x 60–1020, y 80–1270 | |
| 16:9 YouTube | 1920×1080 | x 96–1824, y 54–1026 (title-safe 5%) | Bottom-right: the end-screen element area in the last 20 s |

On 9:16, keep key words out of **x > 900 between y 1100–1700**, where the action rail sits.

## Fill the frame (the #1 fix)

- Hero text block = 75–92% of the safe width. A 9:16 frame is tall, so use **3–5 stacked lines** or one giant word, not one small line.
- **Vertical balance:** the visual centre of the content sits between y 760 and 1050 on 9:16. A headline stuck in the top third with an empty bottom half is an accident, not a choice.
- Negative space is deliberate when it *frames* the subject (big margin around one word). It's accidental when it's just left over.
- Fill the support zone too: a card, an image, a waveform, a counter, a label row. Every scene has a **primary** (type) and a **secondary** (proof or visual).

## Grids

- 9:16: a 4-column grid, 60 px margins, 24 px gutters. Align text left edges to column 1. Centre only for end cards and single-word slams.
- Keep a consistent left edge across scenes so cuts feel designed (the eye doesn't have to hunt).
- Use a baseline rhythm: line spacing in multiples of 8 px.

## Focal point

- One focal point per moment. Lead the eye: big → highlight → small.
- After a cut, put the new focal point where the old one was, or move it deliberately (match on position).
- Use contrast to direct attention: the focal element gets the accent colour, and the rest goes ink or muted.

## Colour

- A maximum of 3 colours plus neutrals per film. Accent ≤ 10% of the pixels.
- Alternating backgrounds (paper ↔ dark ↔ accent) create rhythm and make the colour change *be* the cut.
- Contrast: text ≥ 4.5:1 against its background (WCAG AA). Captions ≥ 7:1.

## Texture

- Use one fixed grain layer (`MM.grain`), 6–10% opacity: `multiply` on light, `overlay` on dark.
- Vignettes on dark scenes are subtle (≤ 45% at the corners).
- Images get a slow push-in (1.12 → 1.00 over 3–4 s). Under text, they get a 5 px blur and 12% darkening.

## Images and footage

- Only use assets the user owns or supplied. Never use generated logos, watermarked stock, or another brand's marks.
- Footage plays as an image sequence (`MM.footage`) so speed ramps are frame-accurate:
  `ffmpeg -i clip.mp4 -vf fps=60,scale=1080:-2 -q:v 3 footage/clip/%05d.jpg`
- Devices and cards around footage give it depth: radius 48–64, a soft shadow `0 60px 120px rgba(0,0,0,.5)`, and 3D tilt ±6–14°.
