#!/bin/bash
# Rebuild the edited part; exit 2 sends failures back to Claude.
f=$(jq -r '.tool_input.file_path')
case "$f" in
  */parts/*.py|*/coupons/*.py)
    out=$(cd "$CLAUDE_PROJECT_DIR" && env -u CAD_SHOW "$CLAUDE_PROJECT_DIR/.venv/bin/python" "$f" 2>&1) || { echo "$out" >&2; exit 2; } ;;
esac
exit 0
