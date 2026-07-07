import matplotlib.pyplot as plt
import pandas as pd

DISTANCE_COLOR = "tab:blue"
PACE_COLOR = "tab:red"
MARGIN_COLOR = "tab:red"
WAR_PERIODS = ((1914.5, 1918.5, "WWI"), (1939.5, 1946.5, "WWII"))

# (value in minutes, human-readable label) candidates for the log axis
MARGIN_TICKS = (
    (10 / 60, "10 s"),
    (1, "1 min"),
    (10, "10 min"),
    (60, "1 h"),
    (600, "10 h"),
    (3000, "50 h"),
)


def _format_margin(gap_seconds: int) -> str:
    if gap_seconds < 120:
        return f"{gap_seconds} seconds"
    return f"{gap_seconds // 60} minutes"


def _format_margin_short(gap_seconds: int) -> str:
    """Cycling-style compact notation, e.g. 3'48'' or 8''."""
    minutes, seconds = divmod(gap_seconds, 60)
    if minutes == 0:
        return f"{seconds}''"
    return f"{minutes}'{seconds:02d}''"


class Visualizer:
    def plot(self, df: pd.DataFrame, saveas: str, title: str | None = None) -> None:
        """Plot the total distance and the winner's average pace per year.

        Args:
            df: A riders-history dataframe (one row per rider and year).
            saveas: Path of the PNG file to write.
            title: Plot title; derived from the year range if omitted.
        """
        data = df.copy()
        data["Rank"] = pd.to_numeric(data["Rank"], errors="coerce")
        # Pace is undefined for editions without recorded times
        # (ResultType 'points' / 'no-results' have TotalSeconds == 0).
        data["PersonalAvgPace"] = (
            data["Distance (km)"] / (data["TotalSeconds"] / 3600)
        ).mask(data["TotalSeconds"] <= 0)

        distance = data.groupby("Year")["Distance (km)"].mean().sort_index()
        winners = (
            data.dropna(subset=["Rank"])
            .sort_values("Rank", kind="stable")
            .groupby("Year")
            .head(1)
        )
        winner_pace = winners.set_index("Year")["PersonalAvgPace"].sort_index()

        year_min = int(distance.index.min())
        year_max = int(distance.index.max())
        if title is None:
            title = f"Tour de France {year_min} - {year_max}"

        pace_max = float(winner_pace.max()) * 1.4
        distance_max = float(distance.max()) * 1.1

        with plt.rc_context({"font.size": 22}):
            fig, ax = plt.subplots(1, 1, figsize=(15, 7))
            ax.scatter(distance.index, distance.to_numpy(), color=DISTANCE_COLOR)

            ax.set_title(title, fontsize=24, color="gray")
            ax.set_xlabel("Year", fontsize=20, color="gray")
            ax.set_xlim(year_min - 2, year_max + 2)
            ax.tick_params(axis="x", colors="gray")

            ax.set_ylabel("Total distance (km)", fontsize=20, color=DISTANCE_COLOR)
            ax.set_ylim(0, distance_max)
            ax.tick_params(axis="y", colors=DISTANCE_COLOR)

            ax_twinx = ax.twinx()
            ax_twinx.scatter(
                winner_pace.index, winner_pace.to_numpy(), color=PACE_COLOR
            )
            for start, end, label in WAR_PERIODS:
                if start < year_max and end > year_min:
                    ax_twinx.axvspan(start, end, zorder=-1, alpha=0.1, color="grey")
                    ax_twinx.text(
                        start + 0.5,
                        pace_max * 0.45,
                        label,
                        color="darkgray",
                        fontsize=13,
                        rotation=90,
                    )

            ax_twinx.set_xlim(year_min - 2, year_max + 2)
            ax_twinx.set_ylabel(
                "Winner avg. pace (kph)", fontsize=20, color=PACE_COLOR
            )
            ax_twinx.set_ylim(0, pace_max)
            ax_twinx.tick_params(axis="y", colors=PACE_COLOR)

            for axis in (ax, ax_twinx):
                for side in ("top", "right", "bottom", "left"):
                    axis.spines[side].set_visible(False)
            # Only one y-grid; two would draw near-duplicate lines
            ax.grid(which="major", axis="y", linestyle="-")

            fig.savefig(saveas, dpi=100)
            plt.close(fig)

    def plot_winning_margin(
        self, df: pd.DataFrame, saveas: str, title: str | None = None
    ) -> None:
        """Plot the winner's margin over the runner-up per year (log scale).

        Args:
            df: A riders-history dataframe (one row per rider and year).
            saveas: Path of the PNG file to write.
            title: Plot title; derived from the year range if omitted.
        """
        data = df.copy()
        data["Rank"] = pd.to_numeric(data["Rank"], errors="coerce")
        runner_up = data[
            (data["ResultType"] == "time")
            & (data["Rank"] == 2)
            & (data["GapSeconds"] > 0)
        ]
        margin_minutes = (
            runner_up.groupby("Year")["GapSeconds"].min().sort_index() / 60.0
        )

        year_min = int(margin_minutes.index.min())
        year_max = int(margin_minutes.index.max())
        if title is None:
            title = f"Winning margin, {year_min} - {year_max}"

        with plt.rc_context({"font.size": 22}):
            fig, ax = plt.subplots(1, 1, figsize=(15, 7))
            ax.scatter(
                margin_minutes.index, margin_minutes.to_numpy(), color=MARGIN_COLOR
            )
            ax.set_yscale("log")

            low = float(margin_minutes.min())
            high = float(margin_minutes.max())
            ticks = [
                (value, label)
                for value, label in MARGIN_TICKS
                if low * 0.5 <= value <= high * 2
            ]
            ax.set_yticks([value for value, _ in ticks])
            ax.set_yticklabels([label for _, label in ticks])
            ax.tick_params(axis="y", colors="gray", which="both")
            ax.set_yticks([], minor=True)

            ax.set_title(title, fontsize=24, color="gray")
            ax.set_xlabel("Year", fontsize=20, color="gray")
            ax.set_xlim(year_min - 2, year_max + 2)
            ax.tick_params(axis="x", colors="gray")

            if len(margin_minutes) <= 10:
                # Sparse data: log ticks don't bracket a handful of points
                # well, so label every point directly instead
                for year, value in margin_minutes.items():
                    ax.annotate(
                        _format_margin_short(int(round(value * 60))),
                        xy=(year, value),
                        xytext=(0, 14),
                        textcoords="offset points",
                        ha="center",
                        color="darkgray",
                        fontsize=14,
                    )
                ax.set_ylim(float(margin_minutes.min()) * 0.4,
                            float(margin_minutes.max()) * 3)

            # Call out the closest race on record (only when there is room)
            if year_max - year_min >= 20:
                closest_year = int(margin_minutes.idxmin())
                closest = margin_minutes.min()
                gap_seconds = int(round(closest * 60))
                ax.annotate(
                    f"{closest_year}: {_format_margin(gap_seconds)}",
                    xy=(closest_year, closest),
                    xytext=(closest_year - (year_max - year_min) * 0.12, closest * 3),
                    color="darkgray",
                    fontsize=13,
                    arrowprops={"arrowstyle": "->", "color": "darkgray"},
                )

            for side in ("top", "right", "bottom", "left"):
                ax.spines[side].set_visible(False)
            ax.grid(which="major", axis="y", linestyle="-", alpha=0.5)

            fig.savefig(saveas, dpi=100)
            plt.close(fig)
