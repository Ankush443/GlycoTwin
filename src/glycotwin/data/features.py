"""Leakage-safe feature construction and patient-level splitting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .tables import SyntheticTables
from .validation import DataValidationError, validate_tables

FEATURE_COLUMNS = [
    "age_years",
    "diabetes_history_years",
    "latest_hba1c_percent",
    "latest_fasting_glucose_mg_dl",
    "latest_bmi_kg_m2",
    "steps_14d_mean",
    "active_minutes_14d_mean",
    "resting_heart_rate_14d_mean",
    "sleep_duration_14d_mean",
    "sleep_consistency_14d_mean",
]
TARGET_COLUMN = "synthetic_future_hba1c_percent"


@dataclass(frozen=True)
class FeatureSplits:
    """Patient-disjoint feature tables for future training and evaluation."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def build_feature_table(tables: SyntheticTables, wearable_days: int = 14) -> pd.DataFrame:
    """Build one feature row per prediction timestamp using only prior data."""

    if wearable_days != 14:
        raise ValueError("The documented feature contract uses exactly 14 wearable days")
    validate_tables(tables)
    patients = tables.patients.set_index("patient_id")
    clinical = tables.clinical_observations.copy()
    wearable = tables.wearable_daily.copy()
    rows: list[dict[str, object]] = []

    for index_row in tables.prediction_index.sort_values("patient_id").itertuples(index=False):
        patient_id = str(index_row.patient_id)
        prediction_at = pd.Timestamp(index_row.prediction_at).normalize()
        expected_dates = pd.date_range(
            prediction_at - pd.Timedelta(days=wearable_days - 1),
            prediction_at,
            freq="D",
        )
        eligible_clinical = clinical.loc[
            (clinical["patient_id"].astype(str) == patient_id)
            & (clinical["observed_at"] <= prediction_at)
        ].sort_values("observed_at")
        if eligible_clinical.empty:
            raise DataValidationError(f"No clinical history is available at prediction time for {patient_id}")
        latest_clinical = eligible_clinical.iloc[-1]
        wearable_window = wearable.loc[
            (wearable["patient_id"].astype(str) == patient_id)
            & wearable["recorded_on"].isin(expected_dates)
            & (wearable["recorded_on"] <= prediction_at)
        ].sort_values("recorded_on")
        actual_dates = set(wearable_window["recorded_on"])
        if len(wearable_window) != wearable_days or actual_dates != set(expected_dates):
            raise DataValidationError(
                f"{patient_id} does not have a complete {wearable_days}-day wearable window"
            )
        patient = patients.loc[patient_id]
        rows.append(
            {
                "patient_id": patient_id,
                "prediction_at": prediction_at,
                "target_at": pd.Timestamp(index_row.target_at).normalize(),
                "age_years": int(prediction_at.year - int(patient["birth_year"])),
                "diabetes_history_years": float(patient["diabetes_history_years"]),
                "latest_hba1c_percent": float(latest_clinical["hba1c_percent"]),
                "latest_fasting_glucose_mg_dl": float(latest_clinical["fasting_glucose_mg_dl"]),
                "latest_bmi_kg_m2": float(latest_clinical["bmi_kg_m2"]),
                "steps_14d_mean": float(wearable_window["steps"].mean()),
                "active_minutes_14d_mean": float(wearable_window["active_minutes"].mean()),
                "resting_heart_rate_14d_mean": float(wearable_window["resting_heart_rate_bpm"].mean()),
                "sleep_duration_14d_mean": float(wearable_window["sleep_duration_hours"].mean()),
                "sleep_consistency_14d_mean": float(wearable_window["sleep_consistency_percent"].mean()),
                TARGET_COLUMN: float(index_row.synthetic_future_hba1c_percent),
            }
        )

    features = pd.DataFrame(rows).sort_values("patient_id").reset_index(drop=True)
    if not (features["target_at"] > features["prediction_at"]).all():
        raise DataValidationError("Feature rows must retain a future target timestamp")
    return features


def split_by_patient(
    features: pd.DataFrame,
    *,
    seed: int = 20_261_012,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> FeatureSplits:
    """Create deterministic train/validation/test partitions with no patient overlap."""

    if "patient_id" not in features.columns:
        raise ValueError("features must contain patient_id")
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train_fraction plus validation_fraction must be less than one")
    patient_ids = np.array(sorted(features["patient_id"].astype(str).unique()))
    if len(patient_ids) < 3:
        raise ValueError("At least three patients are required for train/validation/test splitting")

    rng = np.random.default_rng(seed)
    rng.shuffle(patient_ids)
    train_count = max(1, int(np.floor(len(patient_ids) * train_fraction)))
    validation_count = max(1, int(np.floor(len(patient_ids) * validation_fraction)))
    if train_count + validation_count >= len(patient_ids):
        raise ValueError("split fractions leave no patient for the test set")
    train_ids = set(patient_ids[:train_count])
    validation_ids = set(patient_ids[train_count : train_count + validation_count])
    test_ids = set(patient_ids[train_count + validation_count :])
    if train_ids & validation_ids or train_ids & test_ids or validation_ids & test_ids:
        raise RuntimeError("Patient-level split overlap detected")

    def subset(patient_subset: set[str]) -> pd.DataFrame:
        return features.loc[features["patient_id"].astype(str).isin(patient_subset)].copy()

    return FeatureSplits(
        train=subset(train_ids),
        validation=subset(validation_ids),
        test=subset(test_ids),
    )
