# Architecture

**Status:** Phase 5. The data pipeline, synthetic model, FastAPI inference
service, and React/TypeScript clinician dashboard are implemented.

```text
Versioned synthetic-data generator
    ├─ patients.csv
    ├─ clinical_observations.csv
    ├─ wearable_daily.csv
    └─ prediction_index.csv (future synthetic target)
                │
                ▼
Validation and leakage-safe feature pipeline (implemented)
                │
                ▼
Synthetic HbA1c regression model + saved preprocessing (implemented)
                │
                ▼
FastAPI inference service (implemented) ─── React/TypeScript dashboard
       │        │        │        │                    │ (implemented)
   /health  /patients /predict /simulate /alerts      │
       │        │        │        │                    │
       └─ exact linear contributions   └─ configurable follow-up rule
          (coefficient × scaled value)      │
                                            ▼
                              patient selector, clinical summary,
                              wearable trend charts, prediction +
                              explanation, what-if simulator,
                              alert panel, loading/error states
```

The frontend runs on Vite (`frontend/`, port 5173) and reaches the API through
a same-origin `/api` proxy during development; the API additionally enables
CORS for the local frontend origin as a fallback. Requests are only issued
when the user asks (run inference, run scenario, check alerts), so the UI
never displays fabricated or auto-generated model outputs.

The pipeline preserves `patient_id` and timestamps. The model service returns
an explicitly unavailable state for any output it cannot produce; it does not
substitute constants. The dashboard distinguishes observed synthetic records,
historical values, model estimates, and scenario values, and clears previous
results before each request so a failed call never shows stale numbers.

No external database, cloud service, wearable hardware integration, or booking
system is part of this design.
