# Style presets

Each preset is a complete style lock: palette, type, texture, motion personality and signature move.
Swap the `:root` tokens in the template. All fonts are free (OFL) and on npm as `@fontsource/*`.

---

## 1. Editorial Paper + Purple Glass (AEasyI house style)
- **Palette:** cream `#F3EEE4`, ink `#15171B`, purple radial `#7A3FB0→#3A1658`, deep `#4A1F6E→#1E0A30`, marker `#F2C94C`, coral `#FF5A47`
- **Type:** Geist/Inter Tight 600–850; Fraunces 900 for numbers and italic stickers; Arabic: Lalezar plus Rubik Arabic
- **Texture:** fixed grain at 9% (multiply on cream, overlay on purple). White paper cards with radius 40, and glass cards (`rgba(255,255,255,.12)` + a 2 px border at .28).
- **Motion:** editorial-calm. Use `snap` rises, a yellow marker on the key word, coral strikes, and a −3° to −5° sticker tilt with an `outBack` overshoot of 1.4.
- **Signature:** the colour change *is* the cut (`panel` rising sheet, alternating cream and purple). The music stops for "my voice" with a real waveform.

## 2. Swiss Bold (the `showreel` template)
- **Palette:** paper `#F2EFE8`, ink `#0F0F12`, signal `#FF4A1C`
- **Type:** Inter Tight 900, fitted to the width, tracking −0.045 em; Fraunces italic 300–400 as the counterpoint; JetBrains Mono uppercase labels
- **Motion:** confident and graphic. Use char cascades on `spring.land`, `slats` and `sweep` transitions, counters, and a beat meter.
- **Signature:** a giant fitted word with the accent block, and mono metadata in the corners (timecode, index).

## 3. Dark Tech / Product
- **Palette:** `#07080B` base, `#12151C` surfaces, `#E8ECF2` text, electric accent `#4D7CFF` (or `#00E0A4`)
- **Type:** Geist/Inter 500–800, Geist Mono / JetBrains Mono for UI
- **Texture:** fine noise at 4%. Surfaces get a 1 px border `rgba(255,255,255,.08)` and a large soft radial light behind the hero (not a glow on the text).
- **Motion:** precise. Use `emphasized` easing, UI cards with `stack` transitions, cursor-driven reveals, `iris` from buttons, and counters.
- **Signature:** a product UI rebuilt in HTML (never screenshots stretched), with the camera dollying across it on depth layers.

## 4. Luxury Serif (real estate, fashion, hospitality)
- **Palette:** bone `#EFE9DF`, espresso `#1E1A16`, brass `#B08D57`; on footage, black scrims at 35%
- **Type:** Cormorant Garamond / Fraunces 300 display (wide tracking for caps, +0.2 em), Inter 400 small caps for labels
- **Motion:** slow and deliberate. Use `track` title reveals, `dissolve` and `dip` transitions, a 1.12→1.0 push-in on footage over 4–5 s, and no pops.
- **Signature:** a letter-spacing collapse on the title over a slow-motion speed ramp, with a brass hairline drawing under it.

## 5. Playful Pop (consumer, food, kids' brands)
- **Palette:** cream `#FFF6E5`, tomato `#FF5A3C`, grass `#2EBD6B`, sky `#3DA5FF`, ink `#1B1B1B`
- **Type:** Bricolage Grotesque / Recoleta, 700–900, sticker-like boxes
- **Motion:** bouncy within reason. Use `spring.pop` on stickers, `whip` transitions, 2–3° wobble on idle stickers (seeded `drift`), and `stack`.
- **Signature:** words as stickers slapped on with a `hit` sound, with rotation settling to −4…+4°.

## 6. Brutalist News / Documentary
- **Palette:** white `#FFFFFF`, black `#000000`, a single highlighter `#FFE600` or red `#E10600`
- **Type:** Archivo Black / Druk-like condensed (Anton) plus IBM Plex Mono
- **Motion:** hard cuts on beats, `wipe` with hard edges, `strike` and `swap` corrections, data counters, no easing longer than 0.3 s.
- **Signature:** full-bleed type blocks that hard-cut on every beat for 2 bars, then a long hold on the key fact.

---

## Building a brand preset from a logo
1. Sample 2–3 colours from the logo (dominant plus accent). Add a light and a dark neutral tuned toward the brand hue.
2. Match the type personality: geometric logo → geometric sans; serif logo → serif display plus a neutral sans.
3. Derive the motion personality from the brand voice: bold → snap + whip; calm → glide + dissolve; playful → springs.
4. Write it into `TREATMENT.md` as the style lock before any scene is built.
