import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
import numpy as np
import logging
from rich.progress import track
from Plotter import Plotter


class Downloader:
    def __init__(
        self,
        history_page="https://www.letour.fr/en/history",
        headers={
            "Accept": "text/html",
            "User-Agent": "python-requests/1.2.0",
            "Accept-Charset": "utf-8",
            "accept-encoding": "deflate, br",
        },
    ) -> None:
        self._links: list[str] = self._get_urls(history_page, headers)

    def _get_urls(self, history_page: str, headers: dict[str, str]) -> list[str]:
        return [
            entry["data-tabs-ajax"]
            for entry in BeautifulSoup(
                requests.get(history_page, allow_redirects=True, headers=headers).text,
                "html.parser",
            ).find_all("button", {"class": "dateTabs__link"})
        ]

    def run(self, prefix="http://www.letour.fr") -> tuple[pd.DataFrame, pd.DataFrame]:
        stages_list: list[pd.DataFrame] = []
        rankings_list: list[pd.DataFrame] = []
        for link in track(self._links, "Downloading historical data..."):
            try:
                soup, year, distance = self._get_soup_year_distance(prefix + link)
                df_stage, df_ranking = self._cleanup(
                    self._get_stages(soup, year, distance),
                    self._get_rankings(soup),
                    year,
                    distance,
                )
                stages_list.append(df_stage)
                rankings_list.append(df_ranking)
            except Exception as e:
                logging.warn(link)
                logging.warn(e)

        df_stages = pd.concat(stages_list, ignore_index=True)
        df_rankings = pd.concat(rankings_list, ignore_index=True)

        return df_stages, df_rankings

    def _get_soup_year_distance(self, link: str) -> tuple[Tag, int, int]:
        result = requests.get(link, allow_redirects=True)
        text = result.text
        status = result.status_code
        logging.info(link + " ==> HTTP STATUS = " + str(status))

        soup = BeautifulSoup(text, "html.parser")
        year_tag = soup.find("h3")
        if year_tag is None:
            raise Exception("Could not parse year.")
        year = int(year_tag.text[-4:])
        distance = soup.select("[class~=statsInfos__number]")[1].contents
        distance = int(str(distance[0]).replace(" ", ""))
        return soup, year, distance

    def _get_stages(self, soup: Tag, year: int, distance: int) -> pd.DataFrame:
        select_tag = soup.find("select")
        if not isinstance(select_tag, Tag):
            raise Exception("Can't find `select`.")

        df_stages = pd.DataFrame(
            [[year, distance, option.text] for option in select_tag.find_all("option")],
            columns=["Year", "TotalTDFDistance", "Stage"],
        )
        return df_stages

    def _get_rankings(self, soup: Tag) -> pd.DataFrame:
        rankingTable = soup.find("table")
        df_rankings = pd.read_html(str(rankingTable))[0]
        return df_rankings

    def _cleanup(
        self,
        df_stages: pd.DataFrame,
        df_rankings: pd.DataFrame,
        year: int,
        distance: int,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_rankings["Year"] = year
        df_rankings["Distance (km)"] = distance
        df_rankings["Number of stages"] = len(df_stages)
        df_rankings["TotalSeconds"] = df_rankings["Times"].apply(
            lambda x: self._get_seconds(x, "Total")
        )
        df_rankings["GapSeconds"] = df_rankings["Gap"].apply(
            lambda x: self._get_seconds(x, "Gap")
        )

        # Fix result types
        df_rankings["ResultType"] = "time"
        null_years = [1905, 1906, 1908]
        df_rankings.loc[df_rankings["Year"].isin(null_years), "ResultType"] = "null"
        point_years = [1907, 1909, 1910, 1911, 1912]
        df_rankings.loc[df_rankings["Year"].isin(point_years), "ResultType"] = "points"

        if year in [2006, 1997]:
            tmp = df_rankings[df_rankings["Year"] == year].reset_index()
            ts = np.array(tmp["TotalSeconds"])
            gs = np.array(tmp["GapSeconds"])
            ts[1:] = ts[0] + gs[1:]
            df_rankings.loc[df_rankings["Year"] == year, "TotalSeconds"] = ts

        df_rankings.sort_values(["Year", "Rank"], axis=0, ascending=True, inplace=True)
        df_rankings = df_rankings.reset_index(drop=True)

        df_stages.sort_values(["Year", "Stage"], axis=0, ascending=True, inplace=True)
        df_stages = df_stages.reset_index(drop=True)
        return df_rankings, df_stages

    def _get_seconds(self, row: str, mode: str) -> int:
        val = sum(
            to_seconds * int(t)
            for to_seconds, t in zip(
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
            return 0
        else:
            return val


if __name__ == "__main__":
    downloader = Downloader()
    df_rankings, df_stages = downloader.run()
    df_rankings.to_csv("data/TDF_Riders_History.csv")
    df_stages.to_csv("data/TDF_Stages_History.csv")
    Plotter().plot(df_rankings)
