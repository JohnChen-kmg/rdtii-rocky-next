"""Enable `python -m p1_scrape ...` (adds the repo root so `config` is importable)."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from p1_scrape.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
