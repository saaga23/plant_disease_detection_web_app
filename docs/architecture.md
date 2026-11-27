# Architecture

## Overview

```
┌────────────────────────────────────────────────────────────────┐
│ app.py (Streamlit UI — 14 pages)                               │
│   navigation · upload widgets · result rendering               │
└───────┬───────────────────────┬──────────────────────┬─────────┘
        │                       │                      │
        ▼                       ▼                      ▼
┌────────────────┐   ┌────────────────────┐   ┌──────────────────┐
│ plant_app.models│  │ plant_app.inference│   │ plant_app.services│
│ registry.py     │  │ preprocessing.py   │   │ weather (Open-   │
│ manifest + SHA- │  │ EXIF→RGB→resize→   │   │  Meto, no key)   │
│ 256 + lazy load │  │ /255 → batch       │   │ web_search       │
│ dual Keras2/3   │  │ predictor.py       │   │  (SerpAPI, opt.) │
│ loading paths   │  │ validation, probs, │   │ qa (OpenAI, opt.)│
└───────┬────────┘   │ low-margin warning │   └──────────────────┘
        │            └─────────┬──────────┘
        ▼                      ▼
┌────────────────────────────────────┐   ┌────────────────────────┐
│ models/                            │   │ plant_app.database     │
│  CNN_model_tomatoes/ (SavedModel)  │   │ connection.py          │
│  potatoed_disease_classifier/      │   │ sqlite (default, zero  │
│  pepper-model.h5 (LFS)             │   │  setup) | mysql (env   │
│  pest_detection_model2.h5 (LFS)    │   │  vars + schema_mysql)  │
│  model_manifest.json (SHA-256)     │   │ scripts/schema_*.sql   │
└────────────────────────────────────┘   └────────────────────────┘
```

## Key design decisions

1. **Lazy, cached model loading.** Models load on first use of a page
   (`@st.cache_resource`), not at app start; a broken artifact fails that
   page with a clear message, not the whole app.
2. **Manifest-driven everything.** Paths, input sizes, class lists, and
   SHA-256 checksums live in `models/model_manifest.json`. `load_model()`
   verifies checksums before every load, so a truncated LFS download fails
   loudly.
3. **Dual-format loader.** Keras 3 (TF ≥ 2.16) removed legacy SavedModel
   support; `registry._make_savedmodel_predict_fn` tries `load_model` first
   and falls back to `TFSMLayer`. H5 files load natively on both generations.
   This removes the TF-version cliff of the legacy app (pinned TF 2.13 +
   Python ≤ 3.11 only).
4. **Honest predictions.** Outputs are labeled *uncalibrated model scores*;
   the full probability vector is shown; near-tied top-2 predictions raise a
   low-margin warning; the UI never claims calibrated confidence or a
   diagnosis.
5. **Graceful external services.** Missing API keys produce configuration
   messages, not tracebacks. The default database is SQLite (auto-created),
   so the homepage and classifiers never require a personal MySQL server.
6. **Legacy preservation.** The original single-file app and its standalone
   script are kept verbatim under `docs/legacy_*` with a header note; the
   smoke test blocks reintroducing hardcoded secrets outside those
   quarantined files.

## Data flow of a prediction

1. Upload arrives → size/format validated (`MAX_UPLOAD_MB`, allowlist).
2. `load_image_from_bytes` → decode, EXIF transpose, convert to RGB.
3. `to_model_input` → bilinear resize to the model's manifest size, ÷255,
   batch to `(1, H, W, 3)`.
4. `predict_image` → model forward pass, NaN/shape checks, softmax
   normalization, ranking, low-margin check.
5. UI renders class probabilities + explicit uncalibrated-score framing.

## What is deliberately NOT here

- No probability calibration (temperature/Platt/isotonic) — none of the
  shipped models was calibrated, and adding it without validation data would
  fabricate confidence. See `docs/known_limitations.md`.
- No OOD detector / selective prediction layer. Low-margin warnings are a
  heuristic stopgap, clearly labeled as such.
- No claim that these models match the PMLR paper's models — see
  `docs/research_reproducibility.md`.
