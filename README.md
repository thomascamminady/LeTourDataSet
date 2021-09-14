# LeTourDataSet
A data set on riders in the Tour de France.

## TL;DR
If you use `pandas`, just get the data via:
```python
import pandas as pd 
df = pd.read_csv("https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/TDF_Riders_History.csv")
```

## Disclaimer 
For issues with this data set, see the [Issues tab](https://github.com/camminady/LeTourDataSet/issues). There are some entries that are incorrect. However, so far it seems that the mistake stems from wrong data on the letour.fr website. Looking back, I should have probably scraped another website.

## Data
Every cyclist of the Tour de France in a single CSV file, stored in the file `data/TDF_Riders_History.csv`.
There's also data on every stage in `data/TDF_Stages_History.csv`.

## How to run
To regenerate the `data/TDF_Riders_History.csv` file, execute all cells of the `src/main.py`. This might take a couple of minutes. 

## Analysis
The `src/analysis.py` contains some basic analysis and visualizations of the data. For example, the distance and winner pace are shown below.

![Distance and winner average pace](https://raw.githubusercontent.com/camminady/LeTourDataSet/master/data/distanceAndPace.png)

## Legacy code
This code has been completely rewritten. The previous code, including the output, is in the [legacy repository](https://github.com/camminady/LeTourDataSetLegacy). Especially `legacy/README.txt` should be read. 

