"""Smoke tests for the Visualizer."""

from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")

from letourdataset.visualizer import Visualizer  # noqa: E402


def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Year": [2022, 2022, 2023, 2023, 1907],
            "Rank": [1, 2, 1, 2, 1],
            "Distance (km)": [1029, 1029, 956, 956, 4488],
            "TotalSeconds": [96944, 97172, 92643, 93000, 0],
        }
    )


def test_plot_writes_png(tmp_path: Path) -> None:
    out = tmp_path / "plot.png"
    Visualizer().plot(sample_df(), saveas=str(out), title="Test")
    assert out.exists() and out.stat().st_size > 0


def test_plot_does_not_mutate_input(tmp_path: Path) -> None:
    df = sample_df()
    before = df.copy()
    Visualizer().plot(df, saveas=str(tmp_path / "plot.png"))
    pd.testing.assert_frame_equal(df, before)
