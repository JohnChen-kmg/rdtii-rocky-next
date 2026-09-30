import os
import sys
from pathlib import Path

# src-layout + root-level config package are importable without install
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

HANDOFF1_DIR = Path(os.environ.get("HANDOFF1_DIR", REPO_ROOT.parent / "rdtii-p1-scrape" / "handoff1_v2"))
SAMPLE_DOCS = REPO_ROOT / "sample_docs" / "Sample legislations"
