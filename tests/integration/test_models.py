"""Integration tests: real model loading and inference (requires TF + artifacts)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

tf = pytest.importorskip("tensorflow")

from plant_app.inference.predictor import predict_image  # noqa: E402
from plant_app.inference.preprocessing import load_image_from_bytes, to_model_input  # noqa: E402
from plant_app.models.registry import load_manifest, load_model, verify_manifest_checksums  # noqa: E402
from tests.conftest import make_png  # noqa: E402

MANIFEST = load_manifest()
KEYS = ["tomato", "potato", "pepper", "pest"]


def test_all_artifacts_checksummed():
    assert verify_manifest_checksums(MANIFEST) == []


@pytest.mark.parametrize("key", KEYS)
def test_model_loads_and_predicts(key):
    model = load_model(key, MANIFEST)
    img, _ = load_image_from_bytes(make_png(size=(640, 480), noise=0.05, seed=hash(key) % 1000))
    pred = predict_image(img, model)
    assert 0.0 <= pred.top_score <= 1.0
    assert len(pred.probabilities) == model.output_classes
    assert pred.top_class in model.classes
    assert pred.is_uncalibrated is True


@pytest.mark.parametrize("key", KEYS)
def test_input_shape_matches_manifest(key):
    import numpy as np

    model = load_model(key, MANIFEST)
    spec = MANIFEST["models"][key]
    batch = to_model_input(load_image_from_bytes(make_png())[0], model.input_size)
    assert tuple(batch.shape) == (1, spec["input_height"], spec["input_width"], 3)
    out = np.asarray(model.predict_fn(batch))
    assert out.shape[-1] == spec["output_classes"]
