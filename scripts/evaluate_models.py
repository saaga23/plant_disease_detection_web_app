#!/usr/bin/env python
"""Evaluate a model on an image directory: scripts/evaluate_models.py.

Deterministic evaluation harness (no fabricated results). It computes
top-1 accuracy and macro-F1 on a folder structured as:

    dataset_root/
        class_a/ img1.jpg ...
        class_b/ img2.jpg ...

The class folder names must match the manifest's class names, because the
index-to-name ordering of the shipped models is unverified (see
docs/model_cards). This script therefore evaluates models with the class
layout you provide, and labels accuracy as computed against YOUR ordering.

Usage:
  python scripts/evaluate_models.py --model tomato --data-root path/to/dataset
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plant_app.inference.predictor import predict_image  # noqa: E402
from plant_app.inference.preprocessing import load_image_from_path  # noqa: E402
from plant_app.models.registry import load_manifest, load_model  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="manifest key (tomato/potato/pepper/pest)")
    parser.add_argument("--data-root", required=True, help="folder of per-class image subfolders")
    parser.add_argument("--max-per-class", type=int, default=100)
    parser.add_argument("--json", default=None, help="write metrics JSON here")
    args = parser.parse_args()

    manifest = load_manifest()
    model = load_model(args.model, manifest)
    root = Path(args.data_root)
    class_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if not class_dirs:
        print("No class subfolders found under", root)
        return 2
    unmatched = [d.name for d in class_dirs if d.name not in model.classes]
    if unmatched:
        print(
            f"WARNING: folders {unmatched} are not manifest class names "
            f"{model.classes}; they are still evaluated as their own classes."
        )
    labels, preds = [], []
    counts: Counter = Counter()
    for d in class_dirs:
        files = sorted(f for f in d.iterdir() if f.suffix.lower() in IMAGE_EXTS)[: args.max_per_class]
        for f in files:
            try:
                img, _ = load_image_from_path(f)
                pred = predict_image(img, model)
            except Exception as exc:
                print(f"SKIP {f}: {exc}")
                continue
            labels.append(d.name)
            preds.append(pred.top_class)
            counts[d.name] += 1
    if not labels:
        print("No images evaluated.")
        return 2
    # label-space union evaluated as-is (accuracy against provided folder names)
    label_set = sorted(set(labels))
    confusion = {c: {c2: 0 for c2 in label_set} for c in label_set}
    for t, p in zip(labels, preds):
        if p in label_set:
            confusion[t][p] += 1
    correct = sum(t == p for t, p in zip(labels, preds))
    macro_f1s = []
    for c in label_set:
        tp = sum(1 for t, p in zip(labels, preds) if t == c and p == c)
        fp = sum(1 for t, p in zip(labels, preds) if t != c and p == c)
        fn = sum(1 for t, p in zip(labels, preds) if t == c and p != c)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        macro_f1s.append(f1)
    metrics = {
        "model": args.model,
        "n_images": len(labels),
        "n_skipped": counts and None,
        "accuracy": correct / len(labels),
        "macro_f1": sum(macro_f1s) / len(macro_f1s),
        "note": "Accuracy is against YOUR folder naming; shipped class ordering is unverified (see model cards).",
        "confusion": confusion,
    }
    print(json.dumps({k: v for k, v in metrics.items() if k != "confusion"}, indent=2))
    if args.json:
        Path(args.json).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
