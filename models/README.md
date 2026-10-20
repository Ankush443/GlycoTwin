# Model artifacts

Run the Phase 3 training command to create local, ignored artifacts:

```bash
PYTHONPATH=src .venv/bin/python -m glycotwin.training.train \
  --processed-dir data/processed --model-dir models
```

The command writes `synthetic_hba1c_regression.joblib` and
`synthetic_hba1c_metrics.json`. Both contain results for a fully synthetic
benchmark and are not clinical models or clinical-performance evidence.
