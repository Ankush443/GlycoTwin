# GlycoTwin

GlycoTwin is a local, research/demo proof of concept for presenting synthetic
clinical and wearable-like data for Type 2 diabetes glycaemic monitoring.

> This prototype is not a medical device, diagnosis, laboratory result, or
> treatment recommendation. It uses synthetic data only. Every model output is
> an explicitly labelled synthetic, model-estimated value and must be reviewed
> alongside laboratory testing and clinician judgement.

## Current status

Phase 5 clinician-facing dashboard is implemented and consumes the local API.
The repository includes a small, fully synthetic sample and a reproducible
locally generated model artifact. Phases 1 through 4 (scope/data audit, data
pipeline, model training, and inference API) are complete.

The first planned model is a synthetic HbA1c regression benchmark. A
deterioration-risk classifier is explicitly out of scope until a valid,
patient-linked future-event label exists.

## Repository layout

```text
data/             Synthetic-data locations; raw and processed outputs are ignored
docs/             Scope, provenance, schema, and architecture documentation
models/           Generated model artifacts (ignored)
src/glycotwin/    Python package for data, features, training, and inference
frontend/         React/TypeScript clinician dashboard (Vite + Tailwind + Recharts)
tests/            Automated tests
```

## Setup

Use Python 3.11 through 3.14. In this environment, use `python3`; do not use
the unrelated system `pip` executable.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Checks

```bash
python -m pytest
```

The test suite verifies package import, deterministic generation, validation,
feature-window leakage protection, patient-level splitting, CSV preparation,
model training, exact linear explanation contributions, and API behaviour
including CORS.

## Generate and prepare synthetic data

The committed sample is generated from a fixed seed. Regenerate it and create
local processed splits with:

```bash
PYTHONPATH=src python -m glycotwin.data.generate \
  --output-dir data/sample --patient-count 40 --seed 20261012
PYTHONPATH=src python -m glycotwin.data.prepare \
  --input-dir data/sample --output-dir data/processed --seed 20261012
```

The preparer validates schemas, missing values, duplicate patient/date rows,
date fields, patient linkage, target ordering, and documented plausible ranges.
It selects the latest clinical observation at or before prediction time, exactly
14 wearable days ending at prediction time, and then writes patient-disjoint
70%/15%/15% train/validation/test splits. Generated targets and processed data
are synthetic only; the target is not a laboratory result.

## Train the synthetic benchmark

```bash
PYTHONPATH=src python -m glycotwin.training.train \
  --processed-dir data/processed --model-dir models
```

This compares clinical-only and clinical-plus-wearable Ridge-regression
pipelines, selects the lower validation-MAE candidate, evaluates it on the
patient-disjoint held-out test split, and saves an artifact containing both the
scaler and model. Results are synthetic-only and do not establish clinical
accuracy. See the [model card](docs/model_card.md) for measured results and
limitations.

## Run the local API

After training the artifact:

```bash
PYTHONPATH=src uvicorn glycotwin.api.main:app --reload
```

Use `http://127.0.0.1:8000/docs` to inspect and call the synthetic-only API.
It provides health, patient browsing, real-pipeline prediction (with exact
linear feature contributions), exploratory simulation, and a configurable
non-clinical follow-up rule. See the [API contract](docs/api.md) for
request/response details.

## Run the dashboard

Start the API (previous section), then in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api` to the backend on
port 8000. The dashboard shows synthetic patient selection, historical
clinical/laboratory summaries with the last lab date, wearable-like trend
charts, model estimates with the exact linear explanation, a what-if scenario
simulator, and the configurable follow-up alert panel. Every view states that
the system is a synthetic research/demo prototype, not a diagnosis.

For a production-style bundle, run `npm run build` inside `frontend/` and
serve `frontend/dist/` behind the same `/api` proxy.

Troubleshooting: recent npm versions restrict install scripts. If `npm run
build` fails with an esbuild error, approve the skipped script once with
`npm install-scripts approve esbuild` (inside `frontend/`) and re-run.

## Documentation

- [Scope and feasibility](docs/scope.md)
- [Data provenance](docs/data_provenance.md)
- [Data dictionary](docs/data_dictionary.md)
- [Architecture](docs/architecture.md)
- [Model card](docs/model_card.md)
- [API contract](docs/api.md)
- [Experiment log](docs/experiment_log.md)
- [Current project status](PROJECT_STATUS.md)

## Licence

This repository is licensed under the [MIT License](LICENSE).