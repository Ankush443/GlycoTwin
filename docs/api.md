# API contract

**Status:** Phases 4–5 implementation (submission stage). This local API
serves synthetic records and the saved synthetic-only regression pipeline. It
is not for clinical use.

The dashboard on `http://localhost:5173` reaches this API through a
same-origin `/api` dev proxy (see `frontend/vite.config.ts`); the API also
allows CORS for the local frontend origin (`http://localhost:5173` and
`http://127.0.0.1:5173`) as a fallback so direct browser calls work too.
Other origins are refused.

## Run locally

Generate/prepare data and train the artifact first, then run:

```bash
PYTHONPATH=src .venv/bin/uvicorn glycotwin.api.main:app --reload
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Reports synthetic data and model availability. |
| `GET /patients` | Lists synthetic patient summaries. |
| `GET /patients/{patient_id}` | Returns synthetic historical clinical and daily wearable-like observations. |
| `POST /predict` | Runs the saved pipeline for one patient. |
| `POST /simulate` | Re-runs the saved pipeline after supported scenario changes. |
| `GET /alerts` | Returns records matching a configurable, non-clinical synthetic demo rule. |

## Response conventions

Every response follows the project's contract principles:

- **Labelling.** Observation rows carry `data_kind` values
  (`synthetic_historical_observation`, `synthetic_wearable_like_observation`)
  and predictions carry an `output_kind` such as
  `synthetic_model_estimated_future_hba1c_percent` or
  `synthetic_model_scenario_estimated_future_hba1c_percent`.
- **Warnings.** Every endpoint returns a `warnings` array; at minimum it
  contains the synthetic-demo notice. Scenario responses add the
  "exploratory, not a guaranteed treatment outcome" warning.
- **Uncertainty.** `POST /predict` returns `uncertainty: null` — the model
  does not quantify it, and the API never invents an interval.
- **Risk boundary.** `deterioration_risk_available: false` appears on health,
  prediction, and simulation responses. No risk probability is ever produced.
- **Model metadata.** Prediction and simulation responses echo
  `model_version` (and prediction echoes `model_name` and `feature_columns`)
  so consumers can see which artifact produced the number.

## Error responses

| Status | Condition | Example `detail` |
| --- | --- | --- |
| `404` | Unknown `patient_id` on `/patients/{id}` or `/predict` | `Unknown synthetic patient_id: NOPE` |
| `422` | Malformed body, out-of-range field, or `/simulate` with no adjustments | structured Pydantic error list; `At least one scenario adjustment is required` |
| `503` | Model artifact missing or a required feature is absent from the patient record | `Model unavailable. Train the synthetic regression pipeline before requesting inference.` |

Browsing endpoints and `/health` stay available without the model artifact;
`/health` then reports `model_available: false`. The API never substitutes
demo constants for a failed inference.

## Prediction request and response

```json
{"patient_id": "SYN-0001"}
```

`POST /predict` returns the model-estimated synthetic 90-day HbA1c-like value,
the saved model version/name, feature list, and a synthetic-data warning. It
returns `deterioration_risk_available: false`; this project does not implement a
deterioration-risk classifier or probability.

The response also includes an `explanation` object. For the current linear
pipeline (StandardScaler + Ridge) it reports exact per-feature contributions
computed as `coefficient × scaled_feature_value`, sorted by absolute impact,
plus the model intercept. The contributions and intercept reconstruct the
estimate exactly (verified by
`test_prediction_explanation_contributions_sum_to_the_estimate`). The
explanation describes the synthetic model's arithmetic, not clinical
causation. If a future selected model is not linear, `explanation` reports
`available: false` with a reason.

## Scenario request and response

`POST /simulate` requires `patient_id` and at least one of these fields:

- `steps_14d_mean`
- `active_minutes_14d_mean`
- `resting_heart_rate_14d_mean`
- `sleep_duration_14d_mean`
- `sleep_consistency_14d_mean`

Each is range-validated (for example steps `0–100000`, resting heart rate
`20–240`). Example:

```json
{"patient_id": "SYN-0001", "steps_14d_mean": 7000}
```

The response identifies each observed synthetic feature value and scenario
value (in `modifications`), then reports the baseline estimate, the scenario
estimate, and `scenario_minus_baseline`. It explicitly states that the result
is exploratory and not a guaranteed treatment outcome.

## Alert rule

`GET /alerts` uses the latest **synthetic historical** HbA1c-like value and a
configurable default threshold of `8.0` percent. Its response labels the rule
`configurable_demo_rule_not_clinically_approved` and asks users only to
consider clinical/laboratory review. It is not a diagnosis, probability, or
automated booking workflow.
