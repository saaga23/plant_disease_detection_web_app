# Model card — Pest Detection

- **Artifact**: `pest_detection_model2.h5` (Keras H5; SHA-256 `d64f012f…b89c9b7ff4a8e4`; **Git LFS**)
- **Architecture**: 4×(Conv2D+MaxPooling)+Dense CNN, 5,242,189 parameters — **not** MobileNetV2
- **Input**: 128×128×3, float32, bilinear resize, ÷255
- **Output**: 13 class logits
- **Classes** (unverified ordering): aphids, armyworm, beetle, bollworm, grasshopper, mites,
  mosquito, slug, snail, whitefly, fruit & vegetable disease complex, healthy, unknown
- **Training provenance**: not recorded here.
- **Known limitations**: unverified class list ordering; a generic "unknown" class with
  undefined semantics; uncalibrated scores; no external evaluation on record.
