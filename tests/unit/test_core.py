"""Unit tests: configuration, class mapping, prediction formatting."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plant_app.config import get_settings  # noqa: E402
from plant_app.database import connection as db  # noqa: E402
from plant_app.inference.predictor import InferenceError, predict_image  # noqa: E402
from plant_app.inference.preprocessing import load_image_from_bytes  # noqa: E402
from plant_app.models.registry import (  # noqa: E402
    APP_HOME,
    ModelNotFoundError,
    load_manifest,
    load_model,
    verify_manifest_checksums,
)
from tests.conftest import make_png  # noqa: E402


class FakeModel:
    def __init__(self, classes, out, size=(128, 128), n=2, verified=True):
        self.key = 'fake'
        self.classes = classes
        self._out = out
        self.input_size = size
        self.input_shape = (size[1], size[0], 3)
        self.output_classes = n
        self.classes_verified = verified

    def predict(self, batch):
        return self._out


def test_settings_default_sqlite(monkeypatch):
    for var in ("DB_MODE", "DB_PASSWORD", "OPENAI_API_KEY", "SERPAPI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    s = get_settings()
    assert s.db_mode == "sqlite"
    assert not s.has_openai and not s.has_serpapi


def test_manifest_structure():
    m = load_manifest()
    assert set(m["models"]) == {"tomato", "potato", "pepper", "pest"}
    for key, spec in m["models"].items():
        assert spec["output_classes"] == len(spec["classes"]), key
        assert spec["classes_verified"] is False, key  # honesty invariant


def test_manifest_checksums_all_valid():
    m = load_manifest()
    assert verify_manifest_checksums(m) == []


def test_unknown_model_key_rejected():
    m = load_manifest()
    with pytest.raises(ModelNotFoundError):
        load_model("does_not_exist", m)


def test_tampered_checksum_detected(tmp_path):
    m = load_manifest()
    m2 = json.loads(json.dumps(m))
    first = list(m2["models"]["pepper"]["files"])[0]
    m2["models"]["pepper"]["files"][first] = "0" * 64
    problems = verify_manifest_checksums(m2)
    assert problems and "mismatch" in problems[0]


def test_prediction_formatting_and_normalization():
    img, _ = load_image_from_bytes(make_png())
    raw = [0.7, 0.3]
    pred = predict_image(img, FakeModel(["A", "B"], __import__("numpy").array([[raw]]), n=2))
    assert pred.top_class == "A"
    assert abs(pred.top_score - 0.7) < 1e-6
    assert len(pred.probabilities) == 2
    assert pred.is_uncalibrated is True
    assert pred.low_margin_warning is None


def test_low_margin_flagged():
    import numpy as np

    img, _ = load_image_from_bytes(make_png())
    pred = predict_image(img, FakeModel(["A", "B"], np.array([[0.52, 0.48]]), n=2))
    assert pred.low_margin_warning is not None


def test_nonfinite_scores_rejected():
    import numpy as np

    img, _ = load_image_from_bytes(make_png())
    with pytest.raises(InferenceError):
        predict_image(img, FakeModel(["A", "B"], np.array([[float("nan"), 0.5]]), n=2))


def test_wrong_output_shape_rejected():
    import numpy as np

    img, _ = load_image_from_bytes(make_png())
    with pytest.raises(InferenceError):
        predict_image(img, FakeModel(["A", "B"], np.array([[0.5, 0.3, 0.2]]), n=2))


def test_database_sqlite_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_MODE", "sqlite")
    monkeypatch.setattr(db, "DEMO_DATA_DIR", tmp_path)
    rec_id = db.insert_crop_record("Maize", "Field 1", 12.5, "2026-04-01", "2026-08-01", "ok")
    rows = db.list_crop_records()
    assert rows and rows[0]["crop_name"] == "Maize"
    assert rows[0]["quantity"] == 12.5
    assert rec_id >= 0


def test_database_rejects_bad_quantity(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_MODE", "sqlite")
    monkeypatch.setattr(db, "DEMO_DATA_DIR", tmp_path)
    with pytest.raises(ValueError):
        db.insert_crop_record("Maize", "F", -5, "2026-04-01", "2026-08-01", "")
    with pytest.raises(ValueError):
        db.insert_crop_record("   ", "F", 1, "2026-04-01", "2026-08-01", "")


def test_database_unavailable_mysql_message(monkeypatch):
    monkeypatch.setenv("DB_MODE", "mysql")
    monkeypatch.setenv("DB_HOST", "no-such-host.invalid")
    monkeypatch.setattr("sys.modules", {**__import__("sys").modules})
    try:
        import mysql.connector  # noqa: F401

        has_mysql = True
    except ImportError:
        has_mysql = False
    if not has_mysql:
        with pytest.raises(db.DatabaseUnavailableError):
            with db.get_connection():
                pass
    else:
        with pytest.raises(db.DatabaseUnavailableError):
            with db.get_connection():
                pass


def test_app_home_reference_exists():
    assert (APP_HOME / "docs" / "research_reproducibility.md").exists()
