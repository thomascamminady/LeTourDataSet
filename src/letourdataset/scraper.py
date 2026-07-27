import asyncio
import logging
import re
from io import StringIO
from itertools import chain
from typing import Any

import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from rich.progress import track

DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "text/html",
    "User-Agent": "python-requests/1.2.0",
    "Accept-Charset": "utf-8",
    "accept-encoding": "deflate, br",
}
REQUEST_TIMEOUT_SECONDS = 30
MAX_CONCURRENT_REQUESTS = 10

# Editions for which the source site reports a total distance of 0 km.
# The official route totals are used instead, keyed by (is_women, year).
DISTANCE_OVERRIDES: dict[tuple[bool, int], int] = {
    (True, 2025): 1169,
}


def parse_stage_number(stage_str: str, year: int) -> int | float | None:
    """Parse the stage number out of e.g. 'Stage 1 : Paris > Lyon'.

    Early editions ran some stages in two parts, which yields fractional
    numbers such as 13.1 and 13.2; a prologue is stage 0.
    """
    token_parts = stage_str.split(":")[0].split(" ")
    try:
        return int(token_parts[1])
    except (IndexError, ValueError):
        if "Prologue" in stage_str:
            return 0
        try:
            return float(token_parts[1])
        except (IndexError, ValueError):
            logging.warning(
                "Could not parse stage number from '%s' in year %d.",
                stage_str,
                year,
            )
            return None


class Scraper:
    def __init__(
        self,
        history_page: str = "https://www.letour.fr/en/history",
        headers: dict[str, str] | None = None,
    ) -> None:
        self._headers = dict(DEFAULT_HEADERS) if headers is None else dict(headers)
        # aiohttp must negotiate its own content encodings (brotli needs an
        # optional extra), so it gets the headers without accept-encoding.
        self._aio_headers = {
            key: value
            for key, value in self._headers.items()
            if key.lower() != "accept-encoding"
        }
        # Determine the correct prefix based on the history page
        if "letourfemmes.fr" in history_page:
            self._prefix = "https://www.letourfemmes.fr"
            self._is_women = True
        else:
            self._prefix = "https://www.letour.fr"
            self._is_women = False
        self._links: list[str] = self._get_urls(history_page, self._headers)
        self._ranking_types = {
            # "Individual (General)": "itg",
            "Individual (Stage)": "ite",
            # "Points (General)": "ipg",
            "Points (Stage)": "ipe",
            # "Climber (General)": "img",
            "Climber (Stage)": "ime",
            # "Youth (General)": "ijg",
            "Youth (Stage)": "ije",
            # "Combative (General)": "icg",
            "Combative (Stage)": "ice",
            # "Team (General)": "etg",
            "Team (Stage)": "ete",
        }

    def _get_urls(self, history_page: str, headers: dict[str, str]) -> list[str]:
        response = requests.get(
            history_page,
            allow_redirects=True,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        string = str(BeautifulSoup(response.text, "html.parser"))
        pattern = r'data-tabs-ajax="([^"]+)"'
        matches = re.findall(pattern, string)
        # Validate that the URLs are ordered by most recent year first
        years: list[int | None] = []
        for url in matches:
            # Try to extract a 4-digit year from the URL
            year_match = re.search(r"(\d{4})", url)
            years.append(int(year_match.group(1)) if year_match else None)

        def _is_descending(a: int | None, b: int | None) -> bool:
            return a is None or b is None or a >= b

        # Check if years are in descending order (most recent first)
        valid_order = all(_is_descending(a, b) for a, b in zip(years, years[1:]))
        if not valid_order:
            logging.warning(
                "Year order in URLs is not descending (most recent first). Reordering."
            )
            # Sort matches by year descending, keeping None years at the end
            matches = [
                x
                for _, x in sorted(
                    ((y if y is not None else -1, u) for y, u in zip(years, matches)),
                    key=lambda t: t[0],
                    reverse=True,
                )
            ]
        logging.debug(
            "Matches found in the history page:\n{}".format("\n".join(matches))
        )
        return matches

    async def run(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        stages_list: list[pd.DataFrame] = []
        rankings_list: list[pd.DataFrame] = []
        all_rankings_list: list[pd.DataFrame] = []
        logging.debug("Links:\n{}".format("\n".join(self._links)))
        for link in track(self._links, "Downloading historical data..."):
            logging.info("Downloading data from {}".format(self._prefix + link))
            soup, year, distance = self._get_soup_year_distance(self._prefix + link)

            logging.info("Parsing data from {}".format(self._prefix + link))
            stages = self._get_stages(soup, year, distance)
            final_rankings = self._get_rankings(soup)

            logging.info("Fetching yearly TDF URLs from {}".format(self._prefix + link))
            selections_urls = await self._fetch_yearly_tdf_urls(self._prefix + link)
            if final_rankings.empty:
                final_rankings = self._get_general_classification(
                    selections_urls["Ranking"], stages, year
                )
            intermediate_rankings = await self._get_all_rankings(
                selections_urls["Ranking"], list(stages["Stages"])
            )
            stages_winners = self._get_stages_winners(selections_urls["Stages winners"])
            jersey_wearers = self._get_jersey_wearers(selections_urls["Jersey wearers"])

            # Update the dataframe stages by merging on 'Stages' using the stages_winners dataframe and the jersey_wearers dataframe
            stages = pd.merge(stages, stages_winners, on="Stages", how="left")
            # Drop 'Parcours' column
            stages = stages.drop(columns="Parcours")
            stages = pd.merge(stages, jersey_wearers, on="Stages", how="left")
            # Make the first letter of each word in the fields of the columns that contains 'Winner' or 'Jersey' in their names uppercase and the rest lowercase using title() method
            cols = [
                col
                for col in stages.columns
                if "winner" in col.lower() or "jersey" in col.lower()
            ]
            stages[cols] = stages[cols].apply(lambda x: x.str.title())
            # stages['Team'] = stages['Winner of stage'].apply(lambda x: x.split('(')[1].replace(')', ''))
            # stages['Winner of stage'] = stages['Winner of stage'].apply(lambda x: x.split('(')[0].strip())

            logging.info("Cleaning up data from {}".format(self._prefix + link))
            df_ranking, df_all_rankings, df_stage = self._cleanup(
                stages,
                final_rankings,
                intermediate_rankings,
                year,
                distance,
            )
            logging.info("Data from {} cleaned up".format(self._prefix + link))
            stages_list.append(df_stage)
            rankings_list.append(df_ranking)
            all_rankings_list.append(df_all_rankings)

        logging.debug("Stage list:\n{}".format(stages_list))
        logging.debug("Ranking list:\n{}".format(rankings_list))
        df_stages = pd.concat(stages_list, ignore_index=True)
        df_rankings = pd.concat(rankings_list, ignore_index=True)
        df_all_rankings = pd.concat(all_rankings_list, ignore_index=True)

        # try to cast the "Rank" column to int and sort by Year first then Rank
        # for the df_all_rankings sort by Year, Stage, Rank
        return df_stages, df_rankings, df_all_rankings

    def _get_soup_year_distance(self, link: str) -> tuple[BeautifulSoup, int, int]:
        result = requests.get(
            link,
            allow_redirects=True,
            headers=self._headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        result.raise_for_status()
        logging.info("%s ==> HTTP STATUS = %s", link, result.status_code)

        soup = BeautifulSoup(result.text, "html.parser")
        year_tag = soup.find("h3")
        if year_tag is None:
            raise ValueError(f"Could not find the year heading (h3) on {link}.")
        year = int(year_tag.text[-4:])
        stats = soup.select("[class~=statsInfos__number]")
        if len(stats) < 2:
            raise ValueError(f"Could not find the total distance on {link}.")
        distance_str = str(stats[1].contents[0]).replace(" ", "").replace(",", "")
        # Decimal distances are rounded to the nearest integer kilometre
        distance = round(float(distance_str))
        override = DISTANCE_OVERRIDES.get((self._is_women, year))
        if distance == 0 and override is not None:
            logging.info(
                "Source reports 0 km for %d; using the official route total %d km.",
                year,
                override,
            )
            distance = override
        return soup, year, distance

    def _get_stages(self, soup: Tag, year: int, distance: int) -> pd.DataFrame:
        select_tag = soup.find("select")
        if not isinstance(select_tag, Tag):
            raise ValueError("Can't find the stage `select` element.")

        df_stages = pd.DataFrame(
            [[year, distance, option.text] for option in select_tag.find_all("option")],
            columns=["Year", "TotalTDFDistance", "Stage"],
        )

        # The Stage column is formatted like 'Stage 1 : Paris > Lyon', i.e.
        # "Stage [number] : [start city] > [end city]"; split it apart.
        df_stages["Stage number"] = df_stages["Stage"].apply(
            lambda stage_str: parse_stage_number(stage_str, year)
        )
        df_stages["Start"] = df_stages["Stage"].apply(
            lambda x: x.split(":")[1].split(">")[0].strip()
        )
        df_stages["End"] = df_stages["Stage"].apply(
            lambda x: x.split(":")[1].split(">")[1].strip()
        )
        df_stages.drop(columns="Stage", inplace=True)
        df_stages.rename(columns={"Stage number": "Stages"}, inplace=True)
        df_stages = df_stages[["Year", "TotalTDFDistance", "Stages", "Start", "End"]]
        return df_stages

    def _get_stages_winners(self, winners_link: str) -> pd.DataFrame:
        response = requests.get(
            winners_link, headers=self._headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        stages_winners = soup.find("table")
        if stages_winners is None:
            raise ValueError(f"No stage winners table found on {winners_link}.")
        df_stages_winners = pd.read_html(StringIO(str(stages_winners)))[0]
        df_stages_winners.drop(columns="Last km", inplace=True)
        return df_stages_winners

    def _get_jersey_wearers(self, jersey_link: str) -> pd.DataFrame:
        response = requests.get(
            jersey_link, headers=self._headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        jersey_wearers = soup.find("table")
        if jersey_wearers is None:
            raise ValueError(f"No jersey wearers table found on {jersey_link}.")
        df_jersey_wearers = pd.read_html(StringIO(str(jersey_wearers)))[0]
        df_jersey_wearers = df_jersey_wearers.dropna(axis=1, how="all")
        cols = [col for col in df_jersey_wearers.columns if "jersey" in col.lower()]
        # Convert the columns that contains 'jersey' in their names to string
        df_jersey_wearers[cols] = df_jersey_wearers[cols].astype(str)
        return df_jersey_wearers

    def _add_bib_number(self, soup: Tag, df_rankings: pd.DataFrame) -> pd.DataFrame:
        # Manually add the bib numbers because they are not in the rankings table
        bibs = [
            int(bib.replace("#", ""))
            for bib in re.findall(r'data-bib="([^"]+)"', str(soup))
        ]
        if len(bibs) == len(df_rankings):
            df_rankings.insert(2, "Rider No.", bibs)
        else:
            logging.warning(
                "Found %d bib numbers for %d ranking rows; leaving 'Rider No.' empty.",
                len(bibs),
                len(df_rankings),
            )
            df_rankings.insert(2, "Rider No.", None)
        return df_rankings

    def _get_rankings(self, soup: Tag) -> pd.DataFrame:
        """Get the rankings for a given year

        Args:
                soup (Tag): BeautifulSoup object of the ranking page

        Returns:
                pd.DataFrame: DataFrame containing the rankings for the given year
        """
        ranking_table = soup.find("table")
        if ranking_table is None:
            raise ValueError("No ranking table found on the year page.")
        df_rankings = pd.read_html(StringIO(str(ranking_table)))[0]
        self._add_bib_number(soup, df_rankings)
        return df_rankings

    def _get_general_classification(
        self, ranking_link: str, df_stages: pd.DataFrame, year: int
    ) -> pd.DataFrame:
        """Read the final GC off the last stage's general ranking page.

        The year page only gains its own general classification table some
        time after the edition has finished. Until then the general ranking
        after the last stage is the official final result (time bonuses
        included), so it is used instead of leaving the year unranked.
        """
        stage_numbers = [
            stage
            for stage in df_stages["Stages"]
            if stage is not None and pd.notna(stage)
        ]
        if not stage_numbers:
            logging.warning("No stages known for %d; cannot read a final GC.", year)
            return pd.DataFrame()

        last_stage = max(stage_numbers)
        stage_param = (
            int(last_stage) if float(last_stage).is_integer() else float(last_stage)
        )
        url = f"{ranking_link}?stage={stage_param}&type=itg"
        logging.info("Year page for %d has no GC table; falling back to %s", year, url)

        response = requests.get(
            url, headers=self._headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        ranking_table = soup.find(
            "table", {"class": "rankingTable rtable js-extend-target"}
        )
        if not isinstance(ranking_table, Tag) or len(ranking_table.find_all("tr")) <= 1:
            logging.warning("No final general classification available for %d.", year)
            return pd.DataFrame()

        df_rankings = pd.read_html(StringIO(str(ranking_table)))[0]
        self._add_bib_number(ranking_table, df_rankings)
        logging.info("Recovered %d GC rows for %d.", len(df_rankings), year)
        return df_rankings

    @staticmethod
    async def _fetch(
        session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()

    async def _get_all_rankings(
        self, ranking_link: str, stages_numbers: list[float]
    ) -> pd.DataFrame:
        stages: list[list[dict[str, Any]]] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS * 4)
        async with aiohttp.ClientSession(
            timeout=timeout, headers=self._aio_headers
        ) as session:
            tasks = []
            for stage_number in stages_numbers:
                for ranking_type_name, ranking_type_idx in self._ranking_types.items():
                    ranking_url = (
                        f"{ranking_link}?stage={stage_number}&type={ranking_type_idx}"
                    )
                    tasks.append(self._fetch(session, ranking_url, semaphore))

            # Execute all requests concurrently (bounded by the semaphore)
            responses = await asyncio.gather(*tasks)

            response_idx = 0
            for stage_number in stages_numbers:
                for ranking_type_name, ranking_type_idx in self._ranking_types.items():
                    rank_html = responses[response_idx]
                    response_idx += 1
                    rankings = self._parse_ranking_rows(
                        rank_html, stage_number, ranking_type_name, ranking_type_idx
                    )
                    if not rankings:
                        logging.info(
                            "No ranking for %s on stage %s (URL: %s).",
                            ranking_type_name,
                            stage_number,
                            ranking_link,
                        )
                        continue
                    stages.append(rankings)

        return pd.DataFrame(list(chain.from_iterable(stages)))

    @staticmethod
    def _parse_ranking_rows(
        rank_html: str,
        stage_number: float,
        ranking_type_name: str,
        ranking_type_idx: str,
    ) -> list[dict[str, Any]]:
        """Parse one ranking page into row dicts; empty list when no data."""
        rank_soup = BeautifulSoup(rank_html, "html.parser")
        ranking_table = rank_soup.find(
            "table", {"class": "rankingTable rtable js-extend-target"}
        )
        if not isinstance(ranking_table, Tag):
            return []
        rows = ranking_table.find_all("tr")
        if len(rows) <= 2:
            # Just a header, or a header plus a single placeholder row
            return []

        rankings: list[dict[str, Any]] = []
        # Points/climber tables interleave single-cell rows naming the
        # checkpoint the following rows belong to.
        checkpoint: str | None = None
        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                # Header-only rows (th cells) carry no ranking data
                continue
            ranking: dict[str, Any]
            if ranking_type_idx in ("ipe", "ime"):
                if len(cols) == 1:
                    checkpoint = cols[0].text.strip()
                    continue
                if len(cols) < 4:
                    logging.warning(
                        "Skipping malformed %s row on stage %s (%d cells).",
                        ranking_type_name,
                        stage_number,
                        len(cols),
                    )
                    continue
                ranking = {
                    "Rank": cols[0].text.strip(),
                    "Rider": cols[1].text.strip(),
                    "Team": cols[2].text.strip(),
                    "Points": cols[3].text.strip(),
                    "Checkpoint": checkpoint,
                }
                if ranking_type_idx == "ipe" and len(cols) > 4:
                    ranking["B"] = cols[4].text.strip()
            elif ranking_type_idx in ("ite", "ije", "ice"):
                if len(cols) < 4:
                    logging.warning(
                        "Skipping malformed %s row on stage %s (%d cells).",
                        ranking_type_name,
                        stage_number,
                        len(cols),
                    )
                    continue
                ranking = {
                    "Rank": cols[0].text.strip(),
                    "Rider": cols[1].text.strip(),
                    "Team": cols[2].text.strip(),
                    "Times": cols[3].text.strip(),
                }
                if len(cols) > 4:
                    ranking["Gap"] = cols[4].text.strip()
                if ranking_type_idx == "ite":
                    if len(cols) > 5:
                        ranking["B"] = cols[5].text.strip()
                    if len(cols) > 6:
                        ranking["P"] = cols[6].text.strip()
            elif ranking_type_idx == "ete":
                if len(cols) < 3:
                    logging.warning(
                        "Skipping malformed %s row on stage %s (%d cells).",
                        ranking_type_name,
                        stage_number,
                        len(cols),
                    )
                    continue
                ranking = {
                    "Rank": cols[0].text.strip(),
                    "Team": cols[1].text.strip(),
                    "Times": cols[2].text.strip(),
                }
                if len(cols) > 3:
                    ranking["Gap"] = cols[3].text.strip()
            else:
                raise NotImplementedError(
                    f"Ranking type {ranking_type_name} not implemented"
                )

            ranking["Stages"] = stage_number
            ranking["Ranking type"] = ranking_type_name
            rankings.append(ranking)
        return rankings

    async def _fetch_yearly_tdf_urls(self, year_url: str) -> dict[str, str]:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(
            timeout=timeout, headers=self._aio_headers
        ) as session:
            async with session.get(year_url) as response:
                response.raise_for_status()
                html_content = await response.text()

        soup = BeautifulSoup(html_content, "html.parser")

        buttons = soup.find_all(
            "button", class_="tabs__item btn js-tabs-nested"
        ) + soup.find_all("button", class_="tabs__item btn js-tabs-nested is-active")

        selections_urls = {
            button.get_text(strip=True): f"{self._prefix}{button['data-tabs-ajax']}"
            for button in buttons
            if button.get("data-tabs-ajax")
        }

        if not selections_urls:
            raise RuntimeError(
                f"No selection tabs (Ranking, Stages winners, ...) found on "
                f"{year_url}; the page layout may have changed."
            )

        return selections_urls

    def _cleanup(
        self,
        df_stages: pd.DataFrame,
        df_rankings: pd.DataFrame,
        df_all_rankings: pd.DataFrame,
        year: int,
        distance: int,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        # Odd years: some early editions were decided on points, and for a
        # few the source has no result values at all. "no-results" is used
        # instead of "null" because pandas parses the literal string "null"
        # as NaN, so it would not survive a CSV round-trip.
        point_years = [1907, 1909, 1910, 1911, 1912]
        null_years = [1905, 1906, 1908]

        for df in [df_rankings, df_all_rankings]:
            # Remainder of df_rankings.columns : 'Rank', 'Rider', 'Rider No.', 'Team', 'Times', 'Gap', 'B', 'P'
            # Remainder of df_all_rankings.columns : 'Stages', 'Ranking type', 'CheckpointRank', 'Rider', 'Team', 'Times', 'Points', 'Gap', 'B', 'P', 'Rank', 'Checkpoint'
            df["Year"] = year
            df["Distance (km)"] = distance
            df["Number of stages"] = len(df_stages)

            df["ResultType"] = "time"
            df.loc[df["Year"].isin(null_years), "ResultType"] = "no-results"
            df.loc[df["Year"].isin(point_years), "ResultType"] = "points"

            if "Times" in df.columns:
                df["TotalSeconds"] = df["Times"].apply(
                    lambda x: self._get_seconds(x, "Total")
                )
            else:
                df["TotalSeconds"] = 0
            if "Gap" in df.columns:
                df["GapSeconds"] = df["Gap"].apply(
                    lambda x: self._get_seconds(x, "Gap")
                )
            else:
                df["GapSeconds"] = 0

            df["TotalSeconds"] = df["TotalSeconds"].fillna(0).astype(int)
            df["GapSeconds"] = df["GapSeconds"].fillna(0).astype(int)

            # Editions not decided on time carry no meaningful cumulative
            # time, but the source still prints placeholder values (1907
            # runs 47h, 66h, 74h, ... while the race actually took ~158h).
            # The Times/Gap strings are kept as scraped; only the derived
            # seconds are zeroed.
            non_time = df["ResultType"] != "time"
            df.loc[non_time, "TotalSeconds"] = 0
            df.loc[non_time, "GapSeconds"] = 0

            if year in [2006, 1997]:
                tmp = df[df["Year"] == year].reset_index()
                ts = tmp["TotalSeconds"].to_numpy().copy()
                gs = tmp["GapSeconds"].to_numpy()
                ts[1:] = ts[0] + gs[1:]
                df.loc[df["Year"] == year, "TotalSeconds"] = ts

        df_rankings.sort_values(["Year", "Rank"], axis=0, ascending=True, inplace=True)
        df_rankings = df_rankings.reset_index(drop=True)

        df_stages.sort_values(["Year", "Stages"], axis=0, ascending=True, inplace=True)
        df_stages = df_stages.reset_index(drop=True)

        df_all_rankings.sort_values(
            ["Year", "Stages", "Ranking type", "Rank"],
            axis=0,
            ascending=True,
            inplace=True,
        )
        df_all_rankings = df_all_rankings.reset_index(drop=True)

        return df_rankings, df_all_rankings, df_stages

    @staticmethod
    def _get_seconds(row: str | float, mode: str) -> int:
        if isinstance(row, float) and pd.isna(row):
            return 0
        text = str(row)
        if "h" in text:
            try:
                val = sum(
                    to_seconds * int(t)
                    for to_seconds, t in zip(
                        [3600, 60, 1],
                        text.replace("h", ":")
                        .replace("'", ":")
                        .replace('"', ":")
                        .replace(" ", "")
                        .replace("+", "")
                        .replace("-", "0")
                        .split(":"),
                    )
                )
            except ValueError:
                logging.warning(
                    "Could not parse %s value '%s'; treating as 0 seconds.",
                    mode,
                    text,
                )
                return 0
        else:
            try:
                parsed = pd.to_datetime(text)
                val = parsed.hour * 3600 + parsed.minute * 60 + parsed.second
            except Exception:
                logging.debug(
                    "Could not parse %s value '%s'; treating as 0 seconds.",
                    mode,
                    text,
                )
                return 0

        if (mode == "Gap") and val > 180000:
            # Gaps above 50 hours are parsing artefacts on the source pages
            logging.debug("Ignoring implausible %s value '%s'.", mode, text)
            return 0
        return val
