"""API tests using a temporary synthetic dataset and trained artifact."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from glycotwin.api.app import ApiSettings, create_app
from glycotwin.data.prepare import prepare_data
from glycotwin.data.synthetic import SyntheticDataConfig, generate_synthetic_tables
from glycotwin.data.tables import save_tables
from glycotwin.training.train import train_and_evaluate


@pytest.fixture(scope="module")
def api_app(tmp_path_factory: pytest.TempPathFactory) -> FastAPI:
    module_dir = tmp_path_factory.mktemp("api")
    source_dir = module_dir / "source"
    processed_dir = module_dir / "processed"
    model_dir = module_dir / "models"
    save_tables(
        generate_synthetic_tables(SyntheticDataConfig(patient_count=24, seed=991)),
        source_dir,
    )
    prepare_data(source_dir, processed_dir, seed=992)
    outcome = train_and_evaluate(processed_dir, model_dir)
    return create_app(ApiSettings(data_dir=source_dir, model_path=outcome.model_path))


def api_request(app: FastAPI, method: str, path: str, payload: dict[str, object] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=payload)

    return asyncio.run(request())


def test_patient_browsing_and_prediction_use_a_saved_artifact(api_app: FastAPI) -> None:
    health = api_request(api_app, "GET", "/health")
    patients = api_request(api_app, "GET", "/patients")

    assert health.status_code == 200
    assert health.json()["model_available"] is True
    assert patients.status_code == 200
    assert len(patients.json()["patients"]) == 24
    patient_id = patients.json()["patients"][0]["patient_id"]

    detail = api_request(api_app, "GET", f"/patients/{patient_id}")
    prediction = api_request(api_app, "POST", "/predict", {"patient_id": patient_id})

    assert detail.status_code == 200
    assert len(detail.json()["clinical_observations"]) == 3
    assert len(detail.json()["wearable_daily"]) == 14
    assert prediction.status_code == 200
    response = prediction.json()
    assert response["output_kind"] == "synthetic_model_estimated_future_hba1c_percent"
    assert response["deterioration_risk_available"] is False
    assert response["uncertainty"] is None
    assert response["estimated_hba1c_percent"] > 0


def test_prediction_explanation_contributions_sum_to_the_estimate(api_app: FastAPI) -> None:
    patient_id = api_request(api_app, "GET", "/patients").json()["patients"][0]["patient_id"]
    response = api_request(api_app, "POST", "/predict", {"patient_id": patient_id})

    assert response.status_code == 200
    explanation = response.json()["explanation"]
    assert explanation["available"] is True
    assert explanation["method"] == "linear_coefficient_times_scaled_feature"
    features = explanation["features"]
    assert {item["feature"] for item in features} == set(response.json()["feature_columns"])
    reconstructed = explanation["intercept"] + sum(item["contribution"] for item in features)
    assert reconstructed == pytest.approx(response.json()["estimated_hba1c_percent"])


def test_simulation_changes_supported_feature_and_reuses_the_model(api_app: FastAPI) -> None:
    patient_id = api_request(api_app, "GET", "/patients").json()["patients"][0]["patient_id"]
    response = api_request(
        api_app,
        "POST",
        "/simulate",
        {"patient_id": patient_id, "steps_14d_mean": 1_000},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["modifications"]["steps_14d_mean"]["scenario_feature_value"] == 1_000
    assert payload["baseline_estimated_hba1c_percent"] != payload["scenario_estimated_hba1c_percent"]
    assert payload["deterioration_risk_available"] is False


def test_invalid_requests_and_missing_model_return_explicit_errors(
    tmp_path: Path,
    api_app: FastAPI,
) -> None:
    assert api_request(api_app, "GET", "/patients/UNKNOWN").status_code == 404
    assert api_request(api_app, "POST", "/predict", {"patient_id": "UNKNOWN"}).status_code == 404
    assert api_request(api_app, "POST", "/simulate", {"patient_id": "SYN-0001"}).status_code == 422

    source_dir = tmp_path / "source"
    save_tables(
        generate_synthetic_tables(SyntheticDataConfig(patient_count=3, seed=993)),
        source_dir,
    )
    missing_model_app = create_app(
        ApiSettings(
            data_dir=source_dir,
            model_path=tmp_path / "missing-model.joblib",
        )
    )
    assert api_request(missing_model_app, "GET", "/health").json()["model_available"] is False
    unavailable = api_request(missing_model_app, "POST", "/predict", {"patient_id": "SYN-0001"})
    assert unavailable.status_code == 503
    assert "Model unavailable" in unavailable.json()["detail"]


def test_alerts_expose_only_a_configurable_demo_rule(api_app: FastAPI) -> None:
    response = api_request(api_app, "GET", "/alerts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rule"]["status"] == "configurable_demo_rule_not_clinically_approved"
    assert "risk" not in payload


def test_cors_preflight_allows_the_local_frontend_only(api_app: FastAPI) -> None:
    async def preflight(origin: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=api_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.options(
                "/predict",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                },
            )

    allowed = asyncio.run(preflight("http://localhost:5173"))
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"

    denied = asyncio.run(preflight("http://evil.example"))
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
