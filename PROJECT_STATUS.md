# GlycoTwin Project Status

**Audit date:** 11 October 2026; last updated 20 October 2026 (submission stage)
**Current phase:** Phase 5 complete; Phase 6 (submission packaging) in progress

## Current implementation status

The repository is a working application, not an initial scaffold. Phases 1
through 5 are implemented and verified:

- **Phase 1 — Scope and data audit:** problem statement, boundaries, data-source
  feasibility decision, architecture, and documentation set in `docs/`.
- **Phase 2 — Data pipeline:** deterministic synthetic generator, source-table
  validation, leakage-safe feature preparation, patient-level splits, and
  documented provenance/target construction.
- **Phase 3 — Model training:** reproducible clinical-only baseline and
  clinical-plus-wearable Ridge benchmark, held-out evaluation, saved model
  artifact, and exact linear prediction explanations (SHAP deliberately not
  used; rationale in the model card).
- **Phase 4 — Inference API:** FastAPI health, patient, prediction,
  simulation, and alert endpoints backed by the saved artifact, with
  validated requests, explicit 404/422/503 errors, and CORS for the local
  frontend.
- **Phase 5 — Clinician dashboard:** React/TypeScript app (`frontend/`) with a
  synthetic patient selector, historical clinical summary with last lab date,
  wearable trend charts, prediction with the exact linear-contribution
  explanation, what-if simulator, follow-up alert panel, a persistent
  prototype notice, and loading/empty/error states that never display stale
  values after a failed request.

The tracked repository at the initial commit contains only `README.md` and
`.gitattributes`; all phase work exists as local uncommitted changes (nothing
is committed or pushed unless the project owner asks). The test suite passes
15/15.

`GLYCOTWIN_CLI_AGENT_INSTRUCTIONS.md` is present locally as an **untracked**
development guide and has not been modified.

The documentation records a fully synthetic, patient-linked data approach and
explicitly excludes a deterioration-risk classifier from the first release.

## Git and environment

- Branch: `main`, tracking `origin/main` at initial commit `332e1e0`.
- Working tree: Phase 1–5 implementation and documentation are uncommitted
  local changes (one modified file and the new `src/`, `tests/`, `docs/`,
  `frontend/`, configuration, and status files) — committed only when the
  owner explicitly requests it.
- Remote: `https://github.com/Ankush443/GlycoTwin.git`.
- Available runtimes: Python `3.14.0`, Node.js `v25.2.0`, npm `11.19.1`.
- `python` is not on `PATH`; `python3` is available.
- `requirements.txt` and `requirements-dev.txt` define the Python runtime and
  test dependencies; `frontend/package.json` defines the frontend dependencies.
  `uv`, Poetry, and Pipenv are not required.
- `python3 -m pip` reports Python 3.14 and is the supported installer command;
  the separately resolved `pip` executable reports Python 3.12 and is not used.

## Existing run and test commands

Create an environment and install dependencies with the commands in `README.md`.
Run all tests with `python -m pytest` after activation (15 tests: data,
training, and API including CORS and explanation exactness). Regenerate the
sample, prepare local processed splits, train the local artifact, then run the
API with the commands in `README.md`. Run the dashboard with `cd frontend &&
npm install && npm run dev` (see the README troubleshooting note about npm
install scripts). Frontend verification is `npm run build` (strict `tsc` plus
a production bundle).

## Dataset inventory and provenance

`data/sample/` contains a 40-patient, project-generated synthetic cohort:
`patients.csv`, `clinical_observations.csv`, `wearable_daily.csv`, and
`prediction_index.csv`, plus generator metadata. It is generated with seed
`20261012`, has three clinical observations and 14 wearable-like daily records
per patient, and uses a 90-day synthetic HbA1c target. Provenance, target
construction, schema, validation, and feature-window rules are documented in
`docs/`. `data/processed/` is intentionally ignored because it is reproducible
local output.

## Missing core components

- Required challenge documentation and deliverables, including architecture
  diagram, presentation, and demonstration-video link (Phase 6).
- Automated end-to-end browser tests for the dashboard; current verification
  is build/typecheck plus live manual HTTP checks of the same API sequence the
  UI performs.

## Risks and blockers

- The 40-patient sample and generated target are synthetic. They cannot support
  clinical-performance, causal, prevalence, or real-world risk claims.
- The target formula is known to the generator, so a future model may only
  demonstrate pipeline behaviour on synthetic relationships.
- The selected model was evaluated on only six held-out synthetic patients and
  does not quantify uncertainty or real-world generalization.
- The API prediction and scenario values inherit all synthetic-data/model
  limitations; the alert threshold is a configurable demo rule, not clinical
  guidance.
- The MIT licence uses the generic “GlycoTwin contributors” holder; replace it
  if the project owner needs a different legal holder or licence.

## Recommended next three actions

1. **Complete submission-quality documentation and audit (Phase 6).** Add the
   required architecture/presentation assets and video link, then verify setup
   and deliverables from a clean environment.
2. **Review and finalize challenge-submission details.** Confirm ownership,
   public-repository state, licence holder, and accessible submission links.
3. **Optionally harden the dashboard.** Add browser-level end-to-end tests and
   consider code-splitting the Recharts bundle if load time matters.
