#!/bin/bash
# Regenerate the README screenshot from the demo fixture.
#
# Never point this at a real dashboard. The screenshots used to be captured from
# a live machine and then masked; the masks slipped, and the published picture
# still had the original container names readable between them. The fixture
# invents everything, so there is nothing to mask and nothing to slip.
#
#   bash docs/make-screenshots.sh
#
# Needs Python 3 and Chrome (or Chromium). No npm, no node, no puppeteer.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8901}"
OUT="$ROOT/docs/screenshots/dashboard-full.png"

CHROME=""
for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$(command -v google-chrome || true)" \
    "$(command -v chromium || true)" \
    "$(command -v chromium-browser || true)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then CHROME="$candidate"; break; fi
done
if [ -z "$CHROME" ]; then
    echo "error: no Chrome or Chromium found" >&2
    exit 1
fi

python3 "$ROOT/docs/demo_fixture.py" "$PORT" >/dev/null &
FIXTURE=$!
trap 'kill $FIXTURE 2>/dev/null || true' EXIT

for _ in $(seq 1 40); do
    curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
    sleep 0.25
done

# --virtual-time-budget runs the page's own refresh loop far faster than the
# clock, so the charts fill with history before the shutter opens. The window is
# tall enough to hold the whole page: Chrome's --screenshot captures the
# viewport, not the document.
TMP="$(mktemp -d)"
"$CHROME" \
    --headless=new \
    --disable-gpu \
    --hide-scrollbars \
    --force-device-scale-factor=2 \
    --window-size=1414,3400 \
    --virtual-time-budget=620000 \
    --user-data-dir="$TMP" \
    --screenshot="$OUT" \
    "http://127.0.0.1:$PORT/" >/dev/null 2>&1 &
CHROME_PID=$!

# Chrome writes the file and then keeps running for minutes. Wait for the image
# to appear and settle, then stop it — otherwise this script hangs long after
# the picture is taken.
rm -f "$OUT"
LAST=""
for _ in $(seq 1 300); do
    sleep 1
    SIZE=$(wc -c < "$OUT" 2>/dev/null || echo 0)
    if [ "$SIZE" -gt 0 ] && [ "$SIZE" = "$LAST" ]; then break; fi
    LAST="$SIZE"
done
kill "$CHROME_PID" 2>/dev/null || true
wait "$CHROME_PID" 2>/dev/null || true
rm -rf "$TMP"

if [ ! -s "$OUT" ]; then
    echo "error: no screenshot was written" >&2
    exit 1
fi

# The window is taller than the page on purpose — a viewport that came up short
# would cut the footer off. Trim whatever background is left below the content,
# where Pillow is available; the picture is fine either way.
python3 - "$OUT" <<'PY_TRIM'
import sys
try:
    from PIL import Image
except ImportError:
    raise SystemExit(0)

path = sys.argv[1]
img = Image.open(path).convert("RGB")
w, h = img.size
bg = img.getpixel((4, h - 4))
px = img.load()
bottom = h
for y in range(h - 1, 0, -1):
    row = range(0, w, 7)   # sampling is enough to find where the page ends
    if any(px[x, y] != bg for x in row):
        bottom = min(h, y + 40)
        break
if bottom < h:
    img.crop((0, 0, w, bottom)).save(path)
    print(f"  trimmed {h - bottom} px of empty background")
PY_TRIM

echo "wrote $OUT"
python3 - "$OUT" <<'PY_SIZE'
import struct, sys
with open(sys.argv[1], "rb") as f:
    f.read(16)
    w, h = struct.unpack(">II", f.read(8))
print(f"  {w}x{h} pixels")
PY_SIZE
