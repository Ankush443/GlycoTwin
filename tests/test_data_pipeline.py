"""Tests for synthetic data generation, validation, and feature preparation."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from glycotwin.data.features import FEATURE_COLUMNS, build_feature_table, split_by_patient
from glycotwin.data.prepare import prepare_data
from glycotwin.data.synthetic import SyntheticDataConfig, generate_synthetic_tables
from glycotwin.data.tables import SyntheticTables, load_tables, save_tables
from glycotwin.data.validation import DataValidationError, validate_tables


def test_generator_is_deterministic_and_linked() -> None:
    config = SyntheticDataConfig(patient_count=6, seed=41)
    first = generate_synthetic_tables(config)
    second = generate_synthetic_tables(config)

    pd.testing.assert_frame_equal(first.patients, second.patients)
    pd.testing.assert_frame_equal(first.clinical_observations, second.clinical_observations)
    pd.testing.assert_frame_equal(first.wearable_daily, second.wearable_daily)
    pd.testing.assert_frame_equal(first.prediction_index, second.prediction_index)
    assert len(first.clinical_observations) == 18
    assert len(first.wearable_daily) == 84
    assert (first.prediction_index["target_at"] > first.prediction_index["prediction_at"]).all()


def test_validation_rejects_out_of_range_measurement() -> None:
    tables = generate_synthetic_tables(SyntheticDataConfig(patient_count=3, seed=7))
    wearable = tables.wearable_daily.copy()
    wearable.loc[0, "steps"] = -1

    with pytest.raises(DataValidationError, match="wearable_daily.steps"):
        validate_tables(replace(tables, wearable_daily=wearable))


def test_feature_builder_uses_only_the_documented_14_day_window() -> None:
    tables = generate_synthetic_tables(SyntheticDataConfig(patient_count=3, seed=8))
    baseline = build_feature_table(tables)
    future = tables.wearable_daily.iloc[[0]].copy()
    future.loc[:, "recorded_on"] = tables.prediction_index.iloc[0]["prediction_at"] + pd.Timedelta(days=1)
    future.loc[:, "steps"] = 99_999
    wearable_with_future = pd.concat([tables.wearable_daily, future], ignore_index=True)

    actual = build_feature_table(replace(tables, wearable_daily=wearable_with_future))

    pd.testing.assert_frame_equal(baseline, actual)
    assert set(FEATURE_COLUMNS).issubset(baseline.columns)


def test_feature_builder_rejects_incomplete_wearable_window() -> None:
    tables = generate_synthetic_tables(SyntheticDataConfig(patient_count=3, seed=9))
    incomplete = tables.wearable_daily.iloc[1:].copy()

    with pytest.raises(DataValidationError, match="complete 14-day wearable window"):
        build_feature_table(replace(tables, wearable_daily=incomplete))


def test_patient_level_split_has_no_overlap() -> None:
    features = build_feature_table(generate_synthetic_tables(SyntheticDataConfig(patient_count=12, seed=10)))
    splits = split_by_patient(features, seed=22)
    train_ids = set(splits.train["patient_id"])
    validation_ids = set(splits.validation["patient_id"])
    test_ids = set(splits.test["patient_id"])

    assert not train_ids & validation_ids
    assert not train_ids & test_ids
    assert not validation_ids & test_ids
    assert train_ids | validation_ids | test_ids == set(features["patient_id"])


def test_prepare_data_writes_reproducible_processed_splits(tmp_path: pytest.TempPathFactory) -> None:
    source_dir = tmp_path / "source"
    processed_dir = tmp_path / "processed"
    tables = generate_synthetic_tables(SyntheticDataConfig(patient_count=10, seed=11))
    save_tables(tables, source_dir)

    counts = prepare_data(source_dir, processed_dir, seed=33)
    reloaded = load_tables(source_dir)

    validate_tables(reloaded)
    assert counts == {"features": 10, "train": 7, "validation": 1, "test": 2}
    assert (processed_dir / "features.csv").is_file()
    assert (processed_dir / "metadata.json").is_file()
