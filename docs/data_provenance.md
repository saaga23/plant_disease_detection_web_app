# Data provenance

## Deployed models' training data (unknown, disclosed)

No training dataset, split manifest, or training log exists in this
repository or its Git history (two commits, initial upload only). The class
sets strongly suggest PlantVillage-derived training data for the tomato and
potato classifiers, but this is inference from class names, not a record.
Treat every deployed model's training provenance as UNKNOWN.

## The PMLR paper's field dataset (not present)

The paper reports 1,742 field photographs from Oyo and Osun States
(Ibadan area). Those images, their splits, and the evaluation outputs are
not in any public repository we control. `docs/research_reproducibility.md`
records this in detail.

## The bundled report PDF

`docs/report/final_year_report.pdf` is a 96-page academic project report
kept for historical provenance. It describes PlantVillage-based CNN work and
does not contain the paper's numbers. Do not cite it as the paper's record.

## Web pages and guides

- Weather data: Open-Meteo (https://open-meteo.com/), free for non-commercial
  use, CC BY 4.0 attribution required. No API key.
- Crop-rotation and vaccination tables: inherited from the legacy app, which
  attributed them to unnamed "local agricultural experts / veterinary
  professionals". No citable record exists. The UI labels them as
  educational references requiring local professional confirmation.
- No user-uploaded images are stored by the application: inference happens
  in memory and nothing is persisted to disk.
- The demonstration SQLite database is created locally on first use of a
  database page; it contains only what a user of that instance enters.
