import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Visualizer:
    def __init__(self) -> None:
        pass

    def plot(self, df: pd.DataFrame, saveas="data/TDF_Distance_And_Pace.png") -> None:
        last_year = 2024

        year = np.unique(df["Year"])
        distance = df.groupby("Year")["Distance (km)"].mean(numeric_only=True).values
        df["PersonalAvgPace"] = df["Distance (km)"] / (df["TotalSeconds"] / 3600)
        df.loc[df["Year"] < 1915, "PersonalAvgPace"] = np.nan
        winnerpace = df.groupby("Year").first()["PersonalAvgPace"]

        matplotlib.rcParams.update({"font.size": 22})
        _, ax = plt.subplots(1, 1, figsize=(15, 7))
        ax.scatter(year, distance)  # type:ignore

        ax.set_title(f"Tour de France 1903 - {last_year}", fontsize=24, color="gray")

        ax.set_xlabel("Year", fontsize=20, color="gray")
        ax.set_xlim(1900, last_year + 1)
        ax.set_xticks([1925, 1950, 1975, 2000])
        ax.set_xticklabels([1925, 1950, 1975, 2000], color="gray")

        ax.set_ylabel("Total distance (km)", fontsize=20, color="tab:blue")
        ax.set_ylim(1000, 6000)
        ax.set_yticks([2000, 3000, 4000, 5000])
        ax.set_yticklabels([2000, 3000, 4000, 5000], color="tab:blue")

        for where in ["top", "right", "bottom", "left"]:
            ax.spines[where].set_visible(False)
        ax.grid(True)
        ax.grid(which="major", axis="y", linestyle="-")

        ax_twinx = ax.twinx()
        ax_twinx.scatter(year, winnerpace, color="tab:red")
        args = {"zorder": -1, "alpha": 0.1, "color": "grey"}
        ax_twinx.fill_betweenx([00, 412], 1914.5, 1918.5, **args)
        ax_twinx.fill_betweenx([00, 412], 1939.5, 1946.5, **args)
        args = {"color": "darkgray", "fontsize": 13, "rotation": 90}
        ax_twinx.text(1915, 27, "WWI", **args)
        ax_twinx.text(1940, 27, "WWII", **args)

        ax_twinx.set_xlim(1900, last_year + 1)

        ax_twinx.set_ylabel("Winner avg. pace (kph)", fontsize=20, color="tab:red")
        ax_twinx.set_ylim(20, 45)
        ax_twinx.set_yticks([25, 30, 35, 40])
        ax_twinx.set_yticklabels([25, 30, 35, 40], color="tab:red")

        for where in ["top", "right", "bottom", "left"]:
            ax_twinx.spines[where].set_visible(False)

        ax_twinx.grid(which="major", axis="y", linestyle="-")
        plt.savefig(saveas, dpi=100)
