from abc import ABC, abstractmethod
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import numpy as np
import re
from typing import Literal


class AbstractTourDataFrame(ABC):
    def __init__(self, url: str, year: int | None) -> None:
        self._url = url
        self._encoding = "UTF-8"
        self._df = self._parse()
        self._year = year
        if year and ("Year" not in self._df.columns):
            self._df["Year"] = year
        self._post_process()

    def get_df(self) -> pd.DataFrame:
        return self._df

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
    def _post_process(self) -> None:
        if self._df["Year"][0] == 1997:
            self._bugfix_year_1997()

        if self._df["Year"][0] == 2006:
            self._bugfix_year_2006()

        self._df["Duration (seconds)"] = self._df["Times"].apply(
            self._convert_string_to_seconds
        )
        self._df["Gap (seconds)"] = self._df["Gap"].apply(
            self._convert_string_to_seconds
        )

        self._df["Result type"] = self._df["Year"].apply(self._result_type)

    def _bugfix_year_1997(self) -> None:
        # Year 1997 has a bug where the hours are >100,
        # but except for the first two riders, the 1 is missing
        # and the hours are listed as 00h ... instead of 100h ...
        #
        # data looks like this:
        # 5883	1	JAN ULLRICH	8	TEAM DEUTSCHE TELEKOM	100h 30' 35''	-	NaN	NaN	361835	0	1997
        # 5884	2	RICHARD VIRENQUE	11	FESTINA Watches	100h 39' 44''	+ 00h 09' 09''	NaN	NaN	362384	549	1997
        # 5885	3	MARCO PANTANI	181	MERCATONE-UNO	00h 23' 12''	+ 00h 14' 03''	NaN	NaN	1392	843	1997
        # 5886	4	ABRAHAM OLANO	151	BANESTO	00h 25' 04''	+ 00h 15' 55''	NaN	NaN	1504	955	1997

        self._df["Times"] = self._df["Times"].apply(
            lambda x: "1" + x if x[0] == "0" else x
        )

    def _bugfix_year_2006(self) -> None:
        # The "Times" column is the "Gap" column

        self._df.loc[0, "Gap"] = "-"
        gaps_in_seconds = self._df["Gap"].apply(self._convert_string_to_seconds)
        times_in_seconds = self._df["Times"].apply(self._convert_string_to_seconds)
        # use the duration of the winner and add the gap
        times_in_seconds.iloc[1:] = times_in_seconds.iloc[0] + gaps_in_seconds.iloc[1:]
        # convert back to string
        self._df["Times"] = times_in_seconds.apply(self._convert_seconds_to_string)

    def _convert_string_to_seconds(self, _gap_string: str) -> int:
        try:
            _gap_string = _gap_string.replace("+", "").strip()
            # use regex to extract from format xxxh yy' zz"
            hms = re.findall(r"(\d+)h (\d+)' (\d+)''", _gap_string)
            if hms:
                h, m, s = hms[0]
                return int(h) * 3600 + int(m) * 60 + int(s)
            else:
                return 0
        except Exception:
            return 0

    def _convert_seconds_to_string(self, _seconds: int) -> str:
        # Inverse to _convert_string_to_seconds
        h = _seconds // 3600
        m = (_seconds - h * 3600) // 60
        s = _seconds - h * 3600 - m * 60
        return f"{h}h {m}' {s}''"

    def _result_type(self, year) -> Literal["null", "points", "time"]:
        if year in [1905, 1906, 1908]:
            return "null"
        elif year in [1907, 1909, 1910, 1911, 1912]:
            return "points"
        else:
            return "time"


class StagesDataFrame(GenericEasyToParseDataFrame):
    def _post_process(self) -> None:
        self._bugfix_year_1904()
        self._df["Date"] = pd.to_datetime(self._df["Date"], dayfirst=True)

    def _bugfix_year_1904(self) -> None:
        # Fix typo for year 1904 data.
        # https://www.letour.fr/en/block/history/10708/stages/5067141e55bf996ee34cbce430900ad5
        if self._df["Date"][0] == "02/07/0194":
            self._df.loc[0, "Date"] = "02/07/1904"


class JerseyWearersDataFrame(GenericEasyToParseDataFrame):
    pass


class StageWinnersDataFrame(GenericEasyToParseDataFrame):
    def _post_process(self) -> None:
        self._df["Start"] = self._df["Parcours"].apply(
            lambda _: _.split(">")[0].strip()
        )
        self._df["Finish"] = self._df["Parcours"].apply(
            lambda _: _.split(">")[-1].strip()
        )
        self._df["Rider"] = self._df["Winner of stage"].apply(
            lambda _: _.split("(")[0].strip()
        )
        self._df["Team"] = self._df["Winner of stage"].apply(
            lambda _: _.split("(")[-1].strip(")")
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

        if isinstance(y := self._df["Year"].values[0], np.integer):
            return int(y)
        else:
            return -1

    def to_numeric(self, s: str) -> int | float:
        try:
            return int(s)
        except ValueError:
            return float(s)
