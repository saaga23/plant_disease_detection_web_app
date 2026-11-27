# Model card — Pepper Disease Classifier

- **Artifact**: `pepper-model.h5` (Keras H5; SHA-256 `43ee4c24…b53aa15a`; distributed via **Git LFS** — run `git lfs pull`)
- **Architecture**: 4×(Conv2D+MaxPooling)+Dense CNN, 5,239,362 parameters — **not** MobileNetV2
- **Input**: 128×128×3, float32, bilinear resize, ÷255
- **Output**: 2 class logits
- **Classes** (unverified ordering): Bacterial spot, Healthy
- **Training provenance**: not recorded here.
- **Known limitations**: the two-class set is inconsistent with the PlantVillage pepper
  collection (10 diseases + background); provenance unknown. Uncalibrated scores; unverified
  class ordering; no external evaluation on record.
