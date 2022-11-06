from letourdataset.TourDataFrame import (
    TourInfoDataFrame,
    StartersDataFrame,
    StageWinnersDataFrame,
    JerseyWearersDataFrame,
    StagesDataFrame,
    RankingsDataFrame,
)
from typing import Type, TypeVar, Literal
import pandas as pd

TDF = TypeVar(
    "TDF",
    TourInfoDataFrame,
    StartersDataFrame,
    StageWinnersDataFrame,
    JerseyWearersDataFrame,
    StagesDataFrame,
    RankingsDataFrame,
)


class TourData:
    def __init__(self, url_dict: dict[str, str]) -> None:
        self._url_dict = url_dict
        # The retrieve function needs to pass a year so that that column
        # can be created in the dataframes to ultimately do the bugfixes.
        # But at this point it is not yet known, so that year to None.
        self._year: int | None = None
        self._TourInfo = self._retrieve(TourInfoDataFrame, "Tour info")
        self._year = self._TourInfo.get_year()  # Now we know the year.

        self._Rankings = self._retrieve(RankingsDataFrame, "Ranking")
        self._Starters = self._retrieve(StartersDataFrame, "Starters")
        self._Stages = self._retrieve(StagesDataFrame, "Stages")
        self._StageWinners = self._retrieve(StageWinnersDataFrame, "Stages winners")
        self._JerseyWearers = self._retrieve(JerseyWearersDataFrame, "Jersey wearers")

        self._append_year_to_df()

    def get_df(
        self,
        which: Literal[
            "TourInfo",
            "Rankings",
            "Starters",
            "Stages",
            "StageWinners",
            "JerseyWearers",
        ],
    ) -> pd.DataFrame:
        return getattr(self, f"_{which}").get_df()

    def _retrieve(self, obj: Type[TDF], key: str) -> TDF:
        try:
            return obj(self._url_dict[key], self._year)
        except KeyError:
            raise KeyError(f"Key {key} not found in URL dictionary.")

    def _append_year_to_df(self) -> None:
        self._Rankings._df["Year"] = self._year
        self._Starters._df["Year"] = self._year
        self._Stages._df["Year"] = self._year
        self._StageWinners._df["Year"] = self._year
        self._JerseyWearers._df["Year"] = self._year
