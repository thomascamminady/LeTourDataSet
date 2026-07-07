"""Tests for the CSV data-protection script's comparison logic."""

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT = (
    Path(__file__).parent.parent / ".github" / "scripts" / "check_csv_integrity.py"
)
spec = importlib.util.spec_from_file_location("check_csv_integrity", SCRIPT)
assert spec is not None and spec.loader is not None
integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity)


class TestCanonical:
    def test_integers_and_floats_agree(self) -> None:
        assert integrity._canonical("11.0") == integrity._canonical(11) == "11"

    def test_whitespace_trimmed(self) -> None:
        assert integrity._canonical("  POGACAR ") == "POGACAR"

    def test_missing_is_empty(self) -> None:
        assert integrity._canonical(float("nan")) == ""

    def test_true_float_kept(self) -> None:
        assert integrity._canonical("13.1") == integrity._canonical(13.1)


class TestCanonicalRows:
    def test_reordered_frames_are_equal(self) -> None:
        a = pd.DataFrame({"x": [1, 2], "y": ["a", "b"]})
        b = pd.DataFrame({"x": [2.0, 1.0], "y": ["b", "a "]})
        cols = ["x", "y"]
        assert integrity.canonical_rows(a, cols) == integrity.canonical_rows(b, cols)

    def test_modification_shows_as_missing_row(self) -> None:
        a = pd.DataFrame({"x": [1, 2]})
        b = pd.DataFrame({"x": [1, 3]})
        missing = integrity.canonical_rows(a, ["x"]) - integrity.canonical_rows(
            b, ["x"]
        )
        assert sum(missing.values()) == 1

    def test_added_rows_do_not_hide_modifications(self) -> None:
        old = pd.DataFrame({"x": [1, 2]})
        new = pd.DataFrame({"x": [1, 99, 4, 5]})  # 2 modified, rows added
        missing = integrity.canonical_rows(old, ["x"]) - integrity.canonical_rows(
            new, ["x"]
        )
        assert sum(missing.values()) == 1

    def test_duplicate_rows_are_counted(self) -> None:
        # Multisets: dropping one of two identical rows must be detected
        old = pd.DataFrame({"x": [7, 7]})
        new = pd.DataFrame({"x": [7]})
        missing = integrity.canonical_rows(old, ["x"]) - integrity.canonical_rows(
            new, ["x"]
        )
        assert sum(missing.values()) == 1
