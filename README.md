<div align="center">
  <img src="logo.png" alt="Le Tour de France Data Set Logo" width="350"/>
</div>


Every cyclist and stage of the Tour de France (up to including 2025) in four CSV files.

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

## Quick Start

```bash
# Install dependencies
make install

# Download latest data (2025 men's and 2024 women's included)
make update

# Generate plots
make plot

# Or do both
make all
```

## Data Structure

The repository is organized as follows:

```
data/
├── men/                    # Men's Tour de France data
│   ├── TDF_Riders_History.csv
│   ├── TDF_Stages_History.csv
│   └── TDF_All_Rankings_History.csv
├── women/                  # Women's Tour de France data
│   ├── TDFF_Riders_History.csv
│   ├── TDFF_Stages_History.csv
│   └── TDFF_All_Rankings_History.csv
└── plots/                  # Generated visualizations
    ├── TDF_Distance_And_Pace.png
    └── TDFF_Distance_And_Pace.png
```

## Le Tour de France Femmes avec Zwift

As of 2022, the women's Tour de France was relaunched as "Le Tour de France Femmes avec Zwift". The data is available on the official [tour website](https://www.letourfemmes.fr/en) and is included in this dataset with complete coverage through 2025.

## Data Coverage

-   **Men's Tour de France**: 1903-2024 (complete historical coverage)
-   **Women's Tour de France**: 2022-2025 (complete since relaunch)

## Available Files

### Men's Data (`data/men/`)

-   `TDF_Riders_History.csv`: Every cyclist and winner data
-   `TDF_Stages_History.csv`: Stage-by-stage information
-   `TDF_All_Rankings_History.csv`: Comprehensive rankings data

### Women's Data (`data/women/`)

-   `TDFF_Riders_History.csv`: Every cyclist and winner data
-   `TDFF_Stages_History.csv`: Stage-by-stage information
-   `TDFF_All_Rankings_History.csv`: Comprehensive rankings data

## How to Run

### Using Make (Recommended)

```bash
# Install dependencies
make install

# Download latest data
make update

# Generate plots
make plot

# Run everything
make all

# See all available commands
make help
```

### Manual Execution

```bash
# Install environment
poetry install

# Download data
cd scripts && poetry run python download_data.py

# Generate plots
cd scripts && poetry run python generate_plots.py
```

## Development

```bash
# Install development dependencies
make install

# Run tests
make test

# Format code
make format

# Check code quality
make lint

# Check CSV data integrity
make check-csv
```

## Data Protection

This repository includes automated data protection to ensure historical data integrity:

-   ✅ **Row Protection**: CSV files can only grow (no data deletion)
-   ✅ **Column Protection**: New columns allowed, existing columns protected
-   ✅ **Data Integrity**: Existing data cannot be modified
-   ✅ **Automatic Validation**: GitHub Actions check every pull request

## Recent Updates (2025)

-   ✅ Added 2025 men's Tour de France data
-   ✅ Added 2024 women's Tour de France data
-   ✅ Reorganized repository with modern Python packaging
-   ✅ Renamed classes: `Downloader` → `Scraper`, `Plotter` → `Visualizer`
-   ✅ Added comprehensive Makefile for easy data management
-   ✅ Implemented CSV data protection workflows
-   ✅ Organized data into men/women subfolders

## Disclaimer

For issues with this data set, see the [Issues tab](https://github.com/thomascamminady/LeTourDataSet/issues). Some entries may be incorrect due to source data issues on the official websites. When discrepancies are found, they typically stem from the original letour.fr or letourfemmes.fr websites.

## Legacy Code

This code has been completely rewritten for 2025. The previous code and output are available in the [legacy repository](https://github.com/thomascamminady/LeTourDataSetLegacy). See `legacy/README.txt` for historical context.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes (data will be automatically validated)
4. Submit a pull request

The CSV data protection system will automatically verify that:

-   No historical data is deleted or modified
-   Only new data additions are permitted
-   Data integrity is maintained across all changes
