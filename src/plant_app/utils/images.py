"""Shared image helpers for the UI layer."""
from __future__ import annotations

from .preprocessing import (  # noqa: F401  (re-exports)
    ALLOWED_FORMATS,
    ImageTooLargeError,
    InvalidImageError,
    load_image_from_bytes,
    load_image_from_path,
    to_model_input,
)


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024
    return f"{num_bytes} B"
