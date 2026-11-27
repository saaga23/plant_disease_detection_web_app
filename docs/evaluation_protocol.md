# Evaluation protocol

## What has actually been evaluated (and how to check)

1. **Artifact integrity** - SHA-256 of every model file vs
   `models/model_manifest.json`. Command: `python scripts/validate_models.py`.
   Verified locally on 2026-11-27 (all four artifacts PASS).
2. **Loading correctness** - all four models load and produce correctly
   shaped, finite outputs (integration tests, real artifacts, TF 2.21 /
   Python 3.12): `python -m pytest tests/integration`.
3. **Smoke inference** - zero-tensor forward passes return one finite score
   per class with sensible softmax sums (part of validate_models.py).

## What has NOT been evaluated

- **Accuracy of the deployed models**: no labeled evaluation set exists in
  the repository; no historical evaluation record survives. Any accuracy
  number for the deployed models would be fabricated, so none is claimed.
- **Calibration**: ECE/Brier are not reported because (a) no evaluation data
  exists here and (b) the models are explicitly labeled uncalibrated in the
  UI.
- **Field robustness**: no controlled corruption experiments have been run
  for the deployed models.

## Evaluating a model yourself

`scripts/evaluate_models.py` computes top-1 accuracy and macro-F1 against
your own class-labeled image folders (folder names are used as labels
because the shipped class ordering is unverified). The output states this
explicitly. It does not invent a test set.

```bash
python scripts/evaluate_models.py --model tomato --data-root path/to/tomato_test
```

## Stance on the PMLR paper's numbers

The paper's reported accuracies (tomato 34.69% -> 97.96%; cassava 52.42% ->
98.39%) belong to models and a dataset that are not in this repository.
They are neither reproduced nor disputed here; see
`docs/research_reproducibility.md` for the full traceability statement.
