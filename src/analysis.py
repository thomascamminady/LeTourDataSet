# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# %%
df = pd.read_csv("../data/TDF_Riders_History.csv")

# %%
year = np.unique(df["Year"])
distance = df.groupby("Year").agg("mean")["Distance (km)"].values
nriders = df.groupby("Year").agg("count")["Rider"]
df["PersonalAvgPace"] = df["Distance (km)"] / (df["TotalSeconds"] / 3600)
df.loc[df["Year"] < 1915, "PersonalAvgPace"] = np.nan

winnerpace = df.groupby("Year").first()["PersonalAvgPace"]
meantime = df.groupby("Year").agg("mean")["TotalSeconds"]
meanpace = distance / meantime * 3600

# %%
matplotlib.rcParams.update({"font.size": 22})
fig, ax = plt.subplots(1, 1, figsize=(15, 7))
ax.scatter(year, distance)
ax.set_ylabel("Total distance (km)", fontsize=20, color="tab:blue")

ax2 = ax.twinx()
ax2.scatter(year, winnerpace, color="tab:red")
ax2.set_ylabel("Winner avg. pace (kph)", fontsize=20, color="tab:red")
ax.set_xlabel("Year", fontsize=20, color="gray")
ax.grid("on")
ax.set_title("Tour de France 1903 - 2021", fontsize=24, color="gray")
ax2.set_ylim(20, 45)
ax.set_ylim(1000, 6000)
ax2.set_yticks([25, 30, 35, 40])
ax2.set_yticklabels([25, 30, 35, 40], color="tab:red")
ax.set_yticks([2000, 3000, 4000, 5000])
ax.set_yticklabels([2000, 3000, 4000, 5000], color="tab:blue")
ax2.fill_betweenx([00, 412], 1939.5, 1946.5, zorder=-1, alpha=0.1, color="grey")
ax2.fill_betweenx([00, 412], 1914.5, 1918.5, zorder=-1, alpha=0.1, color="grey")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax.grid(which="major", axis="y", linestyle="-")
ax2.grid(which="major", axis="y", linestyle="-")
ax.set_xticks([1925, 1950, 1975, 2000])
ax.set_xticklabels([1925, 1950, 1975, 2000], color="gray")
ax.set_xlim(1900, 2023)
ax2.set_xlim(1900, 2023)
plt.savefig("../data/TDF_Distance_And_Pace.png", dpi=100)
