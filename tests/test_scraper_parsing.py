"""Unit tests for the scraper's pure parsing logic (no network access)."""

from types import SimpleNamespace
from typing import Callable

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from letourdataset.scraper import Scraper, parse_stage_number


def _as_all_rankings(rankings: "pd.DataFrame") -> "pd.DataFrame":
    """Add the columns _cleanup sorts the all-rankings frame by."""
    df = rankings.copy()
    df["Stages"] = 1
    df["Ranking type"] = "Individual (Stage)"
    return df


def make_scraper() -> Scraper:
    """Create a Scraper without running __init__ (which hits the network)."""
    return object.__new__(Scraper)


class TestGetSeconds:
    def test_full_time(self) -> None:
        assert Scraper._get_seconds("76h 00' 32''", "Total") == 273632

    def test_gap_with_plus(self) -> None:
        assert Scraper._get_seconds("+ 00h 04' 24''", "Gap") == 264

    def test_dash_means_zero(self) -> None:
        assert Scraper._get_seconds("-", "Gap") == 0

    def test_nan_means_zero(self) -> None:
        assert Scraper._get_seconds(float("nan"), "Gap") == 0

    def test_unparseable_means_zero(self) -> None:
        assert Scraper._get_seconds("not a time", "Total") == 0

    def test_implausible_gap_is_dropped(self) -> None:
        # Gaps above 50 hours are parsing artefacts on the source pages
        assert Scraper._get_seconds("51h 00' 00''", "Gap") == 0

    def test_implausible_total_is_kept(self) -> None:
        assert Scraper._get_seconds("51h 00' 00''", "Total") == 51 * 3600


class TestParseStageNumber:
    def test_regular_stage(self) -> None:
        assert parse_stage_number("Stage 1 : Paris > Lyon", 1903) == 1

    def test_split_stage(self) -> None:
        assert parse_stage_number("Stage 13.1 : A > B", 1934) == 13.1

    def test_prologue(self) -> None:
        assert parse_stage_number("Prologue : Nice > Nice", 1981) == 0

    def test_unparseable(self) -> None:
        assert parse_stage_number("garbage", 2000) is None


class TestYearPageParsing:
    """Parse a saved letourfemmes.fr 2025 year page."""

    @pytest.fixture
    def soup(self, load_fixture: Callable[[str], str]) -> BeautifulSoup:
        return BeautifulSoup(
            load_fixture("women_2025_year_page.html.gz"), "html.parser"
        )

    def test_get_stages(self, soup: BeautifulSoup) -> None:
        df = make_scraper()._get_stages(soup, 2025, 1169)
        assert list(df.columns) == [
            "Year",
            "TotalTDFDistance",
            "Stages",
            "Start",
            "End",
        ]
        assert len(df) == 9
        assert df["Stages"].tolist() == list(range(1, 10))
        assert df["Start"].iloc[0] == "Vannes"
        assert df["End"].iloc[0] == "Plumelec"

    def test_get_rankings(self, soup: BeautifulSoup) -> None:
        df = make_scraper()._get_rankings(soup)
        assert len(df) == 124
        assert df["Rider"].iloc[0] == "PAULINE FERRAND PREVOT"
        # Bib numbers are scraped separately and attached as 'Rider No.'
        assert df["Rider No."].notna().all()

    def test_year_and_distance_markup(self, soup: BeautifulSoup) -> None:
        year_tag = soup.find("h3")
        assert year_tag is not None
        assert int(year_tag.text[-4:]) == 2025


class TestParseRankingRows:
    def test_individual_stage_ranking(self, load_fixture: Callable[[str], str]) -> None:
        rows = Scraper._parse_ranking_rows(
            load_fixture("women_2025_stage5_individual.html.gz"),
            5,
            "Individual (Stage)",
            "ite",
        )
        assert len(rows) > 100
        first = rows[0]
        assert first["Rank"] == "1"
        assert first["Stages"] == 5
        assert first["Ranking type"] == "Individual (Stage)"
        assert "h" in first["Times"]

    def test_points_ranking_has_checkpoints(
        self, load_fixture: Callable[[str], str]
    ) -> None:
        """Regression test: the checkpoint used to be reset for every row,
        so the Checkpoint column was always None."""
        rows = Scraper._parse_ranking_rows(
            load_fixture("women_2025_stage5_points.html.gz"),
            5,
            "Points (Stage)",
            "ipe",
        )
        assert rows
        checkpoints = {row["Checkpoint"] for row in rows}
        assert checkpoints - {None}, "no checkpoint captured from the page"
        # Every row after the first checkpoint header carries a checkpoint
        assert all(row["Checkpoint"] is not None for row in rows)

    def test_empty_page_gives_no_rows(self) -> None:
        assert Scraper._parse_ranking_rows("<html></html>", 1, "x", "ite") == []


class TestFinalGeneralClassificationFallback:
    """A just-finished edition has an empty GC table on its year page, so the
    GC is read off the general ranking after the final stage instead."""

    def test_year_page_gc_table_is_empty(
        self, load_fixture: Callable[[str], str]
    ) -> None:
        soup = BeautifulSoup(load_fixture("men_2026_year_page.html.gz"), "html.parser")
        assert make_scraper()._get_rankings(soup).empty

    def test_fallback_reads_the_official_gc(
        self,
        load_fixture: Callable[[str], str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scraper = make_scraper()
        scraper._headers = {}
        requested: list[str] = []

        def fake_get(url: str, **kwargs: object) -> SimpleNamespace:
            requested.append(url)
            return SimpleNamespace(
                text=load_fixture("men_2026_final_general.html.gz"),
                raise_for_status=lambda: None,
            )

        monkeypatch.setattr("letourdataset.scraper.requests.get", fake_get)

        stages = pd.DataFrame({"Stages": [0, 1, 2, 21]})
        df = scraper._get_general_classification("http://x/ranking", stages, 2026)

        # The last stage is queried, as an integer and as the general ranking
        assert requested == ["http://x/ranking?stage=21&type=itg"]
        assert list(df.columns) == [
            "Rank",
            "Rider",
            "Rider No.",
            "Team",
            "Times",
            "Gap",
            "B",
            "P",
        ]
        assert len(df) == 158
        winner = df.iloc[0]
        assert winner["Rank"] == 1
        assert winner["Rider"] == "TADEJ POGACAR"
        assert winner["Times"] == "73h 56' 26''"
        # Bib numbers only exist on the ranking rows, not in the table cells
        assert winner["Rider No."] == 1

    def test_no_stages_gives_empty_frame(self) -> None:
        scraper = make_scraper()
        empty = pd.DataFrame({"Stages": pd.Series(dtype=float)})
        assert scraper._get_general_classification("http://x", empty, 2026).empty


class TestNonTimeEditionsHaveZeroedSeconds:
    """1907-1912 were decided on points and the source prints placeholder
    times (47h, 66h, 74h, ... for a race that actually took ~158h), so the
    derived seconds must stay 0 while the raw strings are kept."""

    def test_points_edition_seconds_are_zeroed(self) -> None:
        scraper = make_scraper()
        rankings = pd.DataFrame(
            {
                "Rank": [1, 2],
                "Rider": ["A", "B"],
                "Times": ["47h 00' 00''", "66h 00' 00''"],
                "Gap": ["-", "+ 19h 00' 00''"],
            }
        )
        stages = pd.DataFrame(
            {"Year": [1907], "Stages": [1], "Start": ["x"], "End": ["y"]}
        )
        out, _, _ = scraper._cleanup(
            stages, rankings, _as_all_rankings(rankings), 1907, 4488
        )
        assert (out["ResultType"] == "points").all()
        assert (out["TotalSeconds"] == 0).all()
        assert (out["GapSeconds"] == 0).all()
        # The scraped strings are left untouched
        assert out["Times"].tolist() == ["47h 00' 00''", "66h 00' 00''"]

    def test_time_edition_seconds_are_kept(self) -> None:
        scraper = make_scraper()
        rankings = pd.DataFrame(
            {
                "Rank": [1],
                "Rider": ["A"],
                "Times": ["73h 56' 26''"],
                "Gap": ["-"],
            }
        )
        stages = pd.DataFrame(
            {"Year": [2026], "Stages": [1], "Start": ["x"], "End": ["y"]}
        )
        out, _, _ = scraper._cleanup(
            stages, rankings, _as_all_rankings(rankings), 2026, 3333
        )
        assert out["ResultType"].iloc[0] == "time"
        assert out["TotalSeconds"].iloc[0] == 73 * 3600 + 56 * 60 + 26
