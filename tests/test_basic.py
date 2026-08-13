"""Basic package import smoke tests for WordListsForHacking."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_import_wfh_modules() -> None:
    """Installable package must import cleanly."""
    module = importlib.import_module("wfh_modules")
    assert module is not None


def test_import_wfh_and_version() -> None:
    """CLI module must import and expose canonical VERSION as X.Y.Z."""
    module = importlib.import_module("wfh")
    version = getattr(module, "VERSION", None)
    assert isinstance(version, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version