#!/usr/bin/env bash
# motion-montage · new_project.sh — scaffold a render-ready project folder.
#
#   bash new_project.sh <project-dir> [template]      template: voice-kinetic (default) | showreel
#
# Creates:
#   <dir>/composition.html   ← the film (edit this)
#   <dir>/lib/               ← engine runtime (motion, stage, text, transitions)
#   <dir>/fonts/             ← default font set (Inter Tight, Fraunces, JetBrains Mono — all OFL)
#   <dir>/assets/ footage/ out/
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:?usage: new_project.sh <dir> [template]}"; TPL="${2:-voice-kinetic}"
SRC="$HERE/../templates/$TPL"
[[ -d "$SRC" ]] || { echo "unknown template: $TPL (have: $(ls "$HERE/../templates" | tr '\n' ' '))"; exit 1; }

if [[ ! -d "$HERE/node_modules/playwright" ]]; then
  echo "▸ installing engine dependencies (once)…"
  (cd "$HERE" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-} npm install --no-audit --no-fund --silent)
  if [[ -z "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" ]]; then (cd "$HERE" && npx playwright install chromium) || true; fi
fi

mkdir -p "$DIR"/{lib,fonts,assets,footage,out}
cp -r "$SRC"/. "$DIR"/
cp "$HERE"/lib/*.js "$DIR/lib/"

NM="$HERE/node_modules"
cp "$NM/@fontsource-variable/inter-tight/files/inter-tight-latin-wght-normal.woff2" "$DIR/fonts/InterTight.woff2"
cp "$NM/@fontsource-variable/inter-tight/files/inter-tight-latin-wght-italic.woff2" "$DIR/fonts/InterTight-Italic.woff2"
cp "$NM/@fontsource-variable/fraunces/files/fraunces-latin-full-normal.woff2" "$DIR/fonts/Fraunces.woff2"
cp "$NM/@fontsource-variable/fraunces/files/fraunces-latin-full-italic.woff2" "$DIR/fonts/Fraunces-Italic.woff2"
cp "$NM/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2" "$DIR/fonts/JetBrainsMono-500.woff2"

cat <<EOF
✓ project ready: $DIR   (template: $TPL)

next:
  stills  node $HERE/render.mjs --comp $DIR/composition.html --every 0.5
  qc      node $HERE/render.mjs --comp $DIR/composition.html --qc
  render  node $HERE/render.mjs --comp $DIR/composition.html --shutter 2

more fonts: npm i @fontsource/<name> in $HERE and copy the .woff2 into $DIR/fonts
  (Arabic: @fontsource/lalezar, @fontsource/rubik [arabic subset], @fontsource/noto-kufi-arabic)
EOF
