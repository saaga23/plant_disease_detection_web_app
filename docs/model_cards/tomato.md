# Model card — Tomato Disease Classifier

- **Artifact**: `CNN_model_tomatoes/` (Keras 2-era TF SavedModel; directory SHA-256s pinned in `models/model_manifest.json`)
- **Architecture**: sequential CNN (Conv2D/MaxPooling stack, ~0.5M parameters) — **not** MobileNetV2
- **Input**: 256×256×3, float32, resized bilinearly, rescaled by 1/255
- **Output**: 10 class logits (softmax normalized at inference)
- **Classes** (ordering inherited from the legacy app; **unverified** — no label artifact exists):
  Bacterial spot, Early blight, Late blight, Leaf mold, Septoria leaf spot,
  Spider mites (two-spotted), Target spot, Tomato yellow leaf curl virus,
  Tomato mosaic virus, Healthy
- **Training provenance**: not recorded in this repository. Class set is consistent with the
  PlantVillage tomato dataset; training code, dataset, and splits are absent.
- **Framework**: trained with a Keras 2-era TensorFlow build; loads via
  `tf.keras.models.load_model` (TF ≤ 2.15) or `TFSMLayer` (Keras 3).
- **Relation to the PMLR paper**: none demonstrated — this is not the paper's MobileNetV2 model
  (`docs/research_reproducibility.md`).
- **Calibration**: uncalibrated. Scores are softmax values, not calibrated probabilities.
- **Known limitations**: unverified class ordering; no recorded accuracy on any external
  dataset; likely degraded accuracy on real field photographs (lighting, dust, backgrounds)
  relative to curated leaf scans.
