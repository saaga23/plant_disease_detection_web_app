# Deployment

## Local installation (verified commands)

```bash
git clone https://github.com/saaga23/plant_disease_detection_web_app
cd plant_disease_detection_web_app
git lfs pull                        # fetch the two LFS model files (~126 MB)
python -m venv .venv
# Windows:  .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Tested combination: Python 3.12.3, TensorFlow 2.21, Streamlit 1.67 (see
"Verified environments" below). Any Python 3.9-3.13 with TF >= 2.15 should
work; the loader supports both Keras 2 and Keras 3.

## Docker

```bash
docker build -t plant-app .
docker run -p 8501:8501 plant-app
```

(LFS files are included in the build context because they are smudged in a
normal checkout; the Dockerfile copies the working tree.)

## Environment variables

Required: **none**. The app runs with zero configuration: SQLite demo
database, and optional-service pages show configuration messages.

| Variable | Default | Required when |
|---|---|---|
| `DB_MODE` | `sqlite` | set to `mysql` for a real MySQL server |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | - | `DB_MODE=mysql` |
| `OPENAI_API_KEY` | - | Question Answering page |
| `SERPAPI_API_KEY` | - | Google Search page |
| `MAX_UPLOAD_MB` | `10` | to change the upload limit |

Put real values in a local `.env` file (never commit it) or export them in
the environment. For MySQL, apply `scripts/schema_mysql.sql` once.

## Cloud deployment notes

- Streamlit Community Cloud can host this app; **LFS-hosted .h5 artifacts
  must be reachable** (Community Cloud runs `git lfs pull` during setup).
- Any container host (Fly.io, Railway, Cloud Run) works with the provided
  Dockerfile; allocate >= 2 GB RAM for TensorFlow.
- Do not set real API keys in the container image; inject them as runtime
  secrets.

## Verified environments

| Environment | Result |
|---|---|
| Windows 10/11, Python 3.12.3, TF 2.21.0, Streamlit 1.67.0 | 33/33 tests pass; all 4 models load and infer; app boots (see README) |
