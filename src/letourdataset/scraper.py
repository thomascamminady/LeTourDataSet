import asyncio
import logging
import re
from io import StringIO
from itertools import chain

import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from requests_html import AsyncHTMLSession
from rich.progress import track


class Scraper:
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
        # Determine the correct prefix based on the history page
        if "letourfemmes.fr" in history_page:
            self._prefix = "http://www.letourfemmes.fr"
            self._is_women = True
        else:
            self._prefix = "http://www.letour.fr"
            self._is_women = False
        self._links: list[str] = self._get_urls(history_page, headers)
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
        string = str(
            BeautifulSoup(
                requests.get(history_page, allow_redirects=True, headers=headers).text,
                "html.parser",
            )
        )
        pattern = r'data-tabs-ajax="([^"]+)"'
        matches = re.findall(pattern, string)
        # Validate that the URLs are ordered by most recent year first
        years = []
        for url in matches:
            # Try to extract a 4-digit year from the URL
            year_match = re.search(r'(\d{4})', url)
            if year_match:
                years.append(int(year_match.group(1)))
            else:
                years.append(None)
        # Check if years are in descending order (most recent first)
        valid_order = all(
            years[i] is None or years[i + 1] is None or years[i] >= years[i + 1]
            for i in range(len(years) - 1)
        )
        if not valid_order:
            logging.warning(
                "Year order in URLs is not descending (most recent first). Reordering."
            )
            # Sort matches by year descending, keeping None years at the end
            matches = [x for _, x in sorted(
                ((y if y is not None else -1, u) for y, u in zip(years, matches)),
                key=lambda t: t[0],
                reverse=True
            )]
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
            intermediate_rankings = await self._get_all_rankings(
                selections_urls["Ranking"], list(stages["Stages"])
            )
            stages_winners = self._get_stages_winners(selections_urls["Stages winners"])
            # teams = self._get_teams(selections_urls["Starters"])
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
        distance_str = str(distance[0]).replace(" ", "").replace(",", "")
        # Handle decimal distances by converting to float first, then to int
        distance = int(float(distance_str))
        return soup, year, distance

    def _get_stages(self, soup: Tag, year: int, distance: int) -> pd.DataFrame:
        select_tag = soup.find("select")
        if not isinstance(select_tag, Tag):
            raise Exception("Can't find `select`.")

        df_stages = pd.DataFrame(
            [[year, distance, option.text] for option in select_tag.find_all("option")],
            columns=["Year", "TotalTDFDistance", "Stage"],
        )

        # For the column Stage, it is formated like 'Stage 1 : Paris > Lyon' (so "Stage [Number of stage] : [Start city] > [End city]")
        # We will split this column into 'Stage number', 'Start city' and 'End city'
        def extract_stage_number(stage_str):
            try:
                return int(
                    stage_str.split(":")[0].split(" ")[1]
                )  # Here we use flot since in the early editions of the TDF some stages are played two times which gives for example stages 13.1 and 13.2; without this, the column should be int
            except (IndexError, ValueError):
                if "Prologue" in stage_str:
                    return (
                        0  # There is a case where the stage 0 is in fact a 'prologue'
                    )
                else:
                    try:
                        return float(stage_str.split(":")[0].split(" ")[1])
                    except (IndexError, ValueError):
                        logging.warning(
                            f"Could not parse stage number from '{stage_str}' in year {year}."
                        )
                        return None

        df_stages["Stage number"] = df_stages["Stage"].apply(extract_stage_number)
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
        response = requests.get(winners_link)
        response.raise_for_status()
        rank_html = response.content
        soup = BeautifulSoup(rank_html, "html.parser")
        stages_winners = soup.find("table")
        html_string = str(stages_winners)
        html_io = StringIO(html_string)
        df_stages_winners = pd.read_html(html_io)[0]
        df_stages_winners.drop(columns="Last km", inplace=True)
        return df_stages_winners

    def _get_teams(self, starters_link: str) -> pd.DataFrame:
        response = requests.get(starters_link)
        response.raise_for_status()
        starter_html = response.content
        soup = BeautifulSoup(starter_html, "html.parser")
        competitors = []
        team_blocks = soup.find("div", class_="list list--competitors").find_all(
            "h3", class_="list__heading"
        )

        for team_block in team_blocks:
            team_name = team_block.text.strip()
            list_box = team_block.find_next_sibling("div", class_="list__box")
            competitor_items = list_box.find_all("li", class_="list__box__item")

            for item in competitor_items:
                bib = (
                    item.find("span", class_="bib").text
                    if item.find("span", class_="bib")
                    else None
                )
                name = (
                    item.find("a", class_="runner__link").text.strip()
                    if item.find("a", class_="runner__link")
                    else None
                )
                country = (
                    item.find("span", class_="flag js-display-lazy")[
                        "data-class"
                    ].split("--")[-1]
                    if item.find("span", class_="flag js-display-lazy")
                    else None
                )

                if bib and name:
                    competitors.append(
                        {
                            "Team": team_name,
                            "Bib": bib,
                            "Name": name,
                            "Country": country,
                        }
                    )

        return pd.DataFrame(competitors)

    def _get_jersey_wearers(self, jersey_link: str) -> pd.DataFrame:
        response = requests.get(jersey_link)
        response.raise_for_status()
        jersey_html = response.content
        soup = BeautifulSoup(jersey_html, "html.parser")
        jersey_wearers = soup.find("table")
        html_string = str(jersey_wearers)
        html_io = StringIO(html_string)
        df_jersey_wearers = pd.read_html(html_io)[0]
        df_jersey_wearers = df_jersey_wearers.dropna(axis=1, how="all")
        cols = [col for col in df_jersey_wearers.columns if "jersey" in col.lower()]
        # Convert the columns that contains 'jersey' in their names to string
        df_jersey_wearers[cols] = df_jersey_wearers[cols].astype(str)
        return df_jersey_wearers

    def _add_bib_number(self, soup: Tag, df_rankings: pd.DataFrame) -> pd.DataFrame:
        # Manually add the bib numbers because they are not in the rankings table
        bibs = re.findall(r'data-bib="([^"]+)"', str(soup))
        bibs = [int(bib.replace("#", "")) for bib in bibs]
        df_rankings.insert(2, "Rider No.", bibs)
        return df_rankings

    def _get_rankings(self, soup: Tag) -> pd.DataFrame:
        """Get the rankings for a given year

        Args:
                soup (Tag): BeautifulSoup object of the ranking page

        Returns:
                pd.DataFrame: DataFrame containing the rankings for the given year
        """
        rankingTable = soup.find("table")
        html_string = str(rankingTable)
        html_io = StringIO(html_string)
        df_rankings = pd.read_html(html_io)[0]
        self._add_bib_number(soup, df_rankings)
        return df_rankings

    @staticmethod
    async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()

    async def _get_all_rankings(
        self, ranking_link: str, stages_numbers: list[float]
    ) -> pd.DataFrame:
        stages: list[list[dict[str, str]]] = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for stage_number in stages_numbers:
                for ranking_type_name, ranking_type_idx in self._ranking_types.items():
                    ranking_url = (
                        f"{ranking_link}?stage={stage_number}&type={ranking_type_idx}"
                    )
                    tasks.append(self._fetch(session, ranking_url))

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)

            response_idx = 0
            for stage_number in stages_numbers:
                for ranking_type_name, ranking_type_idx in self._ranking_types.items():
                    rank_html = responses[response_idx]
                    response_idx += 1
                    rank_soup = BeautifulSoup(rank_html, "html.parser")
                    rankings: list[dict[str, str]] = []

                    # Get the ranking table
                    ranking_table = rank_soup.find(
                        "table", {"class": "rankingTable rtable js-extend-target"}
                    )
                    if not ranking_table:
                        logging.info(
                            f"No ranking for {ranking_type_name} on stage {stage_number} (URL: {ranking_link})."
                        )
                        continue
                    rows = ranking_table.find_all("tr")
                    if len(rows) <= 2:
                        # First case 1- just the header so no data; 2- header and one row of data so no data
                        logging.info(
                            f"No ranking for {ranking_type_name} on stage {stage_number} (URL: {ranking_link})."
                        )
                        continue

                    for row in rows[1:]:
                        cols = row.find_all("td")
                        if "ite" in ranking_type_idx:
                            ranking = {
                                "Rank": cols[0].text.strip(),
                                "Rider": cols[1].text.strip(),
                                "Team": cols[2].text.strip(),
                                "Times": cols[3].text.strip(),
                            }
                            if len(cols) > 4:
                                ranking["Gap"] = cols[4].text.strip()
                            if len(cols) > 5:
                                ranking["B"] = cols[5].text.strip()
                            if len(cols) > 6:
                                ranking["P"] = cols[6].text.strip()
                        elif "ipe" in ranking_type_idx:
                            checkpoint = None
                            if len(cols) == 1:
                                checkpoint = cols[0].text.strip()
                                continue
                            else:
                                ranking = {
                                    "Rank": cols[0].text.strip(),
                                    "Rider": cols[1].text.strip(),
                                    "Team": cols[2].text.strip(),
                                    "Points": cols[3].text.strip(),
                                    "Checkpoint": checkpoint,
                                }
                                if len(cols) > 4:
                                    ranking["B"] = cols[4].text.strip()
                        elif "ime" in ranking_type_idx:
                            checkpoint = None
                            if len(cols) == 1:
                                checkpoint = cols[0].text.strip()
                                continue
                            ranking = {
                                "Rank": cols[0].text.strip(),
                                "Rider": cols[1].text.strip(),
                                "Team": cols[2].text.strip(),
                                "Points": cols[3].text.strip(),
                                "Checkpoint": checkpoint,
                            }
                        elif "ije" in ranking_type_idx or "ice" in ranking_type_idx:
                            ranking = {
                                "Rank": cols[0].text.strip(),
                                "Rider": cols[1].text.strip(),
                                "Team": cols[2].text.strip(),
                                "Times": cols[3].text.strip(),
                            }
                            if len(cols) > 4:
                                ranking["Gap"] = cols[4].text.strip()
                        elif "ete" in ranking_type_idx:
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
                    stages.append(rankings)

        return pd.DataFrame(list(chain.from_iterable(stages)))

    async def _fetch_yearly_tdf_urls(self, year_url: str) -> dict[str, str]:
        # Try using regular requests first (without JavaScript rendering)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(year_url) as response:
                    response.raise_for_status()
                    html_content = await response.text()

            soup = BeautifulSoup(html_content, "html.parser")

            buttons = soup.find_all(
                "button", class_="tabs__item btn js-tabs-nested"
            ) + soup.find_all(
                "button", class_="tabs__item btn js-tabs-nested is-active"
            )

            selections_urls = {
                button.get_text(strip=True): f"{self._prefix}{button['data-tabs-ajax']}"
                for button in buttons
                if button.get("data-tabs-ajax")
            }

            # If we got results, return them
            if selections_urls:
                return selections_urls

        except Exception as e:
            logging.warning(f"Failed to fetch URLs without JavaScript rendering: {e}")

        # Fallback to JavaScript rendering if the above fails
        session = AsyncHTMLSession()
        response = await session.get(year_url)
        await response.html.arender(timeout=20)

        soup = BeautifulSoup(response.html.html, "html.parser")

        buttons = soup.find_all(
            "button", class_="tabs__item btn js-tabs-nested"
        ) + soup.find_all("button", class_="tabs__item btn js-tabs-nested is-active")

        selections_urls = {
            button.get_text(strip=True): f"{self._prefix}{button['data-tabs-ajax']}"
            for button in buttons
        }

        return selections_urls

    def _cleanup(
        self,
        df_stages: pd.DataFrame,
        df_rankings: pd.DataFrame,
        df_all_rankings: pd.DataFrame,
        year: int,
        distance: int,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        # Odd years
        point_years = [1907, 1909, 1910, 1911, 1912]
        null_years = [1905, 1906, 1908]

        for df in [df_rankings, df_all_rankings]:
            # Remainder of df_rankings.columns : 'Rank', 'Rider', 'Rider No.', 'Team', 'Times', 'Gap', 'B', 'P'
            # Remainder of df_all_rankings.columns : 'Stages', 'Ranking type', 'CheckpointRank', 'Rider', 'Team', 'Times', 'Points', 'Gap', 'B', 'P', 'Rank', 'Checkpoint'
            df["Year"] = year
            df["Distance (km)"] = distance
            df["Number of stages"] = len(df_stages)

            df["ResultType"] = "time"
            df.loc[df["Year"].isin(null_years), "ResultType"] = "null"
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

            if year in [2006, 1997]:
                tmp = df[df["Year"] == year].reset_index()
                if "TotalSeconds" not in df.columns:
                    df["TotalSeconds"] = 0
                if "GapSeconds" not in df.columns:
                    df["GapSeconds"] = 0
                ts = tmp["TotalSeconds"].values
                gs = tmp["GapSeconds"].values
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

    def _get_seconds(self, row: str, mode: str) -> int:
        if isinstance(row, float) and pd.isna(row):
            return 0
        elif "h" in row:
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
        else:
            # Try using the library dateutil.parser to parse the time
            try:
                val = (
                    pd.to_datetime(row).hour * 3600
                    + pd.to_datetime(row).minute * 60
                    + pd.to_datetime(row).second
                )
            except Exception:
                val = 0

        if (mode == "Gap") and val > 180000:
            return 0
        else:
            return val
