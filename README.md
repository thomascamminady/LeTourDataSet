# LeTourDataSet
![Distance and winner average pace](https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Distance_And_Pace.png)

## TL;DR
If you use `pandas`, just get the data via:
```python
import pandas as pd 
df = pd.read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Riders_History.csv")
```
If you use `R` instead of `python`, you can run:
```R
library(readr)
df <- read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Riders_History.csv")
```

## Disclaimer 
For issues with this data set, see the [Issues tab](https://github.com/camminady/LeTourDataSet/issues). There are some entries that are incorrect. However, so far it seems that the mistake stems from wrong data on the letour.fr website. Looking back, I should have probably scraped another website.

## Data
Every cyclist of the Tour de France in a single CSV file, stored in the file `data/TDF_Riders_History.csv`.
There's also data on every stage in `data/TDF_Stages_History.csv`.

## How to run
To regenerate the `data/TDF_Riders_History.csv` file, execute all cells of the `src/main.py`. This might take a couple of minutes. 

## Analysis
The `src/analysis.py` contains some basic analysis and visualizations of the data. For example, the distance and winner pace are shown above.


## Legacy code
This code has been completely rewritten. The previous code, including the output, is in the [legacy repository](https://github.com/camminady/LeTourDataSetLegacy). Especially `legacy/README.txt` should be read. 
