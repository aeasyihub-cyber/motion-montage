# Alignment without an ASR model

When Whisper or Parakeet can't be downloaded (blocked network) or mishears a dialect, align the user's own script to the voice.

```bash
python3 $E/align/esalign.py     --audio voice.wav --script script.txt --lang ar --out words.json   # eSpeak NG words + MFCC DTW
python3 $E/align/refine_pauses.py ...   # snap line boundaries to real pauses at punctuation
python3 $E/align/phrase_even.py ...     # spread words inside a phrase by letter count
python3 $E/align/snap_minima.py ...     # move each boundary to the nearest energy minimum
python3 $E/voice/align.py --words words.json --script script.txt --out project/timeline.json
```
Needs `pip install espeakng-loader librosa numpy`. `dp_align.py` assigns whole phrases to pauses by dynamic programming; use it for long takes.

Accuracy: line starts and ends are reliable; word onsets inside a line are about ±0.1 s. That is enough for onset-tied reveals but check hero words by ear.

## Delivery notes
- Final render: `--shutter 4`, 60 fps, 1080x1920. For review on a phone also export a light copy: `ffmpeg -i final.mp4 -vf "fps=30,scale=720:1280" -c:v libx264 -crf 24 -profile:v main -movflags +faststart -c:a copy light.mp4` (about 8 MB for 100 s).
- After the mix, run a limiter (`alimiter=limit=0.82`) so true peak stays under -1 dB at -14 LUFS.
- Check the voice for repeated words (a duplicated word in a take): cut with `atrim` + `acrossfade` (20 ms), then re-align.
- Chromium download blocked? Point `MM_CHROMIUM` at a preinstalled binary.
