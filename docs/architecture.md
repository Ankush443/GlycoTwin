# Architecture

**Status:** Phases 1–5 complete (submission stage). The data pipeline,
synthetic model, FastAPI inference service, and React/TypeScript clinician
dashboard are all implemented and tested.

**Submission deliverable:** a printable version of this diagram is
[Architecture_Diagram.pdf](Architecture_Diagram.pdf), generated from
[`docs/latex/Architecture_Diagram.tex`](latex/Architecture_Diagram.tex)
(TikZ). The PDF is the canonical submission artifact; the text diagram below
tracks the same structure for reviewers reading in-browser.

```text
Versioned synthetic-data generator (src/glycotwin/data/generate.py)
    ├─ patients.csv
    ├─ clinical_observations.csv
    ├─ wearable_daily.csv
    └─ prediction_index.csv (90-day future synthetic target)
                │
                ▼
Validation + leakage-safe features (src/glycotwin/data/)
    │  schema, ranges, linkage, ordering checks
    │  latest clinical ≤ cut-off; exactly 14 wearable days
    │  patient-disjoint 70/15/15 splits (src/glycotwin/data/prepare.py)
                │
                ▼
Synthetic Ridge benchmark (src/glycotwin/training/train.py)
    │  clinical-only vs clinical+wearable candidates
    │  selection by validation MAE; held-out test evaluation
    │  saved artifact: scaler + model + metadata (models/, git-ignored)
                │
                ▼
FastAPI service (src/glycotwin/api/) ─────────── React dashboard (frontend/)
    │  GET  /health               │               Vite dev server :5173
    │  GET  /patients             │               /api proxy → :8000
    │  GET  /patients/{id}        │               ├ patient selector + health badge
    │  POST /predict              │               ├ clinical summary + last lab date
    │       └ exact linear        │               ├ wearable trend charts (14 d)
    │         contributions       │               ├ prediction + contribution chart
    │  POST /simulate             │               ├ what-if simulator
    │       └ baseline vs         │               └ follow-up alert panel
    │         scenario            │
    │  GET  /alerts               │
    └─ CORS restricted to :5173 ──┘
```

## Component responsibilities

| Component | Location | Responsibility |
| --- | --- | --- |
| Data generation | `src/glycotwin/data/` | Deterministic synthetic cohort; validation; leakage-safe features; patient-disjoint splits |
| Training | `src/glycotwin/training/` | Two Ridge candidates, validation-MAE selection, held-out evaluation, saved artifact |
| API | `src/glycotwin/api/` | Serves synthetic records and real-pipeline inference with explicit errors |
| Dashboard | `frontend/` | Clinician-facing views over the API; never fabricates or caches stale outputs |
| Tests | `tests/` | 15 pytest tests: data, training, API (incl. CORS and explanation exactness) |

## Data-flow principles

- The frontend runs on Vite (`frontend/`, port 5173) and reaches the API
  through a same-origin `/api` proxy during development; the API additionally
  enables CORS for the local frontend origin as a fallback. Requests are only
  issued when the user asks (run inference, run scenario, check alerts), so the
  UI never displays fabricated or auto-generated model outputs.
- The pipeline preserves `patient_id` and timestamps. The model service
  returns an explicitly unavailable state for any output it cannot produce; it
  does not substitute constants. The dashboard distinguishes observed synthetic
  records, historical values, model estimates, and scenario values, and clears
  previous results before each request so a failed call never shows stale
  numbers.
- No external database, cloud service, wearable hardware integration, or
  booking system is part of this design.
