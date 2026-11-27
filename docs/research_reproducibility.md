# Research reproducibility: the PMLR paper and this web app

This document states precisely what is and is not traceable between the
published paper and the code/models in this repository. It is deliberately
blunt: a reviewer should be able to reproduce everything reproducible today
and know exactly which artifacts do not exist.

## 1. What the paper reports

Abraham, S. A., Adeniyi, A., Mughal, Q. U. A., & Olanloye, O. (2026).
*Bridging the Domain Gap: Transfer Learning and Aggressive Fine-Tuning for
Robust Plant Disease Detection in Low-Resource African Agriculture.*
Proceedings of IndabaX Nigeria 2026, PMLR 319:16–25.
<https://proceedings.mlr.press/v319/abraham26a.html>

Claims relevant to this audit:

- 1,742 field photographs collected in Ibadan and surrounding districts of
  Oyo and Osun States, Nigeria.
- ImageNet-pretrained **MobileNetV2** backbone.
- A two-step training protocol with an auto-fallback safeguard.
- Tomato accuracy improved from 34.69% to 97.96%; cassava from 52.42% to
  98.39%.

## 2. What this repository contains

| Artifact | Status |
|---|---|
| Four deployed models (tomato SavedModel, potato SavedModel, pepper H5, pest H5) | Present, checksum-verified, loadable (see `models/model_manifest.json`) |
| Architecture of all four models | Small custom sequential CNNs (~0.5–5.2M parameters) — **none is MobileNetV2** |
| Training code for the deployed models | **Absent** |
| Training/evaluation code for the paper's MobileNetV2 models | **Absent** |
| Field dataset (1,742 photographs) | **Absent** |
| Dataset splits, seeds, training configs | **Absent** |
| Evaluation outputs behind the paper's numbers | **Absent** |
| `docs/report/final_year_report.pdf` | A 96-page project report describing CNN work on the **PlantVillage** dataset; it contains none of the paper's headline numbers and is not the paper's record. Kept for provenance. |

## 3. Conclusion on the paper↔app relationship

**The models deployed in this web app are not the models evaluated in the
PMLR paper.** Evidence: (a) the deployed models are small custom CNNs whose
layer types were inspected directly (Conv2D/MaxPool stacks, not MobileNetV2
inverted residuals); (b) the deployed models' class sets match
PlantVillage-style leaf datasets, not the paper's field classes (e.g., the
paper reports cassava, which has no deployed model); (c) no artifact in the
repository (or its Git history — it contains only two commits) links the
deployed checkpoints to the paper's training pipeline.

The CV-relevant implication: this repository **must not** be described as
"the code/models behind the PMLR paper". It is an application that deploys
different, earlier-stage models.

## 4. Reproducibility classification

1. **Directly reproducible today** — model artifact integrity (SHA-256
   manifest), model loading, input/output shapes, smoke inference:
   `python scripts/validate_models.py`.
2. **Supported by surviving artifacts** — the four deployed models' behavior
   on user images (runtime inference). Their accuracy on any external dataset
   was never recorded in this repository, so no accuracy claim can be made
   for them.
3. **Requiring unavailable artifacts** — the paper's results (MobileNetV2
   numbers, field-dataset accuracy, ablations). The training code, dataset,
   splits, and evaluation logs are not in any public repository, so these
   numbers cannot be reproduced from here.
4. **Requiring new experiments** — any claim that the deployed web models
   perform well under field conditions (dust, glare, background clutter), or
   that they generalize beyond their (unverified) training distribution.

## 5. What a reviewer can verify, in commands

```bash
git clone https://github.com/saaga23/plant_disease_detection_web_app
cd plant_disease_detection_web_app
pip install -r requirements.txt          # TensorFlow >= 2.15, Python 3.9–3.13
git lfs pull                             # fetch the two LFS model files
python scripts/validate_models.py        # checksum + load + smoke inference
python -m pytest tests/ -q               # full suite (skip model tests offline)
```

Architecture inspection (no trust required — prints real layer types):

```python
import tensorflow as tf
m = tf.keras.models.load_model("pepper-model.h5", compile=False)
print(m.summary())          # Conv2D/MaxPooling stack, not MobileNetV2
```

## 6. Recommendation

If the paper's training code, the field dataset, and evaluation logs still
exist privately, deposit them (with the authors' consent and a license) in a
`research/` directory of this repository or a companion repository, then
update this document. If they no longer exist, leave this document as the
authoritative statement: the paper's numbers remain published and
unverifiable from public artifacts — which is disclosed, not hidden.
