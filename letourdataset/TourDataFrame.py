from abc import ABC, abstractmethod
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import numpy as np


class AbstractTourDataFrame(ABC):
    def __init__(self, url: str) -> None:
        self._url = url
        self._encoding = "UTF-8"
        self._df = self._parse()
        self._post_process()

    @abstractmethod
    def _parse(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def _post_process(self) -> None:
        pass


class GenericEasyToParseDataFrame(AbstractTourDataFrame):
    """These are sites that can simply be parsed by calling pd.read_html()"""

    def _parse(self) -> pd.DataFrame:
        # Note that calling pd.read_html(self._url) does not work, because
        # we will get a 403 error eventually.
        _website = requests.get(self._url).text
        return pd.read_html(_website, encoding=self._encoding)[0]

    def _post_process(self) -> None:
        pass


class RankingsDataFrame(GenericEasyToParseDataFrame):
    pass


class StagesDataFrame(GenericEasyToParseDataFrame):
    def _post_process(self) -> None:
        self._df["Date"] = pd.to_datetime(self._df["Date"], dayfirst=True)


class JerseyWearersDataFrame(GenericEasyToParseDataFrame):
    pass


class StageWinnersDataFrame(GenericEasyToParseDataFrame):
    def _post_process(self) -> None:
        self._df["Start"] = self._df["Parcours"].apply(
            lambda _: _.split(">")[0].strip()
        )
        self._df["Finish"] = self._df["Parcours"].apply(
            lambda _: _.split(">")[1].strip()
        )
        self._df["Rider"] = self._df["Winner of stage"].apply(
            lambda _: _.split("(")[0].strip()
        )
        self._df["Team"] = self._df["Winner of stage"].apply(
            lambda _: _.split("(")[1].strip(")")
        )


class StartersDataFrame(AbstractTourDataFrame):
    """Starters data is a bit more complicated, because it is not a table."""

    def _parse(self) -> pd.DataFrame:
        html = urlopen(self._url).read()
        soup = BeautifulSoup(html, features="lxml")
        table = soup.findChildren("table")[0]
        starters: list[dict[str, str]] = []
        team_name = ""
        for tr in table.find_all("tr"):
            if tr.find("th") is not None:
                team_name = tr.find("th").text.strip()

            else:
                rider = tr.find_all("td")[2]
                country_code = str(rider.find("span")).split("flag--")[-1].split('"')[0]
                rider_name = str(rider.text.strip())
                starters.append(
                    {
                        "Team": team_name,
                        "Rider": rider_name,
                        "Country": country_code.upper(),
                    }
                )
        return pd.DataFrame(starters)

    def _post_process(self) -> None:
        pass


class TourInfoDataFrame(AbstractTourDataFrame):
    """Tour infos can be taken from the starting url directly."""

    def _parse(self) -> pd.DataFrame:
        content = BeautifulSoup(urlopen(self._url).read(), "html.parser")
        stats_infos = content.find_all("div", {"class": "statsInfos__item"})
        div_content = [div.text for div in stats_infos]

        info_dict = {
            line.strip().split("\n")[0]: self.to_numeric(
                line.strip().split("\n")[1].replace(" ", "")
            )
            for line in div_content
        }
        which_tour = content.find("h3", {"class": "heading heading--3"})
        if which_tour is not None:
            info_dict["Year"] = self.to_numeric(which_tour.text.split(" ")[-1])
            df = pd.DataFrame(info_dict, index=[0])
            return df
        else:
            raise ValueError("No Tour Info found")

    def _post_process(self) -> None:
        pass

    def get_year(self) -> int:
        if isinstance(y := self._df["Year"].values[0], np.int64):
            return int(y)
        else:
            return -1

    def to_numeric(self, s: str) -> int | float:
        try:
            return int(s)
        except ValueError:
            return float(s)
