"""Standard-library tests for the interface. Run: python -m unittest discover interface/tests"""
import sys
from pathlib import Path

INTERFACE = Path(__file__).resolve().parents[1]
if str(INTERFACE) not in sys.path:
    sys.path.insert(0, str(INTERFACE))
