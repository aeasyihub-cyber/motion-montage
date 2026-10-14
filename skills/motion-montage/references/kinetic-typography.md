# Kinetic typography

Type is the actor. Its size, weight and timing perform the voice.

## Scale and hierarchy

- **Hero lines fill the frame.** Use `MM.text.fit(el, 840–940)` for 9:16. A one-word slam can go to 960.
- **Contrast is the design.** Pair a huge word (200–560 px) with a small support line (52–90 px), at a ratio of 3–8×. Two similar sizes look like a slide.
- **Two families at most:** a grotesk (Inter Tight, Geist, Satoshi) plus a serif with character (Fraunces, Instrument Serif, Playfair). Use italic serif for the *emotional* word, and heavy sans for the claim.
- **Tracking:** −0.03 to −0.05 em on big sans, 0 to −0.02 on serif display, +0.06 em uppercase on mono labels.
- **Leading:** 0.84–0.95 on stacked display lines. Masks need `padding-bottom:.12em` (handled by `split`).
- **Optical alignment:** huge type needs a +6–16 px nudge from the margin (side bearing). Italic needs a further +0.05 em.

## Reveal vocabulary (`MM.text.*`)

| Function | Use for | Feel |
|---|---|---|
| `rise(items,t,start,{each,dur,blur})` | default line/word reveal inside masks | editorial, clean |
| `onWords(items,t,times,'fade',{dim:.16})` | **ghost karaoke**: the whole line is visible faintly and lights up word by word | full frames, readable thumbnail |
| `onWords(items,t,times,'rise'/'pop'/'fade')` | **voice mode**: every word appears on its spoken onset | synced, alive |
| `pop` / `onWords(...,'pop')` | short punchy words, negations, numbers | energetic |
| `cascade(chars,t,start,{sp:spring.land})` | hero hooks, titles (Latin only) | premium, physical |
| `track(el,t,start)` | luxury titles, end cards | cinematic |
| `weight(el,t,keys)` | variable-font emphasis (300→900 on the beat) | modern, musical |
| `highlight(hl,t,start,{dir})` | the ONE key word | marker on paper |
| `strike(word,t,start)` | negations, "not this" | editorial wit |
| `swap(a,b,t,at)` | "not X → Y", replacing a word in place | clever, compact |
| `count(el,t,start,dur,a,b)` | stats, prices, numbers | proof |
| `type(el,full,t,start,cps,cursor)` | prompt boxes, code, documents only | diegetic |
| `exit(items,t,start)` | leaving before a cut | tidy |
| `captions(box,t,{hideWhen})` | subtitles from the timeline | accessible |

## Highlight rules

- **Only one** highlighted word on screen. It starts when the word is *said* (+0.03–0.06 s).
- The marker grows from the reading start (left for LTR, right for RTL), with `inOutQuart` over 0.3–0.35 s.
- After the highlight, the text colour may flip (ink to paper on a dark block) at p > 0.5.

## Captions

- A sentence block appears whole when the sentence starts, and the active word gets `.on`. Key words get a white box and a 1→1.12→1 pop.
- **Hide captions while the same words are big on screen.** Duplicates are the most common amateur tell.
- Position: 9:16 → y ≈ 1520–1600, never below 1700 (platform UI). The box is `rgba(12,12,14,.84)`, radius 20, 40–48 px.
- Captions match the voice word for word, with no added words. Don't put a trailing full stop on Latin words in RTL lines (bidi jumps).

## Arabic, Persian, Urdu (RTL)

- Split by **words only**. Never by characters, because joins break.
- `dir="rtl"` on blocks. Highlights and strikes grow from the right (`dir:'rtl'`).
- Fonts: Lalezar or Noto Kufi Arabic for headlines, and Rubik/IBM Plex Sans Arabic for body. Lalezar needs `word-spacing:14px`.
- Never put Arabic in a monospace or Latin-only font (you get tofu or broken shaping). Check every still.
- Mixed lines: wrap Latin runs in `<bdi>`.

## Never

Typewriter headlines, per-letter rainbow colours, WordArt outlines plus drop shadow, text on a busy image without a scrim
(use 5 px blur and −12% brightness on the image), centre-aligned paragraphs longer than 2 lines, and more than 7 words on screen in a hook.
