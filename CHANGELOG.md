# Changelog

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
