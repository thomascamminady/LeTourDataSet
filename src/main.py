# %% [markdown]
# # LeTour data set
# This file downloads raw data about every rider of every Tour de France (up to including 2019). This data will then be postprocessed and stored in CSV format.
# Executing this notebook might take some minutes.
# %% [markdown]
# ## 1) Downloading pages in html format
# First we download the raw HTML pages from the `letour.fr` website to work offline from here on. The file `domainendings.txt` stores the respective website for each year, taken with a regular expression from `view-source:https://www.letour.fr/en/history` (at around line 1050-1790).

# %%
import os
import subprocess
import numpy as np
import re
import pandas as pd
from pathlib import Path

folder = "rawhtml"
Path(folder).mkdir(parents=True,
                   exist_ok=True)  # Create the directory if it does not exist
prefix = 'letour.fr'

# %%
with open(
        "endings/domainendings.txt", "r"
) as ins:  # Iterate over each year and use w3m to download t he content in HTML format
    for id, line in enumerate(ins):
        url = prefix + line
        output = folder + '/id_' + str(id) + '.txt'
        mycommand = 'w3m -dump -cols 1000 ' + url
        result = subprocess.check_output(mycommand, shell=True)

        file = open(output, "w")
        file.write(result.decode('utf-8'))
        file.close

# %% [markdown]
# ## 2) Clean up the data
#

# %%
keywords = [
    "Tour de France", "TDF", "Number of stages", "Distance (km)",
    "Average speed"
]
summary = {}
for file in os.listdir(folder):
    if file.endswith(".txt"):
        with open(folder + "/" + file, 'r') as f:
            content = f.read()
            text = re.search(r'Rank .*?(Next rankings|Race)', content,
                             re.DOTALL).group()
            x = ("\n".join(text.split("\n")[1:-1]))
            for i in range(len(text.split("\n"))):
                if i == 0:
                    cols = [
                        "Rank", "Rider", "Rider No.", "Team", "Times", "Gap",
                        "B"
                    ]
                    df = pd.DataFrame(columns=cols)
                else:
                    compressed = [
                        y.strip(" ") for y in text.split("\n")[i].split("  ")
                        if not y == ""
                    ]
                    if len(compressed) == 0:
                        break
                    if len(compressed) < 7:
                        compressed.append("")
                    df.loc[len(df)] = compressed
        with open(folder + "/" + file, 'r') as f:
            lines = f.readlines()
            metakws = []
            for line in lines[:10]:
                for kw in keywords:
                    if kw in line:
                        metakws.append(
                            line[len(kw):].strip("\n").strip(" ").replace(
                                " ", "").replace("PROLOGUE", ""))

            if len(metakws) == 3:
                metakws.append(np.NaN)  # Sotimes the avg pace is missing
            year = int(metakws[0][:4])
            nstages = metakws[1]
            if "+" in nstages:
                nstages = int(nstages[:2]) + 1  # Prologue was counted extra
            else:
                nstages = int(nstages)
            subdict = {
                'nstages': nstages,
                "distance (km)": int(metakws[2]),
                "average speed (kph)": float(metakws[3]),
                "results": df
            }
            summary[year] = subdict
summary = dict(sorted(summary.items()))

# %%
df = pd.DataFrame(columns=[
    "Year", "Rank", "Rider", "Rider No.", "Team", "Times", "Gap", "B", "P"
])
for key in summary:
    tmp = summary[key]["results"]
    tmp["Year"] = key
    if key in [1907, 1909, 1910, 1911, 1912]:
        f = lambda x: x["Times"].split("h")[0]
        tmp["P"] = tmp.apply(f, axis=1)
        tmp["Times"] = np.NaN
        tmp["Gap"] = np.NaN
    else:
        tmp["P"] = np.NaN
    tmp["Distance (km)"] = summary[key]["distance (km)"]
    tmp["No. Stages"] = summary[key]["nstages"]
    tmp["Listed Avg. Speed (kph)"] = summary[key]["average speed (kph)"]

    df = df.append(tmp)

# %%
# Fix result types
df["ResultType"] = "time"
df.loc[df["Year"].isin([1905, 1906, 1908]), "ResultType"] = "null"
df.loc[df["Year"].isin([1907, 1909, 1910, 1911, 1912]),
       "ResultType"] = "points"

# %%
# Split up time
df = df.reset_index()
df["Times"].apply(lambda x: re.sub('[^0-9]', ' ', str(x)).split("  "))
df["Hours"] = np.NaN
df["Minutes"] = np.NaN
df["Seconds"] = np.NaN

for i in range(len(df)):
    x = df.loc[i, "Times"]
    z = (re.sub('[^0-9]', ' ', str(x)).split("  "))
    if len(z) == 4:
        z = [int(zi) for zi in z[:3]]
    if len(z) < 3:
        z = [np.NaN, np.NaN, np.NaN]
    df.loc[i, "Hours"] = z[0]
    df.loc[i, "Minutes"] = z[1]
    df.loc[i, "Seconds"] = z[2]
df["TotalSeconds"] = df["Hours"] * 3600 + df["Minutes"] * 60 + df["Seconds"]

# %%
# Fix this weird bug for e.g. year 2006
for year in np.unique(df["Year"]):
    tmp = df[df["Year"] == year].reset_index()
    if tmp.loc[0]["TotalSeconds"] > tmp.loc[1]["TotalSeconds"]:
        print(year)
# Okay seems to be only for 2006
tmp = df[df["Year"] == 2006].reset_index()
ts = np.array(tmp["TotalSeconds"])
ts[1:] += ts[0]
h = ts // 3600
m = (ts - (h * 3600)) // 60
s = (ts - (h * 3600) - m * 60)

df.loc[df["Year"] == 2006, "Hours"] = h
df.loc[df["Year"] == 2006, "Minutes"] = m
df.loc[df["Year"] == 2006, "Seconds"] = s
df.loc[df["Year"] == 2006, "TotalSeconds"] = ts

# %%
# Get speed
df["kph"] = df["Distance (km)"] / df["TotalSeconds"] * 3600
df["kph"] = np.round(df["kph"], 3)

# %%
# Convert to int
cats = ["Hours", "Minutes", "Seconds", "TotalSeconds"]
for cat in cats:
    df[cat] = pd.Series(df[cat], dtype=pd.Int64Dtype())

# %%
# Rearrange
df = df.drop(columns=list(df)[:1])
df = df.rename(
    columns={
        "Rider No.": "RiderNumber",
        "Times": "Time",
        "Distance (km)": "DistanceKilometer",
        "B": "Bonus",
        "P": "Points",
        "No. Stages": "NumberStages",
        "Listed Avg. Speed (kph)": "ListedAvgPace",
        "kph": "PersonalAvgPace"
    })
df = df[[
    "Year",
    "Rider",
    "Rank",
    "Time",
    "DistanceKilometer",
    "PersonalAvgPace",
    "Hours",
    "Minutes",
    "Seconds",
    "Team",
    "RiderNumber",
    "TotalSeconds",
    "Gap",
    "Bonus",
    "Points",
    "NumberStages",
    "ListedAvgPace",
]]

# %%
df.to_csv("../data/riders.csv")

# %%
