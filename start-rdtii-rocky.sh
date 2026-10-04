#!/bin/sh
# RDTII Rocky: double-click (macOS) or run (Linux) to open the interface in a window of its own.
# Closing the window stops it. Nothing is installed; the interface needs Python 3.10 or newer, and a
# .venv at the top of the repository (README, Quick Start 2) is used when there is one.
cd "$(dirname "$0")" || exit 1
for py in .venv/bin/python python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    exec "$py" interface/app.py --window "$@"
  fi
done
echo "Python 3.10 or newer is needed and was not found."
echo "Install it (macOS: brew install python@3.12, or https://www.python.org/downloads/) and start this file again."
printf "Press Return to close. "
read -r _
exit 1
