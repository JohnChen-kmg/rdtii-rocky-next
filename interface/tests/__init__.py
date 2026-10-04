"""Standard-library tests for the interface. Run: python -m unittest discover interface/tests"""
import sys
from pathlib import Path
from unittest import mock

INTERFACE = Path(__file__).resolve().parents[1]
if str(INTERFACE) not in sys.path:
    sys.path.insert(0, str(INTERFACE))

from rdtii_ui import probes  # noqa: E402

# Whether the Python running these tests also holds a stage's packages is a fact about the machine, not about
# the interface: a Check must not fail a test because pytesseract is not installed here. Tests about the probe
# itself call the real one, with a runner of their own.
REAL_PROBE_IMPORTS = probes.probe_imports
mock.patch.object(probes, "probe_imports", return_value={"ok": True, "missing": ""}).start()
