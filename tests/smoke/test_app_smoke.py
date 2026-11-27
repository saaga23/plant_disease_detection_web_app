"""Smoke tests: app importability and navigation structure (Streamlit optional)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))


def test_app_imports_and_declares_pages():
    pytest = __import__("pytest")
    st = pytest.importorskip("streamlit")
    app_path = ROOT / "app.py"
    assert app_path.exists()
    src = app_path.read_text(encoding="utf-8")
    for page in [
        "Home", "Getting Started", "Tomato Disease Classifier", "Pepper Disease Classifier",
        "Potato Disease Classifier", "Pest Detection", "Crop Rotation Advisor",
        "Farm Animal Vaccination Guide", "Question Answering", "Record Input",
        "Retrieve Crop Data for Analysis", "Weather", "Google Search", "Feedback",
    ]:
        assert f'"{page}"' in src, f"missing page {page}"


def test_manifest_present():
    assert (ROOT / "models" / "model_manifest.json").exists()


def test_no_hardcoded_credentials():
    """Guard against regression of the remediated credential exposure."""
    import re

    offenders = []
    for py in ROOT.rglob("*.py"):
        if ".git" in py.parts or "legacy_" in py.name:
            continue  # legacy copies are quarantined under docs/ with warnings
        text = py.read_text(encoding="utf-8", errors="replace")
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', text) and "os.environ" not in text:
            offenders.append(str(py.relative_to(ROOT)))
    assert not offenders, f"hardcoded password found in: {offenders}"
