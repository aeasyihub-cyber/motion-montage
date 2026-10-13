# Case study: what a first "code-made" kinetic video gets wrong

This skill was born from a real 38 s, 9:16, 60 fps kinetic-type ad built in code
(an editorial paper + purple glass style, a phone voice-over, an 11-scene structure). It was a good v1:
the loudness was right (−14.0 LUFS), highlights and strikes were word-synced, and the palette was coherent. Running this skill's
instruments and a frame-by-frame review on it found the gaps between "good for code" and "a pro cut it":

| Finding | Evidence | Rule it became |
|---|---|---|
| **Dead air** | `qc_video.py`: frozen picture 0.70–1.38 s, 13.30–14.00 s, 15.62–16.23 s, 16.57–17.42 s | H3; camera always alive; `freezedetect` in QC |
| **Empty transition frames** | Pure cream or purple frames around the colour changes (≈ 0:15, 0:23, 0:29) | H8; "mid-transition frames must not be empty"; incoming content lands ≤ 0.15 s after |
| **Small type, empty halves** | Headlines about 40% of the frame width, top-left; the lower half often empty | "Fill the frame" + `MM.text.fit()` |
| **Duplicate captions** | The caption box repeated the headline word for word | "Hide captions while the same words are big on screen" |
| **One transition type** | Every scene change was the same colour wipe | 12 transition types and "never twice in a row" |
| **No depth or blur** | Flat layers; whips and slides with no motion blur | `[data-depth]` parallax camera; `--shutter`; `mb` directional blur |
| **Words revealed one by one in a corner** | The hook built word by word at a small size | Big fitted lines; `onWords` reveal inside masks, at hero scale |

What carried over unchanged, because it worked:
- the voice pipeline (measure the spectrum, then a gentle denoise and a presence EQ);
- the cream ↔ purple alternation as the cut;
- yellow marker on the single key word, and coral strike + grey for negations;
- the music stopping for the voice moment, with a waveform reading the real amplitude;
- the deterministic `render(t)` + Playwright + ffmpeg build;
- the stills contact sheet before the full render.
