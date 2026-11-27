"""Unit tests: image validation and preprocessing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plant_app.inference.preprocessing import (  # noqa: E402
    ImageTooLargeError,
    InvalidImageError,
    load_image_from_bytes,
    to_model_input,
)
from tests.conftest import make_png  # noqa: E402


def test_valid_png_loads():
    img, meta = load_image_from_bytes(make_png())
    assert img.size == (64, 64)
    assert img.mode == "RGB"
    assert meta.source_format == "PNG"


def test_rgba_converted_to_rgb():
    img, _ = load_image_from_bytes(make_png(mode="RGBA"))
    assert img.mode == "RGB"


def test_empty_upload_rejected():
    with pytest.raises(InvalidImageError):
        load_image_from_bytes(b"")


def test_corrupt_bytes_rejected():
    with pytest.raises(InvalidImageError):
        load_image_from_bytes(b"this is not an image" * 100)


def test_oversized_upload_rejected():
    big = make_png() + b"\0" * (11 * 1024 * 1024)
    with pytest.raises(ImageTooLargeError):
        load_image_from_bytes(big, max_mb=10)


def test_exif_orientation_applied():
    img, meta = load_image_from_bytes(make_png(add_exif=True))
    assert img.size == (64, 64)  # orientation 6 keeps square dims; transpose applied
    assert isinstance(meta.was_exif_rotated, bool)


def test_to_model_input_shape_and_scale():
    img, _ = load_image_from_bytes(make_png(size=(300, 200)))
    batch = to_model_input(img, (256, 256))
    assert tuple(batch.shape) == (1, 256, 256, 3)
    assert float(batch.min()) >= 0.0 and float(batch.max()) <= 1.0


def test_to_model_input_rejects_bad_size():
    img, _ = load_image_from_bytes(make_png())
    with pytest.raises(InvalidImageError):
        to_model_input(img, (0, 0))
