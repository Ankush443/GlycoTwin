# Data provenance

**Status:** Implemented synthetic-data pipeline. The committed development
sample is generated locally and contains no real people or measurements.

## Selected source

The prototype uses data produced locally by the versioned
`glycotwin.data.generate` generator. It creates related records under the same
generated `patient_id`; it does not represent or reconstruct real people.

The generated data has these tables:

- `patients.csv` — synthetic demographics and baseline history.
- `clinical_observations.csv` — dated synthetic clinical observations.
- `wearable_daily.csv` — dated synthetic wearable-like daily measurements.
- `prediction_index.csv` — prediction timestamps and a separately dated,
  generated future HbA1c target.

## Implemented target construction policy

The future HbA1c target is created by the generator, not observed in a
laboratory. With all quantities generated at or before `prediction_at`, it is:

```text
clip(
  latest_hba1c
  + 0.012 × (latest_bmi − 30)
  + 0.0035 × (latest_fasting_glucose − 130)
  + 0.000025 × (7000 − 14-day mean steps)
  + 0.003 × (120 − 14-day mean active minutes)
  + 0.012 × (14-day mean resting heart rate − 72)
  + 0.05 × (7 − 14-day mean sleep duration)
  + 0.006 × (80 − 14-day mean sleep consistency)
  + Normal(0, 0.18),
  4.5, 13.0
)
```

The generated target is dated 90 days after the feature cut-off. The formula
is a deterministic synthetic-data mechanism plus seeded noise; its coefficients
do **not** represent causal or clinical effects. Generated target values are
labelled `synthetic_future_hba1c_percent` in every dataset and must remain
labelled synthetic in downstream responses.

The default committed sample uses 40 synthetic patients, seed `20261012`, a
prediction date of `2026-10-01`, and a 14-day wearable window. The exact run is
recorded in `docs/experiment_log.md` and `data/sample/metadata.json`.

No deterioration-event label is planned. A threshold applied to a generated
HbA1c target may be used only as a transparent display or alert rule if needed;
it is not a validated outcome label or risk probability.

## Provenance constraints

- Do not add real patient data, direct identifiers, restricted data, or secrets
  to the repository.
- Do not merge clinical and wearable data from independent sources as though
  they are patient linked.
- Keep raw generator output local unless a small safe sample is intentionally
  committed for tests; document the generator version and seed for every
  committed sample.
- The pipeline validates required columns, missingness, duplicate patient/date
  rows, date types, patient linkage, prediction/target ordering, and documented
  synthetic ranges before generating features.
- Processed output uses the latest clinical record at or before prediction time
  and exactly 14 calendar days ending on that date. Future wearable records are
  not selected. Train/validation/test splits are disjoint by `patient_id`.

## Unselected reference

Synthea was reviewed as a possible synthetic clinical reference because it
exports patient-keyed clinical tables and observations. It is not part of the
initial GlycoTwin dataset because a linked wearable-like feed was not verified.
See [scope.md](scope.md) for the inspection decision and source links.
