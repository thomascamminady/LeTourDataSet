# Le Tour de France Data Set

Data for the **Men's and Women's version** of the Tour de France.


## TL;DR
If you use `pandas`, just get the data via:
```python
import pandas as pd 
df_men = pd.read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Riders_History.csv")
df_women = pd.read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDFF_Riders_History.csv")

```
If you use `R` instead of `python`, you can run:
```R
library(readr)
df_men <- read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Riders_History.csv")
df_women <- read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDFF_Riders_History.csv")
```

![Distance and winner average pace](https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Distance_And_Pace.png)




## Disclaimer 
For issues with this data set, see the [Issues tab](https://github.com/camminady/LeTourDataSet/issues). There are some entries that are incorrect. However, so far it seems that the mistake stems from wrong data on the letour.fr website. Looking back, I should have probably scraped another website.

## Data
Every cyclist of the Tour de France in a single CSV file, stored in the file `data/TDF_Riders_History.csv`.
There's also data on every stage in `data/TDF_Stages_History.csv`.

## How to run
In your shell, just run these commands:
```python
poetry install # to install the environment
poetry run python letourdataset/Downloader.py # get the data
```


## Legacy code
This code has been completely rewritten. The previous code, including the output, is in the [legacy repository](https://github.com/camminady/LeTourDataSetLegacy). Especially `legacy/README.txt` should be read. 
