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
ax.plot(year, distance, "-o", lw=3)
ax.set_ylabel("Total distance (km)", fontsize=20, color="tab:blue")

ax2 = ax.twinx()
ax2.plot(year, winnerpace, "-o", color="tab:red", lw=3)
ax2.set_ylabel("Winner avg. pace (kph)", fontsize=20, color="tab:red")
ax.set_xlabel("Year", fontsize=20)
ax.grid("on")
ax.set_title("Tour de France 1903 - 2021", fontsize=20)
plt.savefig("../data/distanceAndPace.png", dpi=100)
