"""Image preprocessing: EXIF handling, RGB conversion, resizing, validation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "BMP", "WEBP"}


class InvalidImageError(ValueError):
    """Raised when an upload is not a usable image."""


class ImageTooLargeError(ValueError):
    """Raised when the upload exceeds the configured size limit."""


@dataclass
class PreprocessResult:
    width: int
    height: int
    source_format: str
    was_exif_rotated: bool


def load_image_from_bytes(data: bytes, max_mb: int = 10) -> tuple[Image.Image, PreprocessResult]:
    if len(data) == 0:
        raise InvalidImageError("Empty upload: no data received.")
    if len(data) > max_mb * 1024 * 1024:
        raise ImageTooLargeError(
            f"Upload is {len(data) / (1024 * 1024):.1f} MB, which exceeds the {max_mb} MB limit."
        )
    try:
        img = Image.open(__import__("io").BytesIO(data))
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Upload is not a readable image file.") from exc
    original_format = (img.format or "").upper()
    if original_format not in ALLOWED_FORMATS:
        raise InvalidImageError(
            f"Unsupported image format '{img.format}'. Allowed: {sorted(ALLOWED_FORMATS)}."
        )
    exif = img.getexif() if hasattr(img, "getexif") else None
    orientation = exif.get(274) if exif else None
    was_exif_rotated = orientation not in (None, 0, 1)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        logger.warning("EXIF transpose failed; using unrotated image.", exc_info=True)
        was_exif_rotated = False
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img, PreprocessResult(
        width=img.width,
        height=img.height,
        source_format=original_format or "RGB",
        was_exif_rotated=was_exif_rotated,
    )


def load_image_from_path(path: Path | str, max_mb: int = 10) -> tuple[Image.Image, PreprocessResult]:
    path = Path(path)
    if not path.exists():
        raise InvalidImageError(f"Image file not found: {path}")
    return load_image_from_bytes(path.read_bytes(), max_mb=max_mb)


def to_model_input(img: Image.Image, size: tuple[int, int]) -> "list[list[list[list[float]]]]":
    """Resize with bilinear interpolation and rescale to [0, 1].

    Produces a (1, h, w, 3) float32 batch. Rescaling by 1/255 must match the
    preprocessing used in training; the legacy training code for these models
    rescaled inputs this way, and the manifest documents this per model.
    """
    import numpy as np
    import tensorflow as tf

    if size[0] <= 0 or size[1] <= 0:
        raise InvalidImageError(f"Invalid model input size: {size}")
    arr = np.asarray(img, dtype=np.float32)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise InvalidImageError(f"Expected an RGB array, got shape {arr.shape}")
    batch = tf.image.resize(arr, size, method="bilinear")
    batch = tf.expand_dims(batch, axis=0) / 255.0
    return batch.numpy()
