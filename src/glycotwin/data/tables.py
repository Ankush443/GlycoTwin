"""File names and I/O for the project-owned synthetic data tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

TABLE_FILENAMES = {
    "patients": "patients.csv",
    "clinical_observations": "clinical_observations.csv",
    "wearable_daily": "wearable_daily.csv",
    "prediction_index": "prediction_index.csv",
}


@dataclass(frozen=True)
class SyntheticTables:
    """Related, patient-linked synthetic source tables."""

    patients: pd.DataFrame
    clinical_observations: pd.DataFrame
    wearable_daily: pd.DataFrame
    prediction_index: pd.DataFrame


def save_tables(tables: SyntheticTables, output_dir: Path) -> None:
    """Write source tables as reproducible CSV files without an index column."""

    output_dir.mkdir(parents=True, exist_ok=True)
    tables.patients.to_csv(output_dir / TABLE_FILENAMES["patients"], index=False)
    tables.clinical_observations.to_csv(
        output_dir / TABLE_FILENAMES["clinical_observations"],
        index=False,
        date_format="%Y-%m-%d",
    )
    tables.wearable_daily.to_csv(
        output_dir / TABLE_FILENAMES["wearable_daily"],
        index=False,
        date_format="%Y-%m-%d",
    )
    tables.prediction_index.to_csv(
        output_dir / TABLE_FILENAMES["prediction_index"],
        index=False,
        date_format="%Y-%m-%d",
    )


def load_tables(input_dir: Path) -> SyntheticTables:
    """Load all required CSV files with their date fields parsed."""

    paths = {name: input_dir / filename for name, filename in TABLE_FILENAMES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Missing required synthetic source table(s): {joined}")

    return SyntheticTables(
        patients=pd.read_csv(paths["patients"], dtype={"patient_id": "string"}),
        clinical_observations=pd.read_csv(
            paths["clinical_observations"],
            dtype={"patient_id": "string"},
            parse_dates=["observed_at"],
        ),
        wearable_daily=pd.read_csv(
            paths["wearable_daily"],
            dtype={"patient_id": "string"},
            parse_dates=["recorded_on"],
        ),
        prediction_index=pd.read_csv(
            paths["prediction_index"],
            dtype={"patient_id": "string"},
            parse_dates=["prediction_at", "target_at"],
        ),
    )
