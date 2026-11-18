#!/bin/bash
# Refresh share/vinyl_holder/ from out/ and zip it for sending.
# Run after rebuilding parts/vinyl_holder.py and parts/vinyl_holder_plates.py.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
B="$ROOT/share/vinyl_holder"
mkdir -p "$B/library_plates"
"$ROOT/.venv/bin/python" "$ROOT/share/render_side_view.py"  # preview.png is rendered separately (build123d MCP)
cp "$ROOT"/out/vinyl_holder/vinyl_holder.{stl,3mf,step} "$B/"
cp "$ROOT"/out/vinyl_holder_plates/plate_{2,4,6}.stl "$B/library_plates/"
cp "$ROOT/out/vinyl_holder_plates/PRINT.md" "$B/library_plates/PRINT_AT_LIBRARY.md"
cd "$ROOT/share" && zip -qr -X vinyl_holder.zip vinyl_holder -x '*.DS_Store'
echo "bundle: $B"; ls -R "$B"; ls -l "$ROOT/share/vinyl_holder.zip"
