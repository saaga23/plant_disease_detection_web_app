#!/usr/bin/env python
"""Run the full verification suite for this repository.

Usage:  python scripts/run_tests.py
        python scripts/run_tests.py --skip-models   (skip TF model validation)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(label: str, cmd: list[str]) -> bool:
    print(f"\n=== {label} ===")
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT)
    print(f"{label}: {'PASS' if proc.returncode == 0 else 'FAIL'}")
    return proc.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-models", action="store_true", help="skip TF model validation")
    args = parser.parse_args()

    results = []
    results.append(run("Unit and integration tests", [sys.executable, "-m", "pytest", "tests/"]))
    if not args.skip_models:
        results.append(run("Model validation", [sys.executable, "scripts/validate_models.py"]))
    print("\n=== SUMMARY ===")
    for i, ok in enumerate(results):
        print(f"step {i + 1}: {'PASS' if ok else 'FAIL'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
