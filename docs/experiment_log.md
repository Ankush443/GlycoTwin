# Experiment log

## 12 October 2026 — synthetic data pipeline v0.1.0

- **Status:** Data generation and feature preparation only; no model trained.
- **Generator:** `glycotwin.data.generate`, version `0.1.0`.
- **Committed sample:** 40 synthetic patients; seed `20261012`; prediction date
  `2026-10-01`; 14 wearable days; synthetic target horizon 90 days.
- **Source tables:** `patients.csv`, `clinical_observations.csv`,
  `wearable_daily.csv`, and `prediction_index.csv`.
- **Features:** latest clinical observation at or before prediction time plus
  means of the preceding 14 calendar days of wearable-like records.
- **Split policy:** deterministic patient-level 70%/15%/15% train/validation/
  test split; no patient may appear in more than one split.
- **Metrics:** Not applicable. No model or clinical-performance claim exists.

## 19 October 2026 — synthetic regression benchmark v0.1.0

- **Status:** Completed Phase 3 synthetic-only training run.
- **Model family:** `StandardScaler` + `Ridge(alpha=1.0)`.
- **Candidates:** Clinical-only baseline and clinical-plus-wearable pipeline,
  both fitted on 28 training patients only.
- **Selection:** Lowest validation MAE; selected clinical-plus-wearable Ridge.
- **Validation result:** MAE `0.2057683599`, RMSE `0.2457621099` on 6 patients.
- **Held-out test result:** MAE `0.1421711686`, RMSE `0.1591112409` on 6 patients.
- **Artifacts:** `models/synthetic_hba1c_regression.joblib` and
  `models/synthetic_hba1c_metrics.json` are reproducible local outputs.
- **Limitation:** These values measure recovery of a project-generated target
  from a small synthetic cohort. They are not clinical-performance evidence.

## 19 October 2026 — inference API v0.1.0

- **Status:** Completed Phase 4 local FastAPI implementation.
- **Endpoints:** Health, synthetic patient list/detail, saved-pipeline
  prediction, saved-pipeline scenario comparison, and synthetic demo alerts.
- **Inference:** `/predict` and `/simulate` load the saved preprocessing/model
  artifact; neither endpoint substitutes constants for model output.
- **Unavailable behaviour:** Inference returns HTTP 503 when the artifact is
  absent; unknown patient IDs return HTTP 404; an empty scenario returns HTTP
  422.
- **Risk boundary:** No deterioration classifier or probability is returned.
- **Alert boundary:** Alerts use a documented configurable synthetic historical
  HbA1c-like threshold and are labelled non-clinically approved.

## 20 October 2026 — clinician dashboard and prediction explanations

- **Status:** Completed Phase 5. React/TypeScript dashboard consumes the
  Phase 4 API; backend gained CORS for the local frontend origin.
- **Explanations:** `/predict` now returns an `explanation` object with exact
  linear contributions (`coefficient × scaled_value`, plus intercept) for the
  saved Ridge pipeline. Verified by test: contributions + intercept reconstruct
  the estimate to machine precision.
- **SHAP decision:** Not added. For the linear `StandardScaler` + `Ridge`
  pipeline, exact coefficients already provide exact attributions; SHAP's
  `LinearExplainer` would report the same values while adding an unnecessary
  dependency. Rationale recorded in `docs/model_card.md`.
- **Frontend:** `frontend/` (Vite, React 19, TypeScript, Tailwind 4, Recharts)
  with patient selector, clinical summary + last lab date, wearable trend
  charts, prediction/explanation panel, what-if simulator, alert panel, and
  loading/empty/error states. Previous results are cleared before each request
  so failures never display stale values.
- **Tests:** 15 passing (data, training, API incl. CORS and explanation
  exactness). Frontend verified by `tsc` typecheck plus live manual HTTP of the
  same request sequence the UI performs.
