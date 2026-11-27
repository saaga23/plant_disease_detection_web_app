# Plant Disease Detection Web App

An educational Streamlit application for detecting crop diseases and pests
from photographs, with practical farming guides, a crop-record book, and
optional weather/search/answering services. Built for the African smallholder
context; developed as a student project and maintained as a public portfolio
artifact.

**Important honesty note:** the four image classifiers deployed here are
small custom CNNs and are **not** the MobileNetV2 models reported in the
published PMLR paper (see [Research context](#research-context)). Predictions
are shown as **uncalibrated model scores**, never as a diagnosis.

---

## What problem does this address?

Smallholder farmers often cannot identify crop diseases or pests quickly.
This app demonstrates a self-service tool where a farmer photographs a leaf
or insect and receives a class prediction plus practical guidance pages
(planting, rotation, livestock vaccination) in one place.

## What is in the repository

| Path | Purpose |
|---|---|
| `app.py` | Streamlit entry point (all 14 legacy pages preserved) |
| `src/plant_app/` | Application package: config, model registry, inference, services, database |
| `models/` | Four model artifacts + `model_manifest.json` (SHA-256 verified) |
| `assets/` | UI images |
| `scripts/` | `validate_models.py`, `evaluate_models.py`, `run_tests.py`, SQL schemas |
| `tests/` | Unit, integration, and smoke tests (33 tests) |
| `docs/` | Architecture, model cards, data provenance, evaluation protocol, deployment, known limitations, security remediation, research reproducibility |
| `docs/legacy_*` | The original sources quarantined for audit integrity; the rotated MySQL credential value was redacted from them (commit 205a10c) |
| `.github/workflows/ci.yml` | CI: lint, model validation, tests, secret scan |

## Quick start

```bash
git clone https://github.com/saaga23/plant_disease_detection_web_app
cd plant_disease_detection_web_app
git lfs pull                       # two ~63 MB model files are Git LFS artifacts
python -m venv .venv
.venv\Scripts\activate             # Windows; source .venv/bin/activate on Linux
pip install -r requirements.txt
streamlit run app.py
```

No configuration is required to run: the database defaults to a zero-setup
SQLite demo, and external-service pages degrade to clear configuration
messages when API keys are absent.

Optional configuration (copy `.env.example` to `.env`):

- `DB_MODE=mysql` + `DB_*` variables for a real MySQL server (apply
  `scripts/schema_mysql.sql`)
- `OPENAI_API_KEY` for the Question Answering page
- `SERPAPI_API_KEY` for the Google Search page

## Features (all tested; see test table in docs/deployment.md)

1. **Home** - overview and honest capability statement.
2. **Getting Started** - step-by-step farming guidance.
3. **Tomato Disease Classifier** - 10-class tomato leaf classification.
4. **Pepper Disease Classifier** - 2-class pepper leaf classification.
5. **Potato Disease Classifier** - 3-class potato leaf classification.
6. **Pest Detection** - 13-class insect classification.
7. **Crop Rotation Advisor** - season/soil lookup table.
8. **Farm Animal Vaccination Guide** - per-animal vaccine reference.
9. **Question Answering** - optional, OpenAI-backed, graceful when unconfigured.
10. **Record Input** - crop record entry (SQLite demo or MySQL).
11. **Retrieve Crop Data for Analysis** - table + yield distribution chart.
12. **Weather** - Open-Meteo current conditions + 3-day outlook (no key needed).
13. **Google Search** - optional, SerpAPI-backed.
14. **Feedback** - guidance form (directs durable feedback to GitHub issues).

Every classifier page: validates file type and size, handles EXIF
orientation, converts to RGB, resizes per the manifest, reports the **full
probability vector**, warns on near-tied predictions, and labels scores as
uncalibrated.

## Verification

```bash
python scripts/validate_models.py        # checksums + load + smoke inference
python -m pytest tests/ -q               # full test suite
python scripts/run_tests.py              # both, with pass/fail summary
```

Latest verified run (2026-11-27, Windows 11, Python 3.12.3, TensorFlow
2.21.0, Streamlit 1.67.0):

- `scripts/validate_models.py`: **PASS** - all four artifacts checksum-match
  the manifest, load, and return finite per-class scores.
- `pytest tests/unit tests/smoke`: **24 passed**.
- `pytest tests/integration`: **9 passed** (real inference on all four models).
- CI (`.github/workflows/ci.yml`): lint, model validation, unit/smoke,
  integration, and a secret scan on Python 3.11 and 3.12.

## Model artifacts

| Key | Artifact | Input | Classes | Note |
|---|---|---|---|---|
| tomato | `CNN_model_tomatoes/` (SavedModel) | 256x256x3 | 10 | custom CNN, not MobileNetV2 |
| potato | `potatoed_disease_classifier/` (SavedModel) | 256x256x3 | 3 | custom CNN, not MobileNetV2 |
| pepper | `pepper-model.h5` (LFS) | 128x128x3 | 2 | custom CNN |
| pest | `pest_detection_model2.h5` (LFS) | 128x128x3 | 13 | custom CNN |

Full details, provenance status, and per-model limitations:
[docs/model_cards/](docs/model_cards). Class-name ordering is marked
**unverified** in the manifest because no label artifact exists; the UI says
so wherever relevant.

## Research context

The maintainer published: *Bridging the Domain Gap: Transfer Learning and
Aggressive Fine-Tuning for Robust Plant Disease Detection in Low-Resource
African Agriculture*, PMLR 319:16-25 (IndabaX Nigeria 2026),
<https://proceedings.mlr.press/v319/abraham26a.html>.

**This app does not deploy those paper models.** The relationship between
the paper's claims and everything in this repository is documented precisely
in [docs/research_reproducibility.md](docs/research_reproducibility.md):
what is reproducible, what is supported by surviving artifacts, and what
would require the (currently absent) training code and field dataset.

## Known limitations

See [docs/known_limitations.md](docs/known_limitations.md). Headlines: the
deployed models are not the paper's models; class ordering is unverified;
scores are uncalibrated; no accuracy numbers are claimed for the deployed
models; the guides' content predates this audit and is labeled
educational-only.

## Security

A hardcoded database credential present in earlier versions was removed;
credentials are now environment-only. Full disclosure and rotation
instructions: [docs/security_remediation.md](docs/security_remediation.md).
The exposed credential was rotated on 2026-11-27 and verified no longer to
authenticate; local root access is pending recovery (see the report).

## License

Code: MIT ([LICENSE](LICENSE)). See [docs/data_provenance.md](docs/data_provenance.md)
for data/asset provenance notes.

## Contact and contribution

Maintainer: Sunday Aspita Abraham - open a GitHub issue for bugs,
reproduction failures, or documentation gaps. PRs are welcome, especially
for: class-ordering verification (training the manifest labels), calibrated
evaluation, and field-robustness tests. Please keep `docs/legacy_*`
untouched (audit record).

## Citation

```bibtex
@misc{abraham2026plantapp,
  title  = {Plant Disease Detection Web App},
  author = {Abraham, Sunday Aspita},
  year   = {2026},
  url    = {https://github.com/saaga23/plant_disease_detection_web_app},
  note   = {Educational Streamlit application; not the PMLR v319 paper's models}
}
```
