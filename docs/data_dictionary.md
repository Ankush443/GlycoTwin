# Data dictionary

**Status:** Implemented synthetic source schema and feature contract. The
values are generated for a research/demo pipeline and are not clinical data.

## `patients.csv`

| Field | Type | Unit / values | Definition |
| --- | --- | --- | --- |
| `patient_id` | string | generated identifier | Synthetic patient key used in every table. |
| `birth_year` | integer | year | Generated year of birth; no real-person identifier. |
| `sex_at_birth` | string | documented allowed values | Generated demographic attribute. |
| `diabetes_history_years` | number | years | Generated duration-like history feature at prediction time. |

## `clinical_observations.csv`

| Field | Type | Unit / values | Definition |
| --- | --- | --- | --- |
| `patient_id` | string | generated identifier | Links to `patients.csv`. |
| `observed_at` | ISO 8601 date | date | Synthetic observation date. |
| `hba1c_percent` | number | percent | Synthetic historical HbA1c-like value. |
| `fasting_glucose_mg_dl` | number | mg/dL | Synthetic fasting-glucose-like value. |
| `bmi_kg_m2` | number | kg/m² | Synthetic body-mass-index value. |

## `wearable_daily.csv`

| Field | Type | Unit / values | Definition |
| --- | --- | --- | --- |
| `patient_id` | string | generated identifier | Links to `patients.csv`. |
| `recorded_on` | ISO 8601 date | date | Synthetic daily record date. |
| `steps` | integer | steps/day | Synthetic wearable-like step count. |
| `active_minutes` | number | minutes/day | Synthetic activity duration. |
| `resting_heart_rate_bpm` | number | beats/minute | Synthetic resting-heart-rate-like value. |
| `sleep_duration_hours` | number | hours/day | Synthetic sleep duration. |
| `sleep_consistency_percent` | number | percent | Synthetic sleep-timing consistency. |

## `prediction_index.csv`

| Field | Type | Unit / values | Definition |
| --- | --- | --- | --- |
| `patient_id` | string | generated identifier | Links to source tables. |
| `prediction_at` | ISO 8601 date | date | Feature cut-off timestamp. |
| `target_at` | ISO 8601 date | date | Future synthetic-target timestamp. |
| `synthetic_future_hba1c_percent` | number | percent | Generated regression target; never a laboratory measurement. |

## Feature-window policy

The future target must have `target_at > prediction_at`. Wearable features
are aggregated from the 14 complete days ending on `prediction_at`; records
after that timestamp are unavailable to feature generation. Historical clinical
features use the latest eligible observation on or before `prediction_at`.

## Processed feature table

| Field | Unit / values | Definition |
| --- | --- | --- |
| `patient_id` | generated identifier | Synthetic patient key; the split unit (patient-disjoint splits). |
| `prediction_at` | ISO 8601 date | Feature cut-off timestamp. |
| `target_at` | ISO 8601 date | Future synthetic-target timestamp (90 days after cut-off). |
| `age_years` | years | Derived from `birth_year` and `prediction_at`. |
| `diabetes_history_years` | years | Copied synthetic history feature. |
| `latest_hba1c_percent` | percent | Latest eligible synthetic clinical observation. |
| `latest_fasting_glucose_mg_dl` | mg/dL | Latest eligible synthetic clinical observation. |
| `latest_bmi_kg_m2` | kg/m² | Latest eligible synthetic clinical observation. |
| `steps_14d_mean` | steps/day | Mean over exactly 14 dates ending on `prediction_at`. |
| `active_minutes_14d_mean` | minutes/day | 14-day mean. |
| `resting_heart_rate_14d_mean` | beats/minute | 14-day mean. |
| `sleep_duration_14d_mean` | hours/day | 14-day mean. |
| `sleep_consistency_14d_mean` | percent | 14-day mean. |
| `synthetic_future_hba1c_percent` | percent | Generated target; never a lab result. |
