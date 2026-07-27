"""Tests for deriving the documented coverage from the CSV data."""

from pathlib import Path

import pandas as pd
import pytest

from letourdataset.coverage import MEN, WOMEN, RaceCoverage, load_coverage
from letourdataset.docsync import (
    render_docs_head,
    render_readme_coverage,
    replace_block,
    sync_all,
)


def _write_dataset(root: Path, men_years: list[int], women_years: list[int]) -> None:
    for subdir, name, years in (
        ("men", "TDF_Riders_History.csv", men_years),
        ("women", "TDFF_Riders_History.csv", women_years),
    ):
        (root / subdir).mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"Year": years, "Rank": range(1, len(years) + 1)}).to_csv(
            root / subdir / name, index=False
        )


class TestLoadCoverage:
    def test_derives_years_and_edition_count(self, tmp_path: Path) -> None:
        # Duplicated years are riders in the same edition, not extra editions
        _write_dataset(
            tmp_path, men_years=[1903, 1903, 1904, 2026], women_years=[2022, 2025]
        )
        coverage = load_coverage(tmp_path)
        men = coverage[MEN]
        assert (men.first_year, men.latest_year, men.editions) == (1903, 2026, 3)
        assert men.span_years == 123
        assert coverage[WOMEN].latest_year == 2025

    def test_missing_file_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Run 'make update'"):
            load_coverage(tmp_path)


class TestReplaceBlock:
    def test_replaces_only_between_markers(self) -> None:
        text = "keep\n<!-- coverage:start -->\nold\n<!-- coverage:end -->\ntail\n"
        assert replace_block(text, "new") == (
            "keep\n<!-- coverage:start -->\nnew\n<!-- coverage:end -->\ntail\n"
        )

    def test_missing_markers_raise(self) -> None:
        with pytest.raises(ValueError, match="markers"):
            replace_block("no markers here", "new")

    def test_body_with_backslash_is_literal(self) -> None:
        text = "<!-- coverage:start -->\nx\n<!-- coverage:end -->"
        assert r"a\b" in replace_block(text, r"a\b")

    def test_is_idempotent(self) -> None:
        text = "<!-- coverage:start -->\nold\n<!-- coverage:end -->"
        once = replace_block(text, "new")
        assert replace_block(once, "new") == once


class TestRenderers:
    @pytest.fixture
    def coverage(self) -> dict[str, RaceCoverage]:
        return {
            MEN: RaceCoverage("Men's Tour de France", 1903, 2027, 114),
            WOMEN: RaceCoverage("Women's Tour", 2022, 2026, 5),
        }

    def test_readme_names_both_races(self, coverage: dict[str, RaceCoverage]) -> None:
        out = render_readme_coverage(coverage)
        assert "1903 - 2027 (all 114 editions)" in out
        assert "2022 - 2026 (all editions since the relaunch)" in out

    def test_docs_head_uses_span_and_en_dashes(
        self, coverage: dict[str, RaceCoverage]
    ) -> None:
        out = render_docs_head(coverage)
        assert "124 years of race data" in out  # 2027 - 1903
        assert "(1903–2027)" in out and "(2022–2026)" in out
        assert out.startswith("<title>") and out.rstrip().endswith(">")


class TestSyncAll:
    def test_a_new_edition_propagates_to_both_files(self, tmp_path: Path) -> None:
        """The whole point: adding an edition updates the prose with no edits."""
        repo = tmp_path / "repo"
        (repo / "docs").mkdir(parents=True)
        (repo / "README.md").write_text(
            "intro\n<!-- coverage:start -->\nstale\n<!-- coverage:end -->\n",
            encoding="utf-8",
        )
        (repo / "docs" / "index.html").write_text(
            "<head>\n<!-- coverage:start -->\nstale\n<!-- coverage:end -->\n</head>\n",
            encoding="utf-8",
        )
        data = repo / "data"
        _write_dataset(data, men_years=[1903, 2026], women_years=[2022, 2025])

        changed = sync_all(repo, load_coverage(data))
        assert changed == {"README.md": True, "docs/index.html": True}
        assert "1903 - 2026" in (repo / "README.md").read_text(encoding="utf-8")
        assert "1903–2026" in (repo / "docs" / "index.html").read_text(encoding="utf-8")

        # Running again is a no-op, and check mode agrees
        assert sync_all(repo, load_coverage(data)) == {
            "README.md": False,
            "docs/index.html": False,
        }

        # A newer edition makes both files stale again
        _write_dataset(data, men_years=[1903, 2026, 2027], women_years=[2022, 2026])
        assert sync_all(repo, load_coverage(data), write=False) == {
            "README.md": True,
            "docs/index.html": True,
        }
        # write=False must not have touched anything
        assert "2027" not in (repo / "README.md").read_text(encoding="utf-8")
