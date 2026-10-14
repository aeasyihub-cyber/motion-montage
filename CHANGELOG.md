# Changelog

## 1.1.0 (2026-10-14): lessons from the first real remake
- New `voice/separate.py`: pulls the voice out of a finished video (UVR via sherpa-onnx), for remaking an old video.
- `transcribe.py`: new `--parakeet` backend (sherpa-onnx Parakeet TDT). Offline, accurate English word onsets.
- `qc_video.py`: sync is judged per accent type. Pops and hits are checked against word onsets, strikes against word ends, and cut whooshes against the cut-ahead window. `{"free":true}` marks a deliberate cue.
- `panel` and `stack` transitions get velocity-based directional blur, and `zoom` gains `blurB`.
- Docs:
  - use `--shutter 4` for finals, because 2 leaves double images on fast moves;
  - a warning about the empty middle frame of `sweep`;
  - two new patterns: ghost karaoke, and slot-then-payoff.

## 1.0.0 (2026-10-13)
- Engine: deterministic HTML→MP4 renderer (Playwright + ffmpeg), parallel workers, sub-frame motion blur (`--shutter`), stills/contact sheets, layout QC probe.
- Runtime: easing vocabulary and springs, keyframes, stagger, seeded drift, speed ramps; camera with parallax depth; velocity motion blur; footage image sequences; the voice word clock; sound cues.
- Kinetic type: fit-to-width, masked rise, onWords, pop, cascade, track-in, weight morph, highlight, strike, swap, counter, typewriter, captions.
- 12 transitions: cut, panel, wipe, push, whip, zoom, iris, slats, sweep, stack, dissolve, dip.
- Audio: synthesised music bed (pulse/warm/tense), 9 SFX types, ducking, two-pass −14 LUFS master; beat detection.
- Voice: clean-up chain with a spectrum print, Whisper word timestamps, script alignment with a diff report, envelope for waveforms.
- QC: dead-air (freezedetect), loudness and true peak, cuts, sync vs words, contact sheet.
- 7 agents: director, timing, storyboard, motion, editor, sound, critic.
- Templates: `voice-kinetic`, `showreel`.
