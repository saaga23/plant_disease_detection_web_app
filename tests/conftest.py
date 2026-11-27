"""Shared test fixtures and synthetic test-image factory.

Test images are generated programmatically (deterministic numpy arrays
encoded to PNG) so the suite needs no network and no committed binary
fixtures.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image


def make_png(size: tuple[int, int] = (64, 64), color=(120, 180, 60), seed: int = 0,
             mode: str = "RGB", add_exif: bool = False, noise: float = 0.0) -> bytes:
    rng = np.random.default_rng(seed)
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    if noise > 0:
        arr = np.clip(arr.astype(int) + rng.integers(-int(noise * 255), int(noise * 255) + 1, arr.shape), 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    if mode == "RGBA":
        rgba = np.zeros((size[1], size[0], 4), dtype=np.uint8)
        rgba[..., :3] = arr
        rgba[..., 3] = 255
        img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    fmt = "PNG"
    if add_exif:
        fmt = "JPEG"
        exif = img.getexif()
        exif[274] = 6  # orientation tag: rotate 90
        img.save(buf, format=fmt, exif=exif)
    else:
        img.save(buf, format=fmt)
    return buf.getvalue()


def write_png(path: Path, **kwargs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_png(**kwargs))
    return path
