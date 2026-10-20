"""Tests for synthetic-only model training and artifact persistence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from glycotwin.data.prepare import prepare_data
from glycotwin.data.synthetic import SyntheticDataConfig, generate_synthetic_tables
from glycotwin.data.tables import save_tables
from glycotwin.training.train import load_model_artifact, train_and_evaluate


def test_training_saves_a_loadable_train_only_model(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    processed_dir = tmp_path / "processed"
    model_dir = tmp_path / "models"
    save_tables(
        generate_synthetic_tables(SyntheticDataConfig(patient_count=30, seed=123)),
        source_dir,
    )
    prepare_data(source_dir, processed_dir, seed=456)

    outcome = train_and_evaluate(processed_dir, model_dir)
    artifact = load_model_artifact(outcome.model_path)
    metrics = json.loads(outcome.metrics_path.read_text(encoding="utf-8"))

    assert outcome.model_path.is_file()
    assert metrics["synthetic_only"] is True
    assert len(outcome.candidates) == 2
    assert {result.name for result in outcome.candidates} == {
        "clinical_only_ridge",
        "clinical_plus_wearable_ridge",
    }
    assert not set(artifact["train_patient_ids"]) & set(artifact["validation_patient_ids"])
    assert not set(artifact["train_patient_ids"]) & set(artifact["test_patient_ids"])
    assert not set(artifact["validation_patient_ids"]) & set(artifact["test_patient_ids"])

    test_frame = __import__("pandas").read_csv(processed_dir / "test.csv")
    predictions = artifact["pipeline"].predict(test_frame[artifact["feature_columns"]])
    assert len(predictions) == len(test_frame)
    assert np.isfinite(predictions).all()


def test_training_rejects_overlapping_patient_splits(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    processed_dir = tmp_path / "processed"
    model_dir = tmp_path / "models"
    save_tables(
        generate_synthetic_tables(SyntheticDataConfig(patient_count=12, seed=111)),
        source_dir,
    )
    prepare_data(source_dir, processed_dir, seed=222)
    train = __import__("pandas").read_csv(processed_dir / "train.csv")
    validation = __import__("pandas").read_csv(processed_dir / "validation.csv")
    validation.loc[0, "patient_id"] = train.loc[0, "patient_id"]
    validation.to_csv(processed_dir / "validation.csv", index=False)

    import pytest

    with pytest.raises(ValueError, match="share patient_id"):
        train_and_evaluate(processed_dir, model_dir)
