# Synthetic sample data

This directory contains a small, project-generated synthetic cohort for local
development and tests. It contains no real people, device records, or clinical
measurements.

Generate the committed 40-patient sample from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m glycotwin.data.generate \
  --output-dir data/sample --patient-count 40 --seed 20261012
```

The command overwrites the four generated CSV files and `metadata.json` in this
directory. The generator configuration and target-construction policy are
documented in `docs/data_provenance.md`.
