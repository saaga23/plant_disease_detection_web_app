"""Prediction pipeline: validation, inference, and honest output shaping.

Design notes
------------
* Model outputs are SOFTMAX PROBABILITIES FROM AN UNCALIBRATED MODEL.
  None of the four shipped models has undergone probability calibration
  (temperature/Platt/isotonic), so the number shown as "confidence" is a raw
  model score, not a calibrated probability. The UI states this explicitly.
* There is no out-of-distribution detector or selective-prediction layer in
  this prototype; instead the app (a) reports the full probability vector,
  (b) flags low-margin predictions, and (c) recommends expert confirmation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from ..models.registry import LoadedModel
from .preprocessing import to_model_input


class InferenceError(RuntimeError):
    """Raised when inference produces an unusable result."""


@dataclass
class Prediction:
    top_class: str
    top_score: float
    probabilities: list[tuple[str, float]]
    is_uncalibrated: bool = True
    low_margin_warning: str | None = None


def predict_image(img: Image.Image, model: LoadedModel, max_mb: int = 10) -> Prediction:
    batch = to_model_input(img, model.input_size)
    try:
        raw = model.predict(batch)
    except Exception as exc:  # pragma: no cover - depends on TF internals
        raise InferenceError(f"Model inference failed: {exc}") from exc
    scores = np.squeeze(np.asarray(raw, dtype=np.float64))
    if scores.ndim != 1 or scores.shape[0] != model.output_classes:
        raise InferenceError(
            f"Model '{model.key}' returned shape {scores.shape}, "
            f"expected {model.output_classes} class scores."
        )
    if not np.all(np.isfinite(scores)):
        raise InferenceError(f"Model '{model.key}' produced non-finite scores (NaN/inf).")
    total = float(np.sum(scores))
    if total <= 0 or not np.isfinite(total):
        raise InferenceError(f"Model '{model.key}' produced a degenerate probability vector.")
    probs = scores / total  # normalize defensively even if the head lacks softmax
    order = np.argsort(-probs)
    ranked = [(model.classes[i] if i < len(model.classes) else f"class_{i}", float(probs[i])) for i in order]
    top1, top2 = float(probs[order[0]]), float(probs[order[1]]) if len(order) > 1 else 0.0
    margin = top1 - top2
    low_margin_warning = None
    if margin < 0.10:
        low_margin_warning = (
            "The two most likely classes are nearly tied "
            f"(margin {margin:.3f}); treat this label as unreliable."
        )
    return Prediction(
        top_class=ranked[0][0],
        top_score=top1,
        probabilities=ranked,
        is_uncalibrated=True,
        low_margin_warning=low_margin_warning,
    )
