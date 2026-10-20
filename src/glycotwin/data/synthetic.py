"""Deterministic, project-owned synthetic data generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .tables import SyntheticTables
from .validation import validate_tables


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Configuration recorded with every generated synthetic cohort."""

    patient_count: int = 120
    seed: int = 20_261_012
    prediction_at: str = "2026-10-01"
    wearable_days: int = 14
    target_horizon_days: int = 90

    def __post_init__(self) -> None:
        if self.patient_count < 3:
            raise ValueError("patient_count must be at least 3")
        if self.wearable_days != 14:
            raise ValueError("The documented pipeline currently requires a 14-day wearable window")
        if self.target_horizon_days <= 0:
            raise ValueError("target_horizon_days must be positive")


def _clip(value: float, lower: float, upper: float) -> float:
    return float(np.clip(value, lower, upper))


def generate_synthetic_tables(config: SyntheticDataConfig) -> SyntheticTables:
    """Generate linked synthetic records and an explicitly synthetic future target.

    The relationship between inputs and target is intentionally a generator
    mechanism for a software demonstration. It is not a clinical model.
    """

    rng = np.random.default_rng(config.seed)
    prediction_at = pd.Timestamp(config.prediction_at).normalize()
    target_at = prediction_at + pd.Timedelta(days=config.target_horizon_days)
    wearable_dates = pd.date_range(
        prediction_at - pd.Timedelta(days=config.wearable_days - 1),
        prediction_at,
        freq="D",
    )

    patient_rows: list[dict[str, object]] = []
    clinical_rows: list[dict[str, object]] = []
    wearable_rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []

    for patient_number in range(1, config.patient_count + 1):
        patient_id = f"SYN-{patient_number:04d}"
        age_years = int(rng.integers(40, 81))
        birth_year = prediction_at.year - age_years
        diabetes_history_years = round(float(rng.uniform(0.5, 20.0)), 1)
        sex_at_birth = str(rng.choice(["female", "male"]))
        baseline_bmi = _clip(rng.normal(30.0, 4.5), 19.0, 45.0)
        baseline_hba1c = _clip(
            5.7 + 0.045 * diabetes_history_years + 0.075 * (baseline_bmi - 25.0)
            + rng.normal(0.0, 0.35),
            5.0,
            11.5,
        )
        patient_rows.append(
            {
                "patient_id": patient_id,
                "birth_year": birth_year,
                "sex_at_birth": sex_at_birth,
                "diabetes_history_years": diabetes_history_years,
            }
        )

        clinical_values: list[dict[str, object]] = []
        for offset_days, drift in [(-180, -0.12), (-90, -0.05), (0, 0.0)]:
            hba1c = _clip(baseline_hba1c + drift + rng.normal(0.0, 0.12), 4.5, 13.0)
            fasting_glucose = _clip(78.0 + 19.0 * (hba1c - 5.0) + rng.normal(0.0, 8.0), 70.0, 330.0)
            bmi = _clip(baseline_bmi + rng.normal(0.0, 0.45), 18.0, 48.0)
            row = {
                "patient_id": patient_id,
                "observed_at": prediction_at + pd.Timedelta(days=offset_days),
                "hba1c_percent": round(hba1c, 2),
                "fasting_glucose_mg_dl": round(fasting_glucose, 1),
                "bmi_kg_m2": round(bmi, 1),
            }
            clinical_rows.append(row)
            clinical_values.append(row)

        activity_baseline = _clip(rng.normal(7_000.0, 1_800.0), 2_000.0, 13_000.0)
        sleep_baseline = _clip(rng.normal(7.0, 0.8), 4.5, 9.5)
        rhr_baseline = _clip(rng.normal(72.0, 8.0), 50.0, 95.0)
        for day_number, recorded_on in enumerate(wearable_dates):
            weekend_adjustment = -500.0 if recorded_on.dayofweek >= 5 else 0.0
            steps = int(_clip(activity_baseline + weekend_adjustment + rng.normal(0.0, 900.0), 500.0, 20_000.0))
            active_minutes = _clip(20.0 + steps / 145.0 + rng.normal(0.0, 8.0), 5.0, 240.0)
            resting_heart_rate = _clip(rhr_baseline - (steps - activity_baseline) / 3_000.0 + rng.normal(0.0, 2.2), 42.0, 115.0)
            sleep_duration = _clip(sleep_baseline + rng.normal(0.0, 0.45), 3.5, 11.0)
            sleep_consistency = _clip(82.0 - abs(day_number - 6.5) * 1.2 + rng.normal(0.0, 5.0), 45.0, 100.0)
            wearable_rows.append(
                {
                    "patient_id": patient_id,
                    "recorded_on": recorded_on,
                    "steps": steps,
                    "active_minutes": round(active_minutes, 1),
                    "resting_heart_rate_bpm": round(resting_heart_rate, 1),
                    "sleep_duration_hours": round(sleep_duration, 2),
                    "sleep_consistency_percent": round(sleep_consistency, 1),
                }
            )

        patient_wearable = [row for row in wearable_rows if row["patient_id"] == patient_id]
        steps_mean = float(np.mean([row["steps"] for row in patient_wearable]))
        active_minutes_mean = float(np.mean([row["active_minutes"] for row in patient_wearable]))
        rhr_mean = float(np.mean([row["resting_heart_rate_bpm"] for row in patient_wearable]))
        sleep_duration_mean = float(np.mean([row["sleep_duration_hours"] for row in patient_wearable]))
        sleep_consistency_mean = float(np.mean([row["sleep_consistency_percent"] for row in patient_wearable]))
        latest = clinical_values[-1]
        synthetic_future_hba1c = _clip(
            float(latest["hba1c_percent"])
            + 0.012 * (float(latest["bmi_kg_m2"]) - 30.0)
            + 0.0035 * (float(latest["fasting_glucose_mg_dl"]) - 130.0)
            + 0.000025 * (7_000.0 - steps_mean)
            + 0.003 * (120.0 - active_minutes_mean)
            + 0.012 * (rhr_mean - 72.0)
            + 0.05 * (7.0 - sleep_duration_mean)
            + 0.006 * (80.0 - sleep_consistency_mean)
            + rng.normal(0.0, 0.18),
            4.5,
            13.0,
        )
        prediction_rows.append(
            {
                "patient_id": patient_id,
                "prediction_at": prediction_at,
                "target_at": target_at,
                "synthetic_future_hba1c_percent": round(synthetic_future_hba1c, 2),
            }
        )

    tables = SyntheticTables(
        patients=pd.DataFrame(patient_rows),
        clinical_observations=pd.DataFrame(clinical_rows),
        wearable_daily=pd.DataFrame(wearable_rows),
        prediction_index=pd.DataFrame(prediction_rows),
    )
    validate_tables(tables)
    return tables
