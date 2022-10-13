# %% [markdown]
# # LeTour data set
# This file downloads raw data about every rider of every Tour de France (from 1903 up to 2021). This data will then be postprocessed and stored in CSV format.
# Executing this notebook might take some minutes.
# %% [markdown]
# ## 1) Retrieve urls for data extract
# First we generate the urls that we need to download the raw HTML pages from the `letour.fr` website to work offline from here on. The dataframe dflink will stores the respective url for each year.
# Take a look at `view-source:https://www.letour.fr/en/history` (at around line 1143-1890).

# %%
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

# %%
PREFIX = "http://www.letour.fr"
HISTORYPAGE = "https://www.letour.fr/en/history"
# %%
headers = {
    "Accept": "text/html",
    "User-Agent": "python-requests/1.2.0",
    "Accept-Charset": "utf-8",
    "accept-encoding": "deflate, br",
}
# %%
resulthistpage = requests.get(HISTORYPAGE, allow_redirects=True, headers=headers)
souphistory = BeautifulSoup(resulthistpage.text, "html.parser")
# %%
# Find select tag for histo links
select_tag_histo = souphistory.find_all("button", {"class": "dateTabs__link"})
LH = [x["data-tabs-ajax"] for x in select_tag_histo]
dflink = pd.DataFrame({"TDFHistorylink": LH})
dflink
# %% [markdown]
# ## 2) Get data from HTML pages and convert results to dataframes
# %% [markdown]
# ### 2.1) Create function that convert HHh mm' ss'' to seconds
# %%
def calcTotalSeconds(row, mode):
    val = sum(
        x * int(t)
        for x, t in zip(
            [3600, 60, 1],
            row.replace("h", ":")
            .replace("'", ":")
            .replace('"', ":")
            .replace(" ", "")
            .replace("+", "")
            .replace("-", "0")
            .split(":"),
        )
    )

    if (mode == "Gap") and val > 180000:
        val = 0

    return val


# %% [markdown]
# ### 2.2) Create a function that will retrieve elements from a source HTML page located on an input url

# %%
def getstagesNrank(i_url):
    resultfull = requests.get(i_url, allow_redirects=True)
    result = resultfull.text
    resultstatus = resultfull.status_code

    print(i_url + " ==> HTTP STATUS = " + str(resultstatus))

    soup = BeautifulSoup(result, "html.parser")
    h = soup.find("h3")
    year = int(h.text[-4:])

    # Find select tag
    select_tag = soup.find("select")

    # find all option tag inside select tag
    options = select_tag.find_all("option")

    cols = ["Year", "TotalTDFDistance", "Stage"]
    lst = []

    # search for stages
    distance = soup.select("[class~=statsInfos__number]")[1].contents

    # search for distance of the TDF edition
    for option in options:
        lst.append([year, int(distance[0].replace(" ", "")), option.text])

    dfstages = pd.DataFrame(lst, columns=cols)

    # Find select tag for ranking racers
    rankingTable = soup.find("table")

    dfrank = pd.read_html(str(rankingTable))[0]

    dfrank["Year"] = year
    dfrank["Distance (km)"] = int(distance[0].replace(" ", ""))
    dfrank["Number of stages"] = len(dfstages)
    dfrank["TotalSeconds"] = dfrank["Times"].apply(
        lambda x: calcTotalSeconds(x, "Total")
    )
    dfrank["GapSeconds"] = dfrank["Gap"].apply(lambda x: calcTotalSeconds(x, "Gap"))

    return dfstages, dfrank


# %% [markdown]
# ### 2.3) Loop on the dflink dataframe to get data from each url source

# %%
dfstagesres = []
dfstagesrestmp = []
dfrankres = []
dfrankrestmp = []
dfrankoutput = []

for index, row in dflink.iterrows():
    url = PREFIX + row["TDFHistorylink"]
    try:
        # if index >= 12 :  # limit from 1919 (data need to be cleaned a little bit more before that)
        if index >= 0:  # I prefer to keep the old data for consistency.
            dfstagesres, dfrankres = getstagesNrank(url)
            dfstagesrestmp = dfstagesres.append(dfstagesrestmp, ignore_index=True)
            dfrankrestmp = dfrankres.append(dfrankrestmp, ignore_index=True)

    except:
        raise


dfstageoutput = dfstagesrestmp
dfrankoutput = dfrankrestmp

# %% [markdown]
# ## 3) Clean up the data
#

# %%
# Fix result types
dfrankoutput["ResultType"] = "time"
dfrankoutput.loc[dfrankoutput["Year"].isin([1905, 1906, 1908]), "ResultType"] = "null"
dfrankoutput.loc[
    dfrankoutput["Year"].isin([1907, 1909, 1910, 1911, 1912]), "ResultType"
] = "points"


# %%
# Fix this weird bug for e.g. year 2006 and 1997
for year in np.unique(dfrankoutput["Year"]):
    tmp = dfrankoutput[dfrankoutput["Year"] == year].reset_index()
    if tmp.loc[0]["TotalSeconds"] > tmp.loc[2]["TotalSeconds"]:
        print(year)
# Okay seems to be only for 2006 and 1997


# %%
tmp = dfrankoutput[dfrankoutput["Year"] == 2006].reset_index()
ts = np.array(tmp["TotalSeconds"])
gs = np.array(tmp["GapSeconds"])
ts[1:] = ts[0] + gs[1:]

dfrankoutput.loc[dfrankoutput["Year"] == 2006, "TotalSeconds"] = ts

tmp = dfrankoutput[dfrankoutput["Year"] == 1997].reset_index()
ts = np.array(tmp["TotalSeconds"])
gs = np.array(tmp["GapSeconds"])
ts[1:] = ts[0] + gs[1:]

dfrankoutput.loc[dfrankoutput["Year"] == 1997, "TotalSeconds"] = ts

# %% [markdown]
# ## 4) Write Data to CSV

# %%
dfrankoutput.sort_values(["Year", "Rank"], axis=0, ascending=True, inplace=True)
dfrankoutput = dfrankoutput.reset_index(drop=True)
dfrankoutput.to_csv("../data/TDF_Riders_History.csv")


# %%
dfstageoutput.sort_values(["Stage"], axis=0, ascending=False, inplace=True)

dfstageoutput.sort_values(["Year", "Stage"], axis=0, ascending=True, inplace=True)
dfstageoutput = dfstageoutput.reset_index(drop=True)
dfstageoutput.to_csv("../data/TDF_Stages_History.csv")

# %%
