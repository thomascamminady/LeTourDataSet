"""Tests for the CSV postprocessor."""

from pathlib import Path

import pandas as pd
import pytest

from letourdataset.postprocessor import (
    RIDERS_SPEC,
    STAGES_SPEC,
    DataPostProcessor,
    FileSpec,
)


@pytest.fixture
def riders_csv(tmp_path: Path) -> Path:
    path = tmp_path / "riders.csv"
    pd.DataFrame(
        {
            "Rank": [2, 1, 10, 1],
            "Rider": ["B", "A", "J", "Z"],
            "Rider No.": [21.0, 11.0, None, 5.0],
            "Year": [2024, 2024, 2024, 2023],
        }
    ).to_csv(path, index=False)
    return path


def test_sorts_numerically_and_writes_integers(riders_csv: Path) -> None:
    DataPostProcessor().process_file(riders_csv, RIDERS_SPEC)

    text = riders_csv.read_text()
    assert "21.0" not in text, "float artifact left in output"

    df = pd.read_csv(riders_csv)
    assert df["Year"].tolist() == [2023, 2024, 2024, 2024]
    assert df["Rank"].tolist() == [1, 1, 2, 10]
    assert df["Rider"].tolist() == ["Z", "A", "B", "J"]


def test_missing_values_stay_missing(riders_csv: Path) -> None:
    DataPostProcessor().process_file(riders_csv, RIDERS_SPEC)
    df = pd.read_csv(riders_csv)
    assert df["Rider No."].isna().sum() == 1


def test_idempotent(riders_csv: Path) -> None:
    DataPostProcessor().process_file(riders_csv, RIDERS_SPEC)
    first = riders_csv.read_bytes()
    DataPostProcessor().process_file(riders_csv, RIDERS_SPEC)
    assert riders_csv.read_bytes() == first


def test_split_stage_numbers_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "stages.csv"
    pd.DataFrame(
        {
            "Year": [1934, 1934, 1934],
            "Stages": [13.2, 13.1, 1.0],
            "Start": ["C", "B", "A"],
        }
    ).to_csv(path, index=False)

    DataPostProcessor().process_file(path, STAGES_SPEC)

    text = path.read_text()
    assert "13.1" in text and "13.2" in text
    assert "1.0" not in text, "whole stage number written as float"
    df = pd.read_csv(path)
    assert df["Start"].tolist() == ["A", "B", "C"]


def test_non_integer_column_left_alone(tmp_path: Path) -> None:
    path = tmp_path / "riders.csv"
    pd.DataFrame({"Rank": ["1", "DSQ"], "Year": [2024, 2024]}).to_csv(
        path, index=False
    )
    DataPostProcessor().process_file(path, RIDERS_SPEC)
    df = pd.read_csv(path, dtype=str)
    assert set(df["Rank"]) == {"1", "DSQ"}


def test_missing_file_is_skipped(tmp_path: Path) -> None:
    DataPostProcessor().process_file(tmp_path / "nope.csv", RIDERS_SPEC)


def test_process_all_files_raises_on_broken_file(tmp_path: Path) -> None:
    (tmp_path / "men").mkdir()
    (tmp_path / "men" / "TDF_Riders_History.csv").write_text(
        'a,b\n1,"unclosed\n'
    )
    with pytest.raises(RuntimeError, match="TDF_Riders_History.csv"):
        DataPostProcessor(tmp_path).process_all_files()


def test_filespec_defaults() -> None:
    spec = FileSpec(sort_columns=("Year",))
    assert spec.integer_columns == ()
    assert spec.stage_number_columns == ()
