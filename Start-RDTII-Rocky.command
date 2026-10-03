#!/bin/sh
# RDTII Rocky: double-click (macOS) or run (Linux) to open the interface in a window of its own.
# Closing the window stops it. Nothing is installed; Python 3.10 or newer is all it needs.
cd "$(dirname "$0")" || exit 1
for py in .venv/bin/python python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" interface/app.py --window "$@"
  fi
done
echo "Python 3.10 or newer is needed and was not found."
echo "Install it from https://www.python.org/downloads/ and start this file again."
printf "Press Return to close. "
read -r _
exit 1
