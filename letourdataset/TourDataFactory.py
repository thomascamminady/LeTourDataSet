from letourdataset.TourData import TourData
import logging
from letourdataset.URLCollector import URLCollector
from urllib.request import urlopen
from bs4 import BeautifulSoup


class TourDataFactory:
    def __init__(self) -> None:

        self._url_collector = URLCollector()
        self._urls = self._url_collector.get_links()
        self._tour_data_collection: list[TourData] = []

    def download(self) -> None:

        for url in self._urls:
            try:
                self._download(url)
            except Exception as e:
                logging.error(f"Error while downloading {url}: {e}")

    def _download(self, url: str) -> None:

        _url_dict = self._get_url_dict(url)
        self._tour_data_collection.append(TourData(_url_dict))

    def _get_url_dict(self, start_url: str) -> dict[str, str]:
        html = urlopen(start_url).read()
        soup = BeautifulSoup(html, features="lxml")
        buttons = soup.find_all("button")
        urls: dict[str, str] = {}
        for button in buttons:
            link_type = str(button.text.strip())
            link = str(button).split('"')[3]
            urls[link_type] = self._url_collector._prefix + link
        urls["Tour info"] = start_url
        return urls

    def get_tour_data_collection(self) -> list[TourData]:
        return self._tour_data_collection
