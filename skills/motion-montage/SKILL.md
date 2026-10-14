---
name: motion-montage
description: Make edited motion-graphics videos in code that look like a professional motion designer and editor cut them in After Effects. Covers kinetic typography synced to a voice word by word, beat-cut promos, footage montages with speed ramps, transitions, camera moves with parallax, motion blur, sound design and loudness-matched mixes, with a team of director, timing, storyboard, motion, edit, sound and critic agents. Use when the user wants a reel, short, ad, promo, explainer, lyric or kinetic-type video, montage or motion graphics, or wants to improve an existing one.
---

# Motion Montage

You are running a small post-production studio. The output must be indistinguishable from a
senior motion designer's work. It must never read as "AI", a template or a slideshow.

Everything is rendered in code, deterministically: an HTML composition with a pure `render(t)`,
captured frame by frame with Playwright, encoded with ffmpeg. Sound is synthesised in code.
There are no licences, no stock and no timeline app.

```
voice / music / footage ──► TIMING ──► STORYBOARD ──► BUILD ──► STILLS GATE ──► RENDER ──► SOUND ──► CRITIC ──► deliver
                              ▲            ▲             ▲           │                                   │
                              └────────────┴─────────────┴───────────┴────── fix list (loop) ◄────────────┘
```

## The studio (agents)

These live in the plugin's `agents/` folder. When subagents aren't available, play each role yourself, in order, and keep its gate.

| Agent | Owns | Never does |
|---|---|---|
| `montage-director` | Brief, treatment, style lock, approvals, final call | Writes scene code |
| `montage-timing` | Voice clean-up, transcription, alignment, beat grid, cut points | Picks visuals |
| `montage-storyboard` | Beat sheet → scene board: layout, focal point, type scale, motion idea per beat | Writes code |
| `montage-motion` | `composition.html`: scenes, type animation, camera, secondary motion, cues | Changes timing or script |
| `montage-editor` | The `CUTS` list: transition per cut, cut timing, pacing, flow across cuts | Animates inside a scene |
| `montage-sound` | Music bed, SFX cues, ducking, mix, loudness | Touches picture |
| `montage-critic` | Independent QC: instruments plus eyes, scored rubric, fix list | Fixes things itself, or grades its own work |

The critic must not have built the video. When subagents exist, always spawn `montage-critic` fresh.

## Phase 0: Intake (one round of questions, at most)

Collect the following, or infer it from the files attached:
1. **Mode:** `voice` (a voice-over drives the edit), `music` (a track or beat drives it) or `footage` (clips plus music, with optional VO).
2. **Format:** 9:16 1080×1920 (default) · 1:1 1080×1080 · 16:9 1920×1080 · 4:5 1080×1350. **Fps:** 60 for social and UI, 30 for broadcast, 24 for a film look (then motion blur is mandatory).
3. **Script:** the exact words, one line per beat. Mark key words with `*stars*` and scene starts with `#markers`.
4. **Brand:** logo file, colours, fonts and handle. If there are none, pick a preset from `references/style-presets.md`.
5. **Assets:** voice file, music, footage clips, images. Only use what the user owns or supplied.
6. **Call to action** and the platform.

If the script is missing, ask. **Never invent the words a person will say.**

## Phase 1: Timing (`montage-timing`)

The clock of the edit is the voice, or the beat. Nothing is timed by hand-typed seconds.

`$E` is this skill's `engine/` folder (in a plugin install: `${CLAUDE_PLUGIN_ROOT}/skills/motion-montage/engine`).
First-time setup: `cd $E && npm install && npx playwright install chromium`, plus `pip install numpy faster-whisper`. ffmpeg must be on PATH.

```bash
bash   $E/voice/clean_voice.sh raw.m4a voice-clean.wav [rnnoise.rnnn]
python3 $E/voice/separate.py old-video.mp4 --out voice.wav --model UVR-MDX-NET-Voc_FT.onnx   # remake mode: no raw voice? pull it out of the old video
python3 $E/voice/transcribe.py voice-clean.wav --lang en --out words.json
python3 $E/voice/align.py --words words.json --script script.txt --out project/timeline.json   # also writes timeline.js
python3 $E/voice/envelope.py voice-clean.wav --out project/voice-env.js                       # for waveforms / audio-reactive motion
python3 $E/audio/beats.py music.mp3 --out beats.json                                          # music mode
```

- Report every difference `align.py` finds between what was written and what was said. **Captions follow what was said.**
- Pauses longer than 0.6 s are natural cut points. A downbeat is a natural scene change.
- See `references/voice-pipeline.md`. Never apply heavy noise reduction (it sounds underwater).
- **Remake mode** (the user gives an existing video to improve): separate the voice, transcribe it (`--parakeet` works offline for English), and look in the pauses for sound effects from the old mix bleeding into the voice stem. Gate them out before mixing. Lift the user's own assets (logo, images) from the old frames only if no originals are supplied, and ask for the originals in the delivery note.

## Phase 2: Treatment and style lock (`montage-director`)

Write `project/TREATMENT.md`. Keep it to a page:
- **Logline** and the **one feeling** the viewer should leave with.
- **Style lock:** palette (at most 3 colours plus neutrals), 2 type families, grain/texture, the motion personality (for example "snappy editorial", "luxury slow", "tech precise") and the signature move. Pick from `references/style-presets.md` or derive from the brand.
- **Rules:** what is forbidden for this film, taken from the negative list below and the brand.

## Phase 3: Storyboard (`montage-storyboard`)

Write `project/BOARD.md`, one card per scene:

```
S03 · 5.00–7.50 · paper · "Every motion you see… is code."
  focal:   the word "code" (yellow highlight, 300px serif italic sticker)
  layout:  headline top-third, editor card 960w bottom half, nothing below y1700
  enter:   words rise on onset (snap 0.4s) · card lands with spring.land from y+300
  life:    camera push 1.00→1.04 · code lines type at 28cps · cursor blink
  exit:    → cut S04 at at('colors')-0.1 · type: slats(7, up) · whoosh
  sfx:     pop @ at('code') · click×6 during typing (−24 dB)
```

Rules to board by (from `references/composition-layout.md` and `references/rhythm-editing.md`):
- **Fill the frame.** The hero text fills 75–92% of the safe width (`MM.text.fit`). Never leave a 40% empty half by accident.
- **One focal point per moment.** At most 3 things move at once. Only one highlighted word is on screen.
- **No dead air.** Something meaningful changes every 0.5–0.7 s, and the camera is never perfectly still.
- **Frame 0 is a designed frame.** It is the thumbnail, so it can't be an empty background.
- **Vary the cut.** Don't use the same transition twice in a row. Choose each one by meaning (see `references/transitions.md`).
- **Don't duplicate captions.** If the words are already big on screen, hide the caption box.
- **Ghost karaoke** fills a frame that would otherwise wait for words. Show the whole line at 13–16% opacity and light each word as it's spoken (`onWords(...,'fade',{dim:.16})`, or a punch). It gives frame 0 a full thumbnail too.
- **Slot, then payoff.** A container (a yellow block, a card) lands 0.5–1.5 s before its hero word, and the word slams into it on the onset. Never leave a CTA line alone on a bare background.

## Phase 4: Build (`montage-motion`, then `montage-editor`)

```bash
bash $E/new_project.sh project voice-kinetic      # or: showreel
```

This copies the engine runtime (`lib/`), fonts and a working template. Read `references/engine-api.md`.
- `montage-motion` writes the scenes in `composition.html`. Each element is a function of `t`, keyed to `MM.at('word')`. Secondary motion goes on every scene (camera drift, parallax layers, a detail that keeps living). Sound cues are declared in `setup()` with `MM.cue()`.
- `montage-editor` owns `S` (scene table) and `CUTS`. A cut lands on a word onset or a beat, 0.05–0.12 s **before** the word (the eye arrives just ahead of the ear). Transition durations are 0.3–0.7 s.
- Motion vocabulary: `references/motion-grammar.md`. Type: `references/kinetic-typography.md`.

## Phase 5: Stills gate (always run it before a full render)

```bash
node $E/render.mjs --comp project/composition.html --every 0.5          # contact sheet
node $E/render.mjs --comp project/composition.html --stills 2.4,2.5,2.6 # around each cut
node $E/render.mjs --comp project/composition.html --qc                 # off-frame / unsafe / overlap
```

Look at the contact sheet (actually open the image). Fix overflow, overlap, empty halves, wrong focal points and bad Arabic shaping.
Run `--qc` until it's clean, or until every remaining flag is explained (for example, a spring overshoot for 2 frames).

## Phase 6: Render

```bash
node $E/render.mjs --comp project/composition.html --workers <cores> --shutter 2    # true motion blur
```

`--shutter 4` blends 4 sub-frames per frame on a 180° shutter, so fast moves smear like a camera. Use it for every final render that has zoom, stack, panel or whip transitions. `--shutter 2` is only for drafts: on moves faster than about 40 px/frame it leaves **double images** (two sharp copies), which the critic will fail.
Outputs: `out/video-silent.mp4` and `out/cues.json`.

## Phase 7: Sound (`montage-sound`)

```bash
python3 $E/audio/sound.py bed --dur <D> --bpm 96 --style pulse --mute a:b --out bed.wav    # or the user's licensed track
python3 $E/audio/sound.py sfx --cues out/cues.json --out sfx.wav
python3 $E/audio/sound.py mix --voice voice-clean.wav --bed bed.wav --sfx sfx.wav --out mix.wav   # ducking + two-pass −14 LUFS
python3 $E/audio/sound.py mux --video out/video-silent.mp4 --audio mix.wav --out final.mp4
```

The voice always wins, and the music ducks about 60% under it. A silence before the payoff is a tool too. See `references/sound-design.md`.

## Phase 8: Critic (`montage-critic`, independent)

```bash
python3 $E/qc/qc_video.py final.mp4 --timeline project/timeline.json --cues out/cues.json --sheet qc-sheet.png --json qc.json
```

Then the critic watches: a still from every scene, the 2 s around every cut, the first and last frames.
It scores `references/qc-rubric.md`. **Ship only when there are no hard fails and every category scores ≥ 8/10.**
Otherwise it returns a numbered fix list to the owning agent, and you loop from that phase. Two loops at most, then show the user what's left.

## Deliver

- `final.mp4`, and a `no-music` version when the platform's own sound may be used.
- `voice-clean.wav`.
- A scene table (time, words, transition).
- Any script/voice differences.
- The critic's score sheet.

## Negative list (never ship any of these)

- An "AI look": neon glow, lens flares, particles for no reason, glitch, chromatic aberration, rainbow gradients, a spinning 3D logo, a moving background grid, camera shake.
- Animated letter-by-letter typing outside a "typing" context (a prompt box or a document).
- Text outside the safe area, two text blocks colliding, or broken Arabic letter joins (split Arabic by **words**, never characters).
- A caption that differs from the voice, or on-screen words that nobody says (except labels, the handle and the logo).
- Dead air: a frozen picture for more than 0.7 s anywhere except the final hold.
- An empty frame 0, or an empty frame mid-transition.
- More than one highlighted word at once. More than 3 elements starting to move at the same moment.
- Music louder than the voice, a muffled or robotic voice, or a final loudness off −14 ±1 LUFS (social).
- A generated or redrawn logo. Always use the supplied file.
- Footage, music, fonts or images the user doesn't have rights to.

## Files

- `engine/`: the renderer, runtime libraries, audio, voice and QC tools (`references/engine-api.md`).
- `templates/voice-kinetic/`: voice-driven kinetic type (captions, highlight, strike, sticker, waveform).
- `templates/showreel/`: music-driven promo (fit type, cascade, counter, film strip, beat meter, footage with a speed ramp, track-in title).
- `references/`: the craft. Read the one for the phase you are in, not all of them at once.
