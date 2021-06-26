# LeTourDataSet
A data set on riders in the Tour de France.

## Disclaimer 
For issues with this data set, see the [Issues tab](https://github.com/camminady/LeTourDataSet/issues). There are some entries that are incorrect. However, so far it seems that the mistake stems from wrong data on the letour.fr website. Looking back, I should have probably scraped another website.

## Data
Every cyclist of the Tour de France in a single CSV file, stored in the file `data/riders.csv`. 
The columns of the CSV file are:

```
Year,Rider,Rank,Time,DistanceKilometer,PersonalAvgPace,Hours,Minutes,Seconds,Team,RiderNumber,
 TotalSeconds,Gap,Bonus,Points,NumberStages,ListedAvgPace
```

## How to run
To regenerate the `data/riders.csv` file execute all cells of the `src/main.py`. This might take a couple of minutes. 

## Analysis
The `src/analysis.py` contains some basic analysis and visualizations of the data. For example, the distance and winner pace are shown below.

![Distance and winner average pace](https://raw.githubusercontent.com/camminady/LeTourDataSet/master/src/distanceAndPace.png)

## How to add future years
This file includes the date up to the 2020 tour (including). 
To add new results, look at `view-source:https://www.letour.fr/en/history`, around line 1790,
and add the new entry to `src/domainending.txt`. Then rerun the notebook.

## Legacy code
This code has been completely rewritten. The previous code, including the output, is in the [legacy repository](https://github.com/camminady/LeTourDataSetLegacy). Especially `legacy/README.txt` should be read. 


## License (MIT)
Copyright 2021 Thomas Camminady 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
