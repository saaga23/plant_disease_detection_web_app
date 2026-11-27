# Model card — Potato Disease Classifier

- **Artifact**: `potatoed_disease_classifier/` (Keras 2-era TF SavedModel; SHA-256s pinned)
- **Architecture**: sequential CNN (~0.5M parameters) — **not** MobileNetV2
- **Input**: 256×256×3, float32, bilinear resize, ÷255
- **Output**: 3 class logits
- **Classes** (unverified ordering): Early blight, Late blight, Healthy
- **Training provenance**: not recorded here; class set matches PlantVillage potato.
- **Relation to the PMLR paper**: none demonstrated (the paper's cassava/tomato field models
  are absent from this repository).
- **Calibration**: uncalibrated.
- **Known limitations**: unverified class ordering; no external evaluation on record.
