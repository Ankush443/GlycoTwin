# GlycoTwin scope and feasibility decision

**Status:** Phase 1 decision record, written before implementation. The project
has since been implemented through Phase 5; this document remains the binding
scope definition, and the implementation honours every boundary below.

**Implementation outcome (20 October 2026):** the six acceptance criteria were
met — a deterministic generator produces the documented tables; features use
only observations at or before each prediction timestamp (enforced and tested
in the preparer); splits are patient-disjoint; and the API and dashboard label
everything synthetic/model-estimated and expose no deterioration probability
(`deterioration_risk_available: false` on every response).

## Problem statement

GlycoTwin is a local, clinician-facing demonstration of how historical
clinical information and a recent wearable-like time series could be presented
as one synthetic patient record and used in an exploratory model scenario for
Type 2 diabetes glycaemic monitoring.

The intended user is a reviewer or clinician evaluating this research/demo
prototype. The user may select a synthetic patient, inspect historical data,
review a recent activity/sleep trend, request an estimated synthetic HbA1c
output, and compare that output with a supported input scenario.

## Confirmed boundaries

- The prototype addresses Type 2 diabetes and glycaemic monitoring only.
- All records used by the application will be synthetic. The system will not
  ingest real patients, real wearable devices, or real-time feeds.
- An output is a model estimate for a synthetic dataset, not a laboratory
  result, diagnosis, treatment recommendation, or medical-device output.
- Scenario results describe a model response to changed synthetic inputs; they
  do not establish that activity or sleep causes a clinical HbA1c change.
- Any follow-up prompt will say “consider clinical/laboratory review” and be
  presented as a configurable demo rule, not a clinically approved threshold.

## Feasible model claim

The only planned predictive task is a **synthetic HbA1c regression benchmark**:
estimate a generated future HbA1c value at a documented prediction timestamp
from synthetic historical clinical features and a preceding 14-day synthetic
wearable window. The target will be produced by the project data generator and
labelled synthetic throughout the API and user interface.

This task can demonstrate a leakage-safe training and inference pipeline, but
it cannot measure real-world clinical performance or establish that wearable
signals predict HbA1c in people.

## Explicitly unavailable output

The first release will not expose a glycaemic-deterioration probability or
classifier. No externally validated, patient-linked future-outcome labels are
available. A binary label derived from the regression estimate would not be an
independent future-event outcome and will not be represented as one.

## Data-source feasibility assessment

| Candidate | Findings from inspection | Decision |
| --- | --- | --- |
| Project-generated deterministic cohort | Can contain both clinical and daily wearable-like records under one generated `patient_id`, with a fully documented synthetic target. | Selected for the proof of concept. |
| Synthea synthetic patient simulator | The project documents synthetic clinical records, CSV export, and clinical observations; the CSV exporter includes an `observations.csv` table keyed by patient. No linked steps, active-minutes, resting-heart-rate, or sleep feed was verified in this audit. | Not selected as the initial linked dataset. It may be reconsidered only as an optional clinical reference after a fresh field-level inspection. |
| Independently sourced wearable datasets | No candidate was verified here as sharing patient identity and temporally aligned clinical HbA1c records with a candidate EHR source. | Excluded. They must not be merged with another source and described as the same patients. |

Synthea references inspected: [project repository](https://github.com/synthetichealth/synthea), [CSV exporter](https://github.com/synthetichealth/synthea/blob/master/src/main/java/org/mitre/synthea/export/CSVExporter.java), and [CSV configuration](https://github.com/synthetichealth/synthea/blob/master/src/main/resources/synthea.properties). Synthea is Apache-2.0 licensed; this is not a licence determination for any individual generated export or terminology used within it.

## Acceptance criteria before modelling

1. A deterministic generator produces documented clinical, wearable, and target
   tables for the same synthetic patients.
2. Each prediction row uses only observations dated on or before its prediction
   timestamp; its future synthetic HbA1c target is stored separately.
3. Training/validation/test splits are by `patient_id`.
4. The UI and API use “synthetic” and “model-estimated” labels and never expose
   an unavailable deterioration probability.
