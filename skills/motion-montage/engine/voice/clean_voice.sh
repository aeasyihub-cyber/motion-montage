#!/usr/bin/env bash
# motion-montage · clean_voice.sh — phone recording → studio-clear voice (ffmpeg only)
#
#   bash clean_voice.sh input.m4a voice-clean.wav [rnnoise-model.rnnn]
#
# Chain (order matters): trim silence → high-pass → light denoise → presence EQ →
# de-ess → compress → soft expander → loudnorm.  NEVER heavy denoise (sounds underwater).
# Optional RNNoise model: https://github.com/GregorR/rnnoise-models (e.g. sh.rnnn), used at mix=0.5.
# Prints a band analysis before and after so the EQ can be adjusted to the actual mic.
set -euo pipefail
IN="$1"; OUT="${2:-voice-clean.wav}"; RNN="${3:-}"

bands() {  # rough spectrum: RMS level per band
  for b in "60:120" "120:250" "250:500" "500:1000" "1000:2000" "2000:4000" "4000:8000" "8000:12000"; do
    lo=${b%:*}; hi=${b#*:}
    lvl=$(ffmpeg -hide_banner -v info -i "$1" -af "highpass=f=$lo,lowpass=f=$hi,astats=metadata=0:measure_overall=RMS_level:measure_perchannel=0" -f null - 2>&1 \
      | grep -m1 "RMS level dB" | awk '{print $NF}')
    printf "  %6s–%-6s Hz  %s dB\n" "$lo" "$hi" "$lvl"
  done
}

echo "▸ input spectrum ($IN)"; bands "$IN"

DN="afftdn=nr=8:nf=-45"
[[ -n "$RNN" && -f "$RNN" ]] && DN="arnndn=m=$RNN:mix=0.5,$DN"

CHAIN="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.2,\
areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse,\
highpass=f=85,\
$DN,\
equalizer=f=150:t=q:w=1:g=-1.5,\
equalizer=f=300:t=q:w=1:g=-4,\
equalizer=f=1200:t=q:w=1:g=2,\
equalizer=f=3000:t=q:w=1.2:g=${PRESENCE_DB:-6},\
equalizer=f=5000:t=q:w=1.2:g=${AIR_DB:-4},\
highshelf=f=7500:g=3,\
deesser=i=0.4,\
acompressor=threshold=-22dB:ratio=3:attack=10:release=150:makeup=2,\
agate=range=0.2:ratio=2:threshold=-42dB,\
loudnorm=I=-16:TP=-1.5:LRA=7"

ffmpeg -y -v error -i "$IN" -af "$CHAIN" -ar 48000 -ac 1 "$OUT"

echo "▸ output spectrum ($OUT)"; bands "$OUT"
echo "▸ noise floor in pauses (want < -55 dB):"
ffmpeg -hide_banner -i "$OUT" -af "silencedetect=n=-40dB:d=0.3" -f null - 2>&1 | grep -c silence_start | xargs -I{} echo "  {} pauses found"
ffmpeg -hide_banner -i "$OUT" -af "agate=threshold=-40dB:range=0,astats=measure_overall=RMS_trough:measure_perchannel=0" -f null - 2>&1 | grep -m1 "RMS trough" || true
echo "✓ $OUT   (tune: PRESENCE_DB / AIR_DB env vars; goal: 2–4 kHz within ~22 dB of the loudest band)"
