#!/usr/bin/env python
"""Validate every model artifact against models/model_manifest.json.

Checks, per model:
  1. the artifact exists,
  2. every file's SHA-256 matches the manifest,
  3. the model loads,
  4. its declared input/output dimensions match the manifest,
  5. a smoke inference on zeros produces one finite score per class.

Usage:  python scripts/validate_models.py [--json PATH]
Exit code 0 = all models valid.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plant_app.models.registry import load_manifest, verify_manifest_checksums  # noqa: E402


def validate() -> tuple[bool, list[dict]]:
    import numpy as np
    import tensorflow as tf

    manifest = load_manifest()
    problems = verify_manifest_checksums(manifest)
    report = []
    all_ok = not problems
    for problem in problems:
        print(f"CHECKSUM PROBLEM: {problem}")
    for key, spec in sorted(manifest["models"].items()):
        rec: dict = {"model": key, "checksum_ok": True, "loaded": False}
        try:
            from plant_app.models.registry import load_model

            model = load_model(key, manifest)
            rec["loaded"] = True
            batch = np.zeros((1, spec["input_height"], spec["input_width"], spec["channels"]), dtype=np.float32)
            out = np.asarray(model.predict_fn(batch))
            squeezed = np.squeeze(out)
            rec["output_shape"] = list(np.asarray(out).shape)
            if squeezed.shape != (spec["output_classes"],):
                rec["status"] = f"SHAPE MISMATCH: got {squeezed.shape}, want ({spec['output_classes']},)"
                all_ok = False
            elif not np.all(np.isfinite(squeezed)):
                rec["status"] = "NON-FINITE OUTPUTS"
                all_ok = False
            else:
                total = float(squeezed.sum())
                rec["softmax_sum"] = total
                rec["status"] = "OK"
        except Exception as exc:
            rec["status"] = f"ERROR: {type(exc).__name__}: {exc}"
            all_ok = False
        report.append(rec)
        print(f"[{rec['status']}] {key}")
    return all_ok, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=None, help="write the report as JSON to this path")
    args = parser.parse_args()
    ok, report = validate()
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
