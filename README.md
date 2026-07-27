<div align="center">
  <img src="logo.png" alt="Le Tour de France Data Set Logo" width="350"/>
</div>

Every cyclist and stage of the Tour de France in four CSV files.

**🟡 Explore the data live: [camminady.dev/LeTourDataSet](https://camminady.dev/LeTourDataSet/)** — interactive charts and a rider lookup, reading these CSVs directly.

**Data coverage**

-   **Men's Tour de France**: 1903 - 2026 (all 113 editions)
-   **Women's Tour de France (Tour de France Femmes avec Zwift)**: 2022 - 2025 (all editions since the relaunch)

If you use `pandas`, just get the data via:

```python
import pandas as pd

# Men's Tour de France data
df_men_riders = pd.read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Riders_History.csv")
df_men_stages = pd.read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Stages_History.csv")

# Women's Tour de France data
df_women_riders = pd.read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/women/TDFF_Riders_History.csv")
df_women_stages = pd.read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/women/TDFF_Stages_History.csv")
```

![Distance and winner average pace](https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/plots/TDF_Distance_And_Pace.png)

![Winning margin](https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/plots/TDF_Winning_Margin.png)

If you use `R` instead of `python`, you can run:

```R
library(readr)

# Men's Tour de France data
df_men_riders <- read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Riders_History.csv")
df_men_stages <- read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Stages_History.csv")

# Women's Tour de France data
df_women_riders <- read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/women/TDFF_Riders_History.csv")
df_women_stages <- read_csv("https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/women/TDFF_Stages_History.csv")
```

## Data Structure

```
data/
├── men/                    # Men's Tour de France data
│   ├── TDF_Riders_History.csv    # one row per rider and edition (final GC)
│   └── TDF_Stages_History.csv    # one row per stage
├── women/                  # Women's Tour de France data
│   ├── TDFF_Riders_History.csv
│   └── TDFF_Stages_History.csv
└── plots/                  # Generated visualizations
    ├── TDF_Distance_And_Pace.png
    └── TDFF_Distance_And_Pace.png
```

Running the update pipeline additionally produces
`TDF_All_Rankings_History.csv` / `TDFF_All_Rankings_History.csv`
(per-stage rankings for every classification). These files are large and
are **not** committed to the repository; run `make update` to generate
them locally.

### Notes on the data

-   `ResultType` in the riders files is `time` (normal editions), `points`
    (1907-1912, when the race was decided on points), or `no-results`
    (1905, 1906, 1908, for which the source has no usable values).
    `TotalSeconds`/`GapSeconds` are 0 for non-`time` editions. The `Times`
    string is still kept verbatim for those years even though the source
    prints placeholders there (1907 runs 47h, 66h, 74h, ... for a race that
    actually took some 158 hours).
-   `B` is the rider's total **time bonus** and `P` the total **time
    penalty**. Both are in *seconds*, but the history pages print the bonus
    with a minute mark, so 52 seconds shows up as `52'`; penalties use the
    `MM' SS''` form. No bonus in the data exceeds 52, which matches the
    seconds reading. See
    [#14](https://github.com/thomascamminady/LeTourDataSet/issues/14).
-   Stage numbers are integers; split stages of early editions appear as
    e.g. `13.1` and `13.2`, and a prologue is stage `0`.
-   Some early editions genuinely had very small classified fields
    (e.g. 10 finishers in 1919).

### Known source-data limitations

The data mirrors letour.fr / letourfemmes.fr, including some flaws of the
source itself:

-   **1966** only lists the podium (3 riders); the full classification is
    not available on letour.fr (verified against all its ranking endpoints).
-   1967 rank 78 and 1982 rank 86 each list two riders with different
    times; ties with identical times (e.g. 1958, 1959, 1975) are real.
-   A few stages have no recorded stage winner, and the `Leader` column of
    the men's stages file is only populated for some editions.
-   **41 editions skip at least one rank** — the source lists e.g. ranks 39
    and 41 for 1928 but no 40. The gaps are in the source, so the dataset
    reproduces them rather than renumbering. Affected years run from 1909 to
    2012; 1985, 2006 and 2009 miss four or five ranks each. See
    [#3](https://github.com/thomascamminady/LeTourDataSet/issues/3).
-   **1981** gives Bernard Hinault `91h 34' 14''`, which implies about
    41 kph and disagrees with other sources; letour.fr still serves that
    value, so it is kept verbatim. See
    [#2](https://github.com/thomascamminady/LeTourDataSet/issues/2).

For other issues, see the [Issues tab](https://github.com/thomascamminady/LeTourDataSet/issues).

## How to Run

Requires [uv](https://docs.astral.sh/uv/).

```bash
make install    # Install dependencies (uv sync)
make update     # Complete data update workflow (recommended for annual updates)
make plot       # Generate plots from existing data
make test       # Run the test suite (pytest, offline)
make lint       # ruff + ty
make format     # ruff format
make check-csv  # Check CSV data integrity against origin/master
make diagnose   # Manual checks against the live letour.fr pages
make help       # See all available commands
```

### Annual update workflow

```bash
make update
```

This will:

1. 📥 Download the latest Tour de France data from the official sites
2. 🔧 Post-process and sort all data files
3. 🩹 Reconstruct the newest general classification if the site does not
   publish one yet (a stopgap that excludes time bonuses; replace it with
   official data once available)
4. 🛡️ Report CSV integrity (informational locally)
5. 📊 Regenerate the plots

A freshly finished edition keeps an empty general-classification table on
its year page for a while. The scraper then falls back to the *general*
ranking after the final stage, which is the official result including time
bonuses, so step 3 only has to reconstruct anything if that is missing too.

Then review the changes and commit. The individual steps are available as
`make download-only`, `make postprocess`, `make fix-riders-history`,
`make check-csv`, and `make plot`.

## Data Protection

A GitHub Actions check compares every data CSV against the base branch
and fails when existing rows or columns disappear or change. Rows are
compared order-independently with normalised values, so re-sorting or
reformatting does not trip it, and modifications are detected even when
rows are added at the same time.

Genuine corrections (e.g. the source site fixed a result) are allowed:
put the marker `[data-fix]` in the commit message together with an
explanation. See `.github/INFOS.md` for details.

## Le Tour de France Femmes avec Zwift

As of 2022, the women's Tour de France was relaunched as "Le Tour de
France Femmes avec Zwift". The data comes from the official
[letourfemmes.fr](https://www.letourfemmes.fr/en) site and is complete
since the relaunch. (Note: the source site reports a total distance of
0 km for 2025; the dataset carries the official route total of 1169 km
instead, via `DISTANCE_OVERRIDES` in `src/letourdataset/scraper.py`.)

## Disclaimer

Some entries may be incorrect due to source data issues on the official
websites. When discrepancies are found, they typically stem from the
original letour.fr or letourfemmes.fr data. If you spot one, please open
an issue.

## Legacy Code

This code has been completely rewritten. The previous code and output are
available in the [legacy repository](https://github.com/thomascamminady/LeTourDataSetLegacy).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes (CI runs linting, tests, and the data-protection check)
4. Submit a pull request
