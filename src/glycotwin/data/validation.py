"""Validation rules for project-owned, synthetic GlycoTwin data."""

from __future__ import annotations

import pandas as pd

from .tables import SyntheticTables


class DataValidationError(ValueError):
    """Raised when a synthetic source table violates its documented contract."""


def _require_columns(frame: pd.DataFrame, table_name: str, columns: set[str]) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise DataValidationError(f"{table_name} is missing required columns: {names}")


def _require_no_missing(frame: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    missing_columns = [column for column in columns if frame[column].isna().any()]
    if missing_columns:
        names = ", ".join(missing_columns)
        raise DataValidationError(f"{table_name} contains missing values in: {names}")


def _require_numeric_range(
    frame: pd.DataFrame,
    table_name: str,
    column: str,
    minimum: float,
    maximum: float,
) -> None:
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.isna().any():
        raise DataValidationError(f"{table_name}.{column} must contain numeric values")
    if ((values < minimum) | (values > maximum)).any():
        raise DataValidationError(
            f"{table_name}.{column} must be between {minimum} and {maximum}"
        )


def _require_date_column(frame: pd.DataFrame, table_name: str, column: str) -> None:
    if not pd.api.types.is_datetime64_any_dtype(frame[column]):
        raise DataValidationError(f"{table_name}.{column} must be parsed as dates")
    if frame[column].isna().any():
        raise DataValidationError(f"{table_name}.{column} contains invalid dates")
    if not (frame[column].dt.normalize() == frame[column]).all():
        raise DataValidationError(f"{table_name}.{column} must use date-level timestamps")


def _require_known_patients(
    frame: pd.DataFrame,
    table_name: str,
    patient_ids: set[str],
) -> None:
    table_patient_ids = set(frame["patient_id"].astype(str))
    unknown = table_patient_ids.difference(patient_ids)
    missing = patient_ids.difference(table_patient_ids)
    if unknown:
        raise DataValidationError(f"{table_name} contains unknown patient_id values")
    if missing:
        raise DataValidationError(f"{table_name} is missing one or more patients")


def validate_tables(tables: SyntheticTables) -> None:
    """Validate schema, linkage, dates, duplicates, and plausible synthetic ranges."""

    patients = tables.patients
    clinical = tables.clinical_observations
    wearable = tables.wearable_daily
    prediction = tables.prediction_index

    _require_columns(
        patients,
        "patients",
        {"patient_id", "birth_year", "sex_at_birth", "diabetes_history_years"},
    )
    _require_columns(
        clinical,
        "clinical_observations",
        {
            "patient_id",
            "observed_at",
            "hba1c_percent",
            "fasting_glucose_mg_dl",
            "bmi_kg_m2",
        },
    )
    _require_columns(
        wearable,
        "wearable_daily",
        {
            "patient_id",
            "recorded_on",
            "steps",
            "active_minutes",
            "resting_heart_rate_bpm",
            "sleep_duration_hours",
            "sleep_consistency_percent",
        },
    )
    _require_columns(
        prediction,
        "prediction_index",
        {
            "patient_id",
            "prediction_at",
            "target_at",
            "synthetic_future_hba1c_percent",
        },
    )

    _require_no_missing(
        patients,
        "patients",
        ["patient_id", "birth_year", "sex_at_birth", "diabetes_history_years"],
    )
    _require_no_missing(
        clinical,
        "clinical_observations",
        ["patient_id", "observed_at", "hba1c_percent", "fasting_glucose_mg_dl", "bmi_kg_m2"],
    )
    _require_no_missing(
        wearable,
        "wearable_daily",
        [
            "patient_id",
            "recorded_on",
            "steps",
            "active_minutes",
            "resting_heart_rate_bpm",
            "sleep_duration_hours",
            "sleep_consistency_percent",
        ],
    )
    _require_no_missing(
        prediction,
        "prediction_index",
        ["patient_id", "prediction_at", "target_at", "synthetic_future_hba1c_percent"],
    )

    if patients["patient_id"].duplicated().any():
        raise DataValidationError("patients contains duplicate patient_id values")
    if clinical.duplicated(["patient_id", "observed_at"]).any():
        raise DataValidationError("clinical_observations contains duplicate patient/date rows")
    if wearable.duplicated(["patient_id", "recorded_on"]).any():
        raise DataValidationError("wearable_daily contains duplicate patient/date rows")
    if prediction["patient_id"].duplicated().any():
        raise DataValidationError("prediction_index contains duplicate patient_id values")

    patient_ids = set(patients["patient_id"].astype(str))
    _require_known_patients(clinical, "clinical_observations", patient_ids)
    _require_known_patients(wearable, "wearable_daily", patient_ids)
    _require_known_patients(prediction, "prediction_index", patient_ids)

    _require_date_column(clinical, "clinical_observations", "observed_at")
    _require_date_column(wearable, "wearable_daily", "recorded_on")
    _require_date_column(prediction, "prediction_index", "prediction_at")
    _require_date_column(prediction, "prediction_index", "target_at")
    if not (prediction["target_at"] > prediction["prediction_at"]).all():
        raise DataValidationError("prediction_index.target_at must be after prediction_at")

    _require_numeric_range(patients, "patients", "birth_year", 1900, 2026)
    _require_numeric_range(patients, "patients", "diabetes_history_years", 0, 80)
    if not patients["sex_at_birth"].isin(["female", "male"]).all():
        raise DataValidationError("patients.sex_at_birth must be either female or male")
    _require_numeric_range(clinical, "clinical_observations", "hba1c_percent", 3, 20)
    _require_numeric_range(clinical, "clinical_observations", "fasting_glucose_mg_dl", 20, 600)
    _require_numeric_range(clinical, "clinical_observations", "bmi_kg_m2", 10, 80)
    _require_numeric_range(wearable, "wearable_daily", "steps", 0, 100_000)
    _require_numeric_range(wearable, "wearable_daily", "active_minutes", 0, 1_440)
    _require_numeric_range(wearable, "wearable_daily", "resting_heart_rate_bpm", 20, 240)
    _require_numeric_range(wearable, "wearable_daily", "sleep_duration_hours", 0, 24)
    _require_numeric_range(wearable, "wearable_daily", "sleep_consistency_percent", 0, 100)
    _require_numeric_range(
        prediction,
        "prediction_index",
        "synthetic_future_hba1c_percent",
        3,
        20,
    )
