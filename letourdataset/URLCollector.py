import requests
from bs4 import BeautifulSoup


class URLCollector:
    def __init__(
        self,
        prefix="http://www.letour.fr",
        headers={
            "Accept": "text/html",
            "User-Agent": "python-requests/1.2.0",
            "Accept-Charset": "utf-8",
            "accept-encoding": "deflate, br",
        },
    ) -> None:

        self._prefix = prefix
        self._history_page = f"{prefix}/en/history"
        self._headers = headers
        self._links: list[str] = self._crawl_urls()

    def _crawl_urls(self) -> list[str]:
        """Crawl the URLs of all the editions of the Tour de France."""
        return [
            self._prefix + entry["data-tabs-ajax"]
            for entry in BeautifulSoup(
                requests.get(
                    self._history_page, allow_redirects=True, headers=self._headers
                ).text,
                "html.parser",
            ).find_all("button", {"class": "dateTabs__link"})
        ]

    def get_links(self) -> list[str]:
        return self._links
