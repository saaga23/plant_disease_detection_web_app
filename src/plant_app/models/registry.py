"""Model manifest access, checksum validation, and lazy loading.

Models are loaded only when a page first needs them and are cached for reuse.
Two artifact formats are supported:

* Keras 2-era SavedModel directories (tomato, potato) - loaded with
  ``tf.keras.models.load_model`` on TF <= 2.15 or via ``TFSMLayer`` on Keras 3.
* Keras H5 files (pepper, pest) - loadable on both Keras 2 and Keras 3.

Every artifact is checksum-verified against ``models/model_manifest.json``
before the first use so that a corrupt or partial download fails loudly
instead of producing garbage predictions.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import MANIFEST_PATH

logger = logging.getLogger(__name__)

APP_HOME = MANIFEST_PATH.parent.parent


class ManifestError(RuntimeError):
    """Raised when the model manifest is missing, malformed, or fails checksums."""


class ModelNotFoundError(RuntimeError):
    """Raised when a declared model artifact is missing."""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or MANIFEST_PATH
    if not manifest_path.exists():
        raise ManifestError(f"Model manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Model manifest is not valid JSON: {exc}") from exc
    if "models" not in manifest or not isinstance(manifest["models"], dict):
        raise ManifestError("Model manifest must contain a 'models' mapping")
    return manifest


def verify_manifest_checksums(manifest: dict[str, Any]) -> list[str]:
    """Return a list of problems; empty list means every checksum matched."""
    problems: list[str] = []
    for key, spec in manifest["models"].items():
        artifact = APP_HOME / spec["path"]
        if not artifact.exists():
            problems.append(f"{key}: artifact missing at {artifact}")
            continue
        files = spec.get("files", {})
        if not files:  # single-file artifact: verify the artifact itself
            files = {spec["path"]: spec.get("sha256", "")}
        for rel, expected in files.items():
            f = APP_HOME / rel
            if not f.exists():
                problems.append(f"{key}: file missing {rel}")
                continue
            actual = _sha256_file(f)
            if actual != expected:
                problems.append(f"{key}: checksum mismatch for {rel}")
    return problems


@dataclass
class LoadedModel:
    key: str
    predict_fn: Any  # callable(np.ndarray batch) -> np.ndarray probabilities
    input_size: tuple[int, int]
    input_shape: tuple[int, ...]
    output_classes: int
    classes: list[str]
    classes_verified: bool

    def predict(self, batch) -> Any:
        return self.predict_fn(batch)


def _make_h5_predict_fn(model):
    def predict(batch):
        return model.predict(batch, verbose=0)

    return predict


def _make_savedmodel_predict_fn(path: Path):
    """Return a predict callable that works on Keras 2 and Keras 3."""
    import numpy as np
    import tensorflow as tf

    try:
        model = tf.keras.models.load_model(str(path), compile=False)
        return _make_h5_predict_fn(model)
    except ValueError:
        # Keras 3 removed legacy SavedModel support from load_model.
        layer = tf.keras.layers.TFSMLayer(str(path), call_endpoint="serving_default")

        def predict(batch):
            out = layer(tf.convert_to_tensor(batch))
            if isinstance(out, dict):
                out = next(iter(out.values()))
            return np.asarray(out)

        return predict


def load_model(key: str, manifest: dict[str, Any] | None = None) -> LoadedModel:
    """Load one model by manifest key. Heavy import happens here, not at app start."""
    manifest = manifest or load_manifest()
    if key not in manifest["models"]:
        raise ModelNotFoundError(
            f"Unknown model key '{key}'. Available: {sorted(manifest['models'])}"
        )
    spec = manifest["models"][key]
    artifact = APP_HOME / spec["path"]
    if not artifact.exists():
        raise ModelNotFoundError(
            f"Model artifact for '{key}' is missing at {artifact}. "
            "If this is a Git LFS file, run 'git lfs pull' and retry."
        )
    problems = verify_manifest_checksums({"models": {key: spec}})
    if problems:
        raise ManifestError("; ".join(problems))

    import tensorflow as tf  # deferred heavy import

    if artifact.is_dir():
        predict_fn = _make_savedmodel_predict_fn(artifact)
    else:
        model = tf.keras.models.load_model(str(artifact), compile=False)
        predict_fn = _make_h5_predict_fn(model)

    return LoadedModel(
        key=key,
        predict_fn=predict_fn,
        input_size=(spec["input_width"], spec["input_height"]),
        input_shape=(spec["input_height"], spec["input_width"], spec["channels"]),
        output_classes=int(spec["output_classes"]),
        classes=list(spec["classes"]),
        classes_verified=bool(spec.get("classes_verified", False)),
    )
