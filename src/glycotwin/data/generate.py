"""CLI for generating project-owned synthetic source data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .synthetic import SyntheticDataConfig, generate_synthetic_tables
from .tables import save_tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic GlycoTwin synthetic data")
    parser.add_argument("--output-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--patient-count", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20_261_012)
    args = parser.parse_args()
    config = SyntheticDataConfig(patient_count=args.patient_count, seed=args.seed)
    tables = generate_synthetic_tables(config)
    save_tables(tables, args.output_dir)
    metadata = {
        "generator": "glycotwin.data.generate",
        "generator_version": "0.1.0",
        "patient_count": config.patient_count,
        "seed": config.seed,
        "prediction_at": config.prediction_at,
        "wearable_days": config.wearable_days,
        "target_horizon_days": config.target_horizon_days,
        "synthetic_only": True,
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {config.patient_count} synthetic patients to {args.output_dir}")


if __name__ == "__main__":
    main()
