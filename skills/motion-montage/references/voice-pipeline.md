# Voice pipeline: phone recording → studio voice → word clock

## 1. Clean (`voice/clean_voice.sh`)

The order matters:
1. trim silence (leave 0.2 s before the first word);
2. high-pass at 85 Hz;
3. **light** denoise: `arnndn` mix 0.5 (optional model) + `afftdn nr=8`;
4. presence EQ;
5. de-ess;
6. compress (−22 dB threshold, 3:1, attack 10, release 150);
7. soft expander (`agate` range 0.2, not a hard gate);
8. loudnorm.

- The script prints band levels before and after. Phone voices are usually weak at 2–5 kHz and heavy at 150–400 Hz.
  Tune `PRESENCE_DB` (3 kHz, default 6) and `AIR_DB` (5 kHz, default 4) until 2–4 kHz is within about 22 dB of the loudest band.
- **Never use strong denoise.** It's the "underwater/robot" sound and is worse than a little room noise.
- Targets: noise in pauses below −55 dB, a bright and present voice, no sibilant spikes.
- RNNoise models: <https://github.com/GregorR/rnnoise-models> (`sh.rnnn` is a good general model).

## 2. Transcribe (`voice/transcribe.py`)

- It tries `faster-whisper` (recommended: `pip install faster-whisper`) and falls back to `openai-whisper`. Both give word timestamps.
- `--lang` matters for accuracy (`en`, `ar`, `hu`, `tr`, …). Use model `medium` or larger for non-English and dialects.
- Whisper may "correct" dialect spellings. `align.py` maps the heard words back onto the user's own script.

## 3. Align (`voice/align.py`)

- Input `script.txt` has one line per beat. `#marker` at the start of a line names it. `*word*` marks emphasis.
- Output `timeline.json` + `timeline.js`, with `words[{w,s,e,line,emph}]`, `lines[{text,said,s,e,key}]`, `markers{}`, `diffs[]` and `duration`.
- **Report `diffs` to the user.** Captions use what was actually said.
- It prints the pauses longer than 0.6 s. These are your natural cut points.

## 4. Envelope (`voice/envelope.py`)

`window.VOICE_ENV` gives a per-frame 0..1 loudness for waveforms, mouth-like pulses and audio-reactive scale.
Never fake a waveform when the real envelope is available.

## In the composition

```js
MM.loadTimeline(window.TIMELINE);
MM.at('motion')        // onset of first "motion"
MM.at('no', 2)         // second "no"
MM.endOf('camera')     // end of the word
MM.at('#hook')         // marker
```
