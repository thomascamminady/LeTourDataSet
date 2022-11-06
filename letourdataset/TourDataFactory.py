from letourdataset.TourData import TourData
import logging
from letourdataset.URLCollector import URLCollector
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from typing import Literal
from concurrent.futures import ProcessPoolExecutor


class TourDataFactory:
    def __init__(self) -> None:

        self._url_collector = URLCollector()
        self._urls = self._url_collector.get_links()
        self._tour_data_collection: list[TourData] = []

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
        return pd.concat(
            [tour_data.get_df(which) for tour_data in self._tour_data_collection],
            ignore_index=True,
        )

    def download(self, parallel: bool = False) -> None:

        _tour_data_collection: list[TourData] = []
        if parallel:
            with ProcessPoolExecutor(max_workers=8) as executor:
                for _url_dict in executor.map(self._get_url_dict, self._urls):
                    _tour_data_collection.append(TourData(_url_dict))
        else:
            for url in self._urls:
                try:
                    _url_dict = self._get_url_dict(url)
                    _tour_data_collection.append(TourData(_url_dict))
                except Exception as e:
                    logging.error(f"Error while downloading {url}: {e}")
        self._tour_data_collection = _tour_data_collection

    def _get_url_dict(self, start_url: str) -> dict[str, str]:
        html = urlopen(start_url).read()
        soup = BeautifulSoup(html, features="lxml")
        buttons = soup.find_all("button")
        urls: dict[str, str] = {}
        for button in buttons:
            link_type = str(button.text.strip())
            try:
                link = str(button).split('"')[3]
                urls[link_type] = self._url_collector._prefix + link
            except Exception as e:
                logging.error(f"Error while parsing {button} for {start_url}: {e}")
        urls["Tour info"] = start_url
        return urls

    def get_tour_data_collection(self) -> list[TourData]:
        return self._tour_data_collection
