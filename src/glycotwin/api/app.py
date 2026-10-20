"""HTTP API backed by the saved synthetic regression pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from glycotwin.data.features import build_feature_table
from glycotwin.data.tables import SyntheticTables, load_tables
from glycotwin.data.validation import validate_tables
from glycotwin.training.train import load_model_artifact

SYNTHETIC_WARNING = (
    "Synthetic demo output only; not a laboratory result, diagnosis, or treatment recommendation."
)
FOLLOW_UP_MESSAGE = "Synthetic demo rule met; consider clinical/laboratory review."
SCENARIO_FIELDS = (
    "steps_14d_mean",
    "active_minutes_14d_mean",
    "resting_heart_rate_14d_mean",
    "sleep_duration_14d_mean",
    "sleep_consistency_14d_mean",
)


class PredictionRequest(BaseModel):
    """Request an estimate for one synthetic patient."""

    patient_id: str = Field(min_length=1)


class ScenarioRequest(PredictionRequest):
    """Scenario changes to supported 14-day synthetic wearable aggregates."""

    steps_14d_mean: float | None = Field(default=None, ge=0, le=100_000)
    active_minutes_14d_mean: float | None = Field(default=None, ge=0, le=1_440)
    resting_heart_rate_14d_mean: float | None = Field(default=None, ge=20, le=240)
    sleep_duration_14d_mean: float | None = Field(default=None, ge=0, le=24)
    sleep_consistency_14d_mean: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def require_one_adjustment(self) -> "ScenarioRequest":
        if all(getattr(self, name) is None for name in SCENARIO_FIELDS):
            raise ValueError("At least one scenario adjustment is required")
        return self


@dataclass(frozen=True)
class ApiSettings:
    """Local paths and documented non-clinical alert configuration."""

    data_dir: Path = Path("data/sample")
    model_path: Path = Path("models/synthetic_hba1c_regression.joblib")
    alert_hba1c_threshold: float = 8.0
    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")


class GlycoTwinService:
    """Read-only synthetic patient repository plus real pipeline inference."""

    def __init__(self, settings: ApiSettings) -> None:
        self.settings = settings
        self.tables: SyntheticTables = load_tables(settings.data_dir)
        validate_tables(self.tables)
        self.features = build_feature_table(self.tables).set_index("patient_id", drop=False)
        self.patients = self.tables.patients.set_index("patient_id", drop=False)

    def _patient_features(self, patient_id: str) -> pd.DataFrame:
        if patient_id not in self.features.index:
            raise HTTPException(status_code=404, detail=f"Unknown synthetic patient_id: {patient_id}")
        return self.features.loc[[patient_id]].copy()

    def _model_artifact(self) -> dict[str, Any]:
        try:
            return load_model_artifact(self.settings.model_path)
        except (FileNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=503,
                detail="Model unavailable. Train the synthetic regression pipeline before requesting inference.",
            ) from error

    def model_status(self) -> tuple[bool, str | None]:
        try:
            artifact = load_model_artifact(self.settings.model_path)
        except (FileNotFoundError, ValueError):
            return False, None
        return True, str(artifact["model_version"])

    @staticmethod
    def _estimate(artifact: dict[str, Any], feature_row: pd.DataFrame) -> float:
        feature_columns = list(artifact["feature_columns"])
        missing = set(feature_columns).difference(feature_row.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise HTTPException(status_code=503, detail=f"Model requires unavailable feature(s): {names}")
        return float(artifact["pipeline"].predict(feature_row[feature_columns])[0])

    @staticmethod
    def _contributions(artifact: dict[str, Any], feature_row: pd.DataFrame) -> dict[str, Any]:
        """Compute exact per-feature contributions for the linear pipeline.

        The saved artifact is a StandardScaler followed by a Ridge regressor,
        so `coefficient * scaled_value` is the exact additive contribution of
        each feature to the estimate (plus the intercept). This is model
        transparency, not clinical attribution: contributions describe how the
        synthetic linear model produced its number.
        """

        feature_columns = list(artifact["feature_columns"])
        pipeline: Any = artifact["pipeline"]
        regressor = pipeline.named_steps.get("regressor")
        scaler = pipeline.named_steps.get("scale")
        if regressor is None or scaler is None or not hasattr(regressor, "coef_"):
            return {"available": False, "reason": "Selected model does not expose linear coefficients.", "features": []}
        row = feature_row[feature_columns]
        scaled = scaler.transform(row)[0]
        coefficients = [float(value) for value in regressor.coef_]
        intercept = float(regressor.intercept_)
        features = [
            {
                "feature": name,
                "observed_value": float(row.iloc[0][name]),
                "coefficient": coefficients[index],
                "contribution": coefficients[index] * float(scaled[index]),
            }
            for index, name in enumerate(feature_columns)
        ]
        features.sort(key=lambda item: abs(item["contribution"]), reverse=True)
        return {
            "available": True,
            "method": "linear_coefficient_times_scaled_feature",
            "intercept": intercept,
            "note": "Contributions explain the synthetic model's arithmetic, not clinical causation.",
            "features": features,
        }

    def patient_summaries(self) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for patient_id, row in self.patients.sort_index().iterrows():
            feature = self.features.loc[patient_id]
            summaries.append(
                {
                    "patient_id": str(patient_id),
                    "age_years": int(feature["age_years"]),
                    "sex_at_birth": str(row["sex_at_birth"]),
                    "diabetes_history_years": float(row["diabetes_history_years"]),
                    "prediction_at": pd.Timestamp(feature["prediction_at"]).date().isoformat(),
                }
            )
        return summaries

    def patient_detail(self, patient_id: str) -> dict[str, Any]:
        feature = self._patient_features(patient_id).iloc[0]
        patient = self.patients.loc[patient_id]
        clinical = self.tables.clinical_observations.loc[
            self.tables.clinical_observations["patient_id"].astype(str) == patient_id
        ].sort_values("observed_at")
        wearable = self.tables.wearable_daily.loc[
            self.tables.wearable_daily["patient_id"].astype(str) == patient_id
        ].sort_values("recorded_on")
        return {
            "patient_id": patient_id,
            "age_years": int(feature["age_years"]),
            "sex_at_birth": str(patient["sex_at_birth"]),
            "diabetes_history_years": float(patient["diabetes_history_years"]),
            "prediction_at": pd.Timestamp(feature["prediction_at"]).date().isoformat(),
            "clinical_observations": [
                {
                    "observed_at": row.observed_at.date().isoformat(),
                    "hba1c_percent": float(row.hba1c_percent),
                    "fasting_glucose_mg_dl": float(row.fasting_glucose_mg_dl),
                    "bmi_kg_m2": float(row.bmi_kg_m2),
                    "data_kind": "synthetic_historical_observation",
                }
                for row in clinical.itertuples(index=False)
            ],
            "wearable_daily": [
                {
                    "recorded_on": row.recorded_on.date().isoformat(),
                    "steps": int(row.steps),
                    "active_minutes": float(row.active_minutes),
                    "resting_heart_rate_bpm": float(row.resting_heart_rate_bpm),
                    "sleep_duration_hours": float(row.sleep_duration_hours),
                    "sleep_consistency_percent": float(row.sleep_consistency_percent),
                    "data_kind": "synthetic_wearable_like_observation",
                }
                for row in wearable.itertuples(index=False)
            ],
            "warnings": [SYNTHETIC_WARNING],
        }

    def predict(self, patient_id: str) -> dict[str, Any]:
        features = self._patient_features(patient_id)
        artifact = self._model_artifact()
        estimate = self._estimate(artifact, features)
        feature = features.iloc[0]
        horizon_days = int(
            (pd.Timestamp(feature["target_at"]) - pd.Timestamp(feature["prediction_at"])).days
        )
        return {
            "patient_id": patient_id,
            "prediction_at": pd.Timestamp(feature["prediction_at"]).date().isoformat(),
            "estimate_horizon_days": horizon_days,
            "output_kind": "synthetic_model_estimated_future_hba1c_percent",
            "estimated_hba1c_percent": estimate,
            "model_version": str(artifact["model_version"]),
            "model_name": str(artifact["selected_model_name"]),
            "feature_columns": list(artifact["feature_columns"]),
            "explanation": self._contributions(artifact, features),
            "uncertainty": None,
            "deterioration_risk_available": False,
            "warnings": [SYNTHETIC_WARNING],
        }

    def simulate(self, request: ScenarioRequest) -> dict[str, Any]:
        baseline_features = self._patient_features(request.patient_id)
        artifact = self._model_artifact()
        supported_by_model = set(artifact["feature_columns"])
        scenario_features = baseline_features.copy()
        modifications: dict[str, dict[str, float]] = {}
        for field_name in SCENARIO_FIELDS:
            scenario_value = getattr(request, field_name)
            if scenario_value is None:
                continue
            if field_name not in supported_by_model:
                raise HTTPException(
                    status_code=422,
                    detail=f"Selected model does not use scenario input: {field_name}",
                )
            baseline_value = float(baseline_features.iloc[0][field_name])
            scenario_features.loc[:, field_name] = scenario_value
            modifications[field_name] = {
                "observed_synthetic_feature_value": baseline_value,
                "scenario_feature_value": float(scenario_value),
            }
        baseline_estimate = self._estimate(artifact, baseline_features)
        scenario_estimate = self._estimate(artifact, scenario_features)
        return {
            "patient_id": request.patient_id,
            "output_kind": "synthetic_model_scenario_estimated_future_hba1c_percent",
            "baseline_estimated_hba1c_percent": baseline_estimate,
            "scenario_estimated_hba1c_percent": scenario_estimate,
            "scenario_minus_baseline": scenario_estimate - baseline_estimate,
            "modifications": modifications,
            "model_version": str(artifact["model_version"]),
            "deterioration_risk_available": False,
            "warnings": [
                SYNTHETIC_WARNING,
                "Scenario output is an exploratory model response, not a guaranteed treatment outcome.",
            ],
        }

    def alerts(self) -> dict[str, Any]:
        alerts: list[dict[str, Any]] = []
        clinical = self.tables.clinical_observations.sort_values("observed_at")
        for patient_id in self.patients.index.astype(str):
            latest = clinical.loc[clinical["patient_id"].astype(str) == patient_id].iloc[-1]
            latest_hba1c = float(latest["hba1c_percent"])
            if latest_hba1c >= self.settings.alert_hba1c_threshold:
                alerts.append(
                    {
                        "patient_id": patient_id,
                        "observed_at": pd.Timestamp(latest["observed_at"]).date().isoformat(),
                        "observed_synthetic_hba1c_percent": latest_hba1c,
                        "message": FOLLOW_UP_MESSAGE,
                    }
                )
        return {
            "rule": {
                "name": "synthetic_historical_hba1c_threshold",
                "threshold_percent": self.settings.alert_hba1c_threshold,
                "status": "configurable_demo_rule_not_clinically_approved",
            },
            "alerts": alerts,
            "warnings": [SYNTHETIC_WARNING],
        }


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Create the local API app with data loaded once and a model loaded per request."""

    resolved_settings = settings or ApiSettings()
    service = GlycoTwinService(resolved_settings)
    app = FastAPI(
        title="GlycoTwin API",
        version="0.1.0",
        description="Synthetic Type 2 diabetes research/demo inference API; not for clinical use.",
    )
    app.state.glycotwin_service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_allow_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        model_available, model_version = service.model_status()
        return {
            "status": "ok",
            "synthetic_data_loaded": True,
            "model_available": model_available,
            "model_version": model_version,
            "deterioration_risk_available": False,
        }

    @app.get("/patients")
    async def patients() -> dict[str, Any]:
        return {"patients": service.patient_summaries(), "synthetic_only": True}

    @app.get("/patients/{patient_id}")
    async def patient_detail(patient_id: str) -> dict[str, Any]:
        return service.patient_detail(patient_id)

    @app.post("/predict")
    async def predict(request: PredictionRequest) -> dict[str, Any]:
        return service.predict(request.patient_id)

    @app.post("/simulate")
    async def simulate(request: ScenarioRequest) -> dict[str, Any]:
        return service.simulate(request)

    @app.get("/alerts")
    async def alerts() -> dict[str, Any]:
        return service.alerts()

    return app
