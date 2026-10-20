"""CLI for validating source data and creating leakage-safe processed splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .features import FEATURE_COLUMNS, TARGET_COLUMN, build_feature_table, split_by_patient
from .tables import load_tables
from .validation import validate_tables


def prepare_data(input_dir: Path, output_dir: Path, seed: int = 20_261_012) -> dict[str, int]:
    """Validate source tables, build features, and write patient-disjoint CSV splits."""

    tables = load_tables(input_dir)
    validate_tables(tables)
    features = build_feature_table(tables)
    splits = split_by_patient(features, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_dir / "features.csv", index=False, date_format="%Y-%m-%d")
    splits.train.to_csv(output_dir / "train.csv", index=False, date_format="%Y-%m-%d")
    splits.validation.to_csv(output_dir / "validation.csv", index=False, date_format="%Y-%m-%d")
    splits.test.to_csv(output_dir / "test.csv", index=False, date_format="%Y-%m-%d")
    metadata = {
        "source": str(input_dir),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "split_seed": seed,
        "row_counts": {
            "features": len(features),
            "train": len(splits.train),
            "validation": len(splits.validation),
            "test": len(splits.test),
        },
        "synthetic_only": True,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata["row_counts"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare validated GlycoTwin synthetic features")
    parser.add_argument("--input-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--seed", type=int, default=20_261_012)
    args = parser.parse_args()
    counts = prepare_data(args.input_dir, args.output_dir, seed=args.seed)
    print(
        "Prepared synthetic feature rows: "
        f"{counts['features']} total / {counts['train']} train / "
        f"{counts['validation']} validation / {counts['test']} test"
    )


if __name__ == "__main__":
    main()
