from letourdataset.TourDataFrame import (
    TourInfoDataFrame,
    StartersDataFrame,
    StageWinnersDataFrame,
    JerseyWearersDataFrame,
    StagesDataFrame,
    RankingsDataFrame,
)
from typing import Type, TypeVar

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
        self._TourInfo = self._retrieve(TourInfoDataFrame, "Tour info")
        self._Rankings = self._retrieve(RankingsDataFrame, "Ranking")
        self._Starters = self._retrieve(StartersDataFrame, "Starters")
        self._Stages = self._retrieve(StagesDataFrame, "Stages")
        self._StageWinners = self._retrieve(StageWinnersDataFrame, "Stages winners")
        self._JerseyWearers = self._retrieve(JerseyWearersDataFrame, "Jersey wearers")

        self._year = self._TourInfo.get_year()
        self._append_year_to_df()

    def _append_year_to_df(self) -> None:
        self._Rankings._df["Year"] = self._year
        self._Starters._df["Year"] = self._year
        self._Stages._df["Year"] = self._year
        self._StageWinners._df["Year"] = self._year
        self._JerseyWearers._df["Year"] = self._year

    def _retrieve(self, obj: Type[TDF], key: str) -> TDF:
        try:
            return obj(self._url_dict[key])
        except KeyError:
            raise KeyError(f"Key {key} not found in URL dictionary.")
