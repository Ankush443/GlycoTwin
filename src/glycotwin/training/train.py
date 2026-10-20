"""Train and evaluate the documented synthetic HbA1c regression benchmark."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from glycotwin.data.features import FEATURE_COLUMNS, TARGET_COLUMN

MODEL_VERSION = "synthetic-hba1c-ridge-v0.1.0"
CLINICAL_FEATURE_COLUMNS = [
    "age_years",
    "diabetes_history_years",
    "latest_hba1c_percent",
    "latest_fasting_glucose_mg_dl",
    "latest_bmi_kg_m2",
]
COMBINED_FEATURE_COLUMNS = FEATURE_COLUMNS


@dataclass(frozen=True)
class RegressionMetrics:
    """Measured regression metrics for a single split."""

    sample_count: int
    mae: float
    rmse: float


@dataclass(frozen=True)
class CandidateResult:
    """Measured performance for one candidate feature set."""

    name: str
    feature_columns: list[str]
    validation: RegressionMetrics
    test: RegressionMetrics


@dataclass(frozen=True)
class TrainingOutcome:
    """Paths and measured results returned by a complete training run."""

    selected_model_name: str
    model_path: Path
    metrics_path: Path
    candidates: list[CandidateResult]


def _load_split(processed_dir: Path, split_name: str) -> pd.DataFrame:
    path = processed_dir / f"{split_name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing processed split: {path}")
    frame = pd.read_csv(path, dtype={"patient_id": "string"})
    required = {"patient_id", TARGET_COLUMN, *FEATURE_COLUMNS}
    missing = required.difference(frame.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"{split_name}.csv is missing required columns: {names}")
    if frame.empty:
        raise ValueError(f"{split_name}.csv must contain at least one row")
    if frame[list(required)].isna().any().any():
        raise ValueError(f"{split_name}.csv contains missing model inputs or targets")
    return frame


def _load_splits(processed_dir: Path) -> dict[str, pd.DataFrame]:
    splits = {name: _load_split(processed_dir, name) for name in ("train", "validation", "test")}
    patient_sets = {name: set(frame["patient_id"].astype(str)) for name, frame in splits.items()}
    if patient_sets["train"] & patient_sets["validation"]:
        raise ValueError("Train and validation splits share patient_id values")
    if patient_sets["train"] & patient_sets["test"]:
        raise ValueError("Train and test splits share patient_id values")
    if patient_sets["validation"] & patient_sets["test"]:
        raise ValueError("Validation and test splits share patient_id values")
    return splits


def _make_pipeline() -> Pipeline:
    """Return the simple, deterministic regression pipeline used for both models."""

    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("regressor", Ridge(alpha=1.0)),
        ]
    )


def _evaluate(model: Pipeline, frame: pd.DataFrame, feature_columns: list[str]) -> RegressionMetrics:
    expected = frame[TARGET_COLUMN].to_numpy(dtype=float)
    predicted = model.predict(frame[feature_columns])
    return RegressionMetrics(
        sample_count=len(frame),
        mae=float(mean_absolute_error(expected, predicted)),
        rmse=float(np.sqrt(mean_squared_error(expected, predicted))),
    )


def train_and_evaluate(processed_dir: Path, model_dir: Path) -> TrainingOutcome:
    """Fit two train-only candidates, select by validation MAE, and save one artifact.

    Both candidates are fitted using only `train.csv`. The validation split is
    used solely to choose the feature set, while `test.csv` is held out for the
    reported final evaluation.
    """

    splits = _load_splits(processed_dir)
    candidate_specs = {
        "clinical_only_ridge": CLINICAL_FEATURE_COLUMNS,
        "clinical_plus_wearable_ridge": COMBINED_FEATURE_COLUMNS,
    }
    trained_models: dict[str, Pipeline] = {}
    results: list[CandidateResult] = []
    for name, feature_columns in candidate_specs.items():
        model = _make_pipeline()
        model.fit(splits["train"][feature_columns], splits["train"][TARGET_COLUMN])
        trained_models[name] = model
        results.append(
            CandidateResult(
                name=name,
                feature_columns=feature_columns,
                validation=_evaluate(model, splits["validation"], feature_columns),
                test=_evaluate(model, splits["test"], feature_columns),
            )
        )

    selected = min(results, key=lambda result: result.validation.mae)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "synthetic_hba1c_regression.joblib"
    metrics_path = model_dir / "synthetic_hba1c_metrics.json"
    artifact: dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "synthetic_only": True,
        "selected_model_name": selected.name,
        "feature_columns": selected.feature_columns,
        "target_column": TARGET_COLUMN,
        "fit_split": "train",
        "pipeline": trained_models[selected.name],
        "train_patient_ids": sorted(splits["train"]["patient_id"].astype(str).unique()),
        "validation_patient_ids": sorted(splits["validation"]["patient_id"].astype(str).unique()),
        "test_patient_ids": sorted(splits["test"]["patient_id"].astype(str).unique()),
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(artifact, model_path)
    metrics_payload = {
        "model_version": MODEL_VERSION,
        "synthetic_only": True,
        "selection_rule": "lowest validation MAE",
        "selected_model_name": selected.name,
        "candidates": [asdict(result) for result in results],
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2) + "\n", encoding="utf-8")
    return TrainingOutcome(
        selected_model_name=selected.name,
        model_path=model_path,
        metrics_path=metrics_path,
        candidates=results,
    )


def load_model_artifact(model_path: Path) -> dict[str, Any]:
    """Load a saved artifact and check the minimum metadata contract."""

    if not model_path.is_file():
        raise FileNotFoundError(f"Model artifact does not exist: {model_path}")
    artifact = joblib.load(model_path)
    required = {"model_version", "synthetic_only", "feature_columns", "pipeline"}
    missing = required.difference(artifact)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"Model artifact is missing required metadata: {names}")
    if artifact["synthetic_only"] is not True:
        raise ValueError("GlycoTwin Phase 3 artifact must be labelled synthetic_only")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the synthetic GlycoTwin HbA1c regression benchmark")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()
    outcome = train_and_evaluate(args.processed_dir, args.model_dir)
    selected = next(result for result in outcome.candidates if result.name == outcome.selected_model_name)
    print(f"Selected model: {selected.name} (validation MAE {selected.validation.mae:.3f})")
    print(f"Held-out test MAE: {selected.test.mae:.3f}; RMSE: {selected.test.rmse:.3f}")
    print(f"Saved model artifact: {outcome.model_path}")
    print(f"Saved metrics: {outcome.metrics_path}")


if __name__ == "__main__":
    main()
