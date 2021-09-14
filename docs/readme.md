# LeTour data set 
This file downloads raw data about every rider of every Tour de France (from 1903 up to 2020). This data will then be postprocessed and stored in CSV format.
Executing this notebook might take some minutes.

## 1) Retrieve urls for data extract
First we generate the urls that we need to download the raw HTML pages from the `letour.fr` website to work offline from here on. The dataframe dflink will stores the respective url for each year.
Take a look at `view-source:https://www.letour.fr/en/history` (at around line 1143-1890).  


```python
import os
import subprocess
import collections
import re
from pathlib import Path
import datetime
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

```


```python
PREFIX = 'http://www.letour.fr'
HISTORYPAGE = 'https://www.letour.fr/en/history'

```


```python
headers = {'Accept': 'text/html', 'User-Agent': 'python-requests/1.2.0','Accept-Charset': 'utf-8','accept-encoding': 'deflate, br'}
```


```python

```


```python
resulthistpage = requests.get(HISTORYPAGE, allow_redirects=True, headers=headers)
souphistory = BeautifulSoup(resulthistpage.text, 'html.parser')
```


```python
# Find select tag for histo links
select_tag_histo = souphistory.find_all("button",{"class" :"dateTabs__link"})

LH = [x["data-tabs-ajax"] for x in select_tag_histo]

dflink = pd.DataFrame({'TDFHistorylink':LH})
dflink
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>TDFHistorylink</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/en/block/history/10707/d0ab6a216569236433268b...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/en/block/history/10708/0b76b8f809ad5d8bcf3579...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/en/block/history/10709/c5f53ced72a23f333cc186...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/en/block/history/10710/ead1d1704b1600c795619e...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/en/block/history/10711/f558d3bc819c8ee5dc627d...</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
    </tr>
    <tr>
      <th>102</th>
      <td>/en/block/history/10809/7be3a459d846b4672915c5...</td>
    </tr>
    <tr>
      <th>103</th>
      <td>/en/block/history/10810/7035a5dc53631209d3581f...</td>
    </tr>
    <tr>
      <th>104</th>
      <td>/en/block/history/11818/f34c3404d95a697dcf77d4...</td>
    </tr>
    <tr>
      <th>105</th>
      <td>/en/block/history/11819/96c0eb3fa403ebf222f28b...</td>
    </tr>
    <tr>
      <th>106</th>
      <td>/en/block/history/11820/17fa8e795e69e9f326ea26...</td>
    </tr>
  </tbody>
</table>
<p>107 rows × 1 columns</p>
</div>



## 2) Get data from HTML pages and convert results to dataframes

### 2.1) Create function that convert HHh mm' ss'' to seconds


```python
def calcTotalSeconds(row,mode):

   val = sum(x * int(t) for x, t in zip([3600, 60, 1], row.replace("h",":").replace("'",":").replace('"',':').replace(" ","").replace("+","").replace("-","0").split(":")))
   
   if ((mode=='Gap') and val > 180000) :
        val=0
    
   return val
```

### 2.2) Create a function that will retrieve elements from a source HTML page located on an input url


```python
def getstagesNrank(i_url):
    resultfull = requests.get(i_url, allow_redirects=True)
    result = resultfull.text
    resultstatus = resultfull.status_code
    
    print(i_url + ' ==> HTTP STATUS = ' + str(resultstatus))
    
    soup = BeautifulSoup(result, 'html.parser')  
    h=soup.find('h3')
    year=int(h.text[-4:])

    # Find select tag
    select_tag = soup.find("select")

    # find all option tag inside select tag
    options = select_tag.find_all("option")

    cols = ['Year','TotalTDFDistance','Stage']
    lst = []
    
    #search for stages
    distance=soup.select("[class~=statsInfos__number]")[1].contents
               
    #search for distance of the TDF edition
    for option in options:
       lst.append([year,int(distance[0].replace(" ","")),option.text])
               
    dfstages = pd.DataFrame(lst, columns=cols)
    
    
    # Find select tag for ranking racers
    rankingTable = soup.find("table")

    dfrank = pd.read_html(str(rankingTable))[0]

    dfrank['Year']=year
    dfrank['Distance (km)']=int(distance[0].replace(" ",""))
    dfrank['Number of stages']=len(dfstages)
    dfrank['TotalSeconds']=dfrank['Times'].apply(lambda x:calcTotalSeconds(x,'Total'))
    dfrank['GapSeconds']=dfrank['Gap'].apply(lambda x:calcTotalSeconds(x,'Gap'))

    
    return dfstages, dfrank
```

### 2.3) Loop on the dflink dataframe to get data from each url source


```python
dfstagesres=[]
dfstagesrestmp=[]
dfrankres=[]
dfrankrestmp=[]
dfrankoutput=[]

for index, row  in dflink.iterrows():
    url = PREFIX+row['TDFHistorylink']
    try :
      if index >= 12 :  # limit from 1919 (data need to be cleaned a little bit more before that)
        dfstagesres, dfrankres=getstagesNrank(url)
        dfstagesrestmp= dfstagesres.append(dfstagesrestmp, ignore_index=True)  
        dfrankrestmp=dfrankres.append(dfrankrestmp, ignore_index=True)
        
        
    except:
      raise

    
dfstageoutput=dfstagesrestmp
dfrankoutput=dfrankrestmp
```

    http://www.letour.fr/en/block/history/10719/f15cf81b7599ea113d2b1d614f73bf83 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10720/53ac40095834ae1aae5d197aa730799a ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10721/c663ba39ac60d58c55a1a787a23025fc ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10722/cc5d0ba48a5d9bd9ee5e222160452b6f ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10723/9212137527c3f19c0cfccd1d07d80649 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10724/61621b1b7012e711ae7457a04e123aab ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10725/326ccc005b547ad2ad33e2fc03d27159 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10726/417b583aab876fdb00496da5c2be1a7d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10727/0ab2dd4f425fcdcb9cc0a1511f49c494 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10728/58abb1c5f80d5d1b088ead3c32a5a815 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10729/323ab10f97b3b3b6c865b63dcecf7e88 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10730/9047f2218cebb70010ff9fc50585e204 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10731/71efd6183471464d6be619275e187eee ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10732/994e5d74cdaede876fec2b451051c8e1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10733/be923012b4124a9bd0991212e9977d42 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10734/aed1c90b119f634ebc5d1e7e6a671faf ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10735/05bd6d64c780c558f7ffd7bd5879c776 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10736/53cfbe0f209af0e4d92fff714bf2f18d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10737/c40634701bbc32655fc85bb3ddde49f5 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10738/c2d7990fb2a094d495e11e8098c59c51 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10739/e8866f6cc4d0163829c95efc4a729463 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10740/c5548896e2ae8715122b3989d3ed76b1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10741/a722302e475af7214500f16e424e25d0 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10742/dfaf06d272727e8b57b63f72fcdbafa8 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10743/5a9ece659139988007c4e0f6f9fc5c20 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10744/367ba379f6d341a7bdc545a122d3c78d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10745/7381958972518a9845edee052c8edbfc ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10746/45ef03cc5c64c264bf96bf08d4384d3d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10747/98d1ca2953df385a9bc1c7b1b4749b2b ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10748/1f6f715544c4aec948adcb4085900c4c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10749/a896b855e40db82c92217ccdd5532cdb ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10750/e072737429413b7d608e99db5313b13e ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10751/bb0f8df099b6e1f53064105d9e789f1f ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10752/cb437a1a3262575de6df27be96d2cd55 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10753/e890ae42c19946e34da655a909f98bfe ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10754/1e38a3d734b196c4f8ac6ba7063b218b ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10755/ff596257302baac39a22e1f2e4faf016 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10756/89a04a27336b19dfe4d6a4ea2ee46582 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10757/a7983332f5a930e28087ae63a7874475 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10758/56a4797d820f12ec56f06298fab868b9 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10759/07dc37874db6b049e640b253672cf299 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10760/3b171e28d17eb88dbb829f02a9fb3709 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10761/c3e23b93c3d11a653857785d1136ffb6 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10762/e5cba06222169e8ea482b253c93fd5b9 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10763/adf45f6a131be9ab505e4d0f100418f7 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10764/9be91c73090072a334e97ec5d9b692b2 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10765/1602abcaab318c332c1479ecd27154e1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10766/5f1300708ea73ac042645afd5da10e29 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10767/62b2104a378309ef9ac5acc908e600df ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10768/12626d9920ed70ad18cdc7869e493ee0 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10769/9184e05910d640ad1af5cccc9321adbb ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10770/0b714daa83b004421e81d0ef62c8c0f3 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10771/395c856712f93e5289971151df458a61 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10772/3108137894d31c631408c1e2ac5510bb ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10773/ad0e4cf5a083a40d11bb15d1404559ed ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10774/5a2702b95bc1f297980241915b0c0eee ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10775/6365159573723beb801f343a6efb4763 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10776/1d486875bf13f11f37a63ee3a773ccc9 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10777/f1773d9b0704ed89afad4012905ec744 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10778/8845310ec3c8145620ac465f3e112cca ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10779/db843b1682239241b56010705153d657 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10780/fce0b5e49551473911dadd219da7cb6c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10781/39d1113fcd9febaf891760301f41a383 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10782/c5cd539d3aed4897b7a087c06fff4e5e ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10783/0d7fef284362baf0738e2569898bcc5c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10784/840372b1c5ef49ced963d12709d2bfe1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10785/88ea8997b2d00f171d74fdd18200c4ac ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10786/97ba8b33489f910f7217ee3f6bdd68c7 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10787/1a04d3c53ae89dcdf73df8027654c1db ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10788/d98288396c5dbd8446699ad88413632b ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10789/0073016ba550a84a666f752c64bafef8 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10790/ba6803b7f72483da9dcef054d3564bef ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10791/70c111aba67f7f32344852fc369f445d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10792/f892bbc452142340a7dfe883719d7637 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10793/532062cd8f6afe8ec3796beeee9fb60d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10794/f456958e5bf979def96740c09a39f0d0 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10795/0ed86366456d46e1defebebcedef4404 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10796/a0c4bbd9f74d2fb237f3fcfd985dcdfe ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10797/4c6e179ada14b5ea99feaa75cfc5cc27 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10798/dc1ea3d295e447e632d63c31d313e22c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10799/4df09e2d455b3d4bfea3d78091f0b0b1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10800/14026271ed58df742b5e2182adc964cb ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10801/7c59f5199df3e8a97888b3ab3deafadb ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10802/814bff61212e58cf7c2beaddb1c083b3 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10803/757e8e81b7183fde7329fd8ab9b69783 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10804/89b36b01ffe439e016ec1d59c57b63d1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10805/1ec24b4375d16b922c9c9c489d25465c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10806/196e36cfe7aff4b5fc2d1055f7dcf864 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10807/d538a7fbdfc0d657fbf064561840fbb1 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10808/3f166bedb535ee9bff2fb7ead0a7812c ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10809/7be3a459d846b4672915c576cb7ed6b9 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/10810/7035a5dc53631209d3581f64a433b10d ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/11818/f34c3404d95a697dcf77d4cd8e8278fa ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/11819/96c0eb3fa403ebf222f28b6e45115c56 ==> HTTP STATUS = 200
    http://www.letour.fr/en/block/history/11820/17fa8e795e69e9f326ea26cf9912e571 ==> HTTP STATUS = 200
    


```python
dfrankoutput
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Rank</th>
      <th>Rider</th>
      <th>Rider No.</th>
      <th>Team</th>
      <th>Times</th>
      <th>Gap</th>
      <th>B</th>
      <th>P</th>
      <th>Year</th>
      <th>Distance (km)</th>
      <th>Number of stages</th>
      <th>TotalSeconds</th>
      <th>GapSeconds</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>TADEJ POGAČAR</td>
      <td>131</td>
      <td>UAE TEAM EMIRATES</td>
      <td>87h 20' 05''</td>
      <td>-</td>
      <td>32'</td>
      <td>NaN</td>
      <td>2020</td>
      <td>3483</td>
      <td>21</td>
      <td>314405</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>PRIMOŽ ROGLIČ</td>
      <td>11</td>
      <td>TEAM JUMBO - VISMA</td>
      <td>87h 21' 04''</td>
      <td>+ 00h 00' 59''</td>
      <td>33'</td>
      <td>NaN</td>
      <td>2020</td>
      <td>3483</td>
      <td>21</td>
      <td>314464</td>
      <td>59</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>RICHIE PORTE</td>
      <td>101</td>
      <td>TREK - SEGAFREDO</td>
      <td>87h 23' 35''</td>
      <td>+ 00h 03' 30''</td>
      <td>04'</td>
      <td>NaN</td>
      <td>2020</td>
      <td>3483</td>
      <td>21</td>
      <td>314615</td>
      <td>210</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4</td>
      <td>MIKEL LANDA MEANA</td>
      <td>61</td>
      <td>BAHRAIN - MCLAREN</td>
      <td>87h 26' 03''</td>
      <td>+ 00h 05' 58''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>2020</td>
      <td>3483</td>
      <td>21</td>
      <td>314763</td>
      <td>358</td>
    </tr>
    <tr>
      <th>4</th>
      <td>5</td>
      <td>ENRIC MAS NICOLAU</td>
      <td>94</td>
      <td>MOVISTAR TEAM</td>
      <td>87h 26' 12''</td>
      <td>+ 00h 06' 07''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>2020</td>
      <td>3483</td>
      <td>21</td>
      <td>314772</td>
      <td>367</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>9062</th>
      <td>6</td>
      <td>JACQUES COOMANS</td>
      <td>63</td>
      <td>TDF 1919 ***</td>
      <td>246h 28' 49''</td>
      <td>+ 15h 21' 34''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>1919</td>
      <td>5560</td>
      <td>15</td>
      <td>887329</td>
      <td>55294</td>
    </tr>
    <tr>
      <th>9063</th>
      <td>7</td>
      <td>LUIGI LUCOTTI</td>
      <td>19</td>
      <td>TDF 1919 ***</td>
      <td>247h 08' 27''</td>
      <td>+ 16h 01' 12''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>1919</td>
      <td>5560</td>
      <td>15</td>
      <td>889707</td>
      <td>57672</td>
    </tr>
    <tr>
      <th>9064</th>
      <td>8</td>
      <td>JOSEPH VAN DAELE</td>
      <td>55</td>
      <td>TDF 1919 ***</td>
      <td>249h 30' 17''</td>
      <td>+ 18h 23' 02''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>1919</td>
      <td>5560</td>
      <td>15</td>
      <td>898217</td>
      <td>66182</td>
    </tr>
    <tr>
      <th>9065</th>
      <td>9</td>
      <td>ALFRED STEUX</td>
      <td>56</td>
      <td>TDF 1919 ***</td>
      <td>251h 36' 16''</td>
      <td>+ 20h 29' 01''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>1919</td>
      <td>5560</td>
      <td>15</td>
      <td>905776</td>
      <td>73741</td>
    </tr>
    <tr>
      <th>9066</th>
      <td>10</td>
      <td>JULES NEMPON</td>
      <td>151</td>
      <td>TDF 1919 ***</td>
      <td>252h 51' 27''</td>
      <td>+ 21h 44' 12''</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>1919</td>
      <td>5560</td>
      <td>15</td>
      <td>910287</td>
      <td>78252</td>
    </tr>
  </tbody>
</table>
<p>9067 rows × 13 columns</p>
</div>



## 3) Clean up the data 



```python
# Fix result types
dfrankoutput["ResultType"] = "time"
dfrankoutput.loc[dfrankoutput["Year"].isin([1905,1906,1908]),"ResultType"] = "null"
dfrankoutput.loc[dfrankoutput["Year"].isin([1907,1909,1910,1911,1912]),"ResultType"] = "points"
```


```python
# Fix this weird bug for e.g. year 2006 and 1997
for year in np.unique(dfrankoutput["Year"]):
    tmp = dfrankoutput[dfrankoutput["Year"]==year].reset_index()
    if tmp.loc[0]["TotalSeconds"] > tmp.loc[2]["TotalSeconds"]:
        print(year)
# Okay seems to be only for 2006 and 1997

```

    1997
    2006
    


```python
tmp = dfrankoutput[dfrankoutput["Year"]==2006].reset_index()
ts = np.array(tmp["TotalSeconds"])
gs = np.array(tmp["GapSeconds"])
ts[1:] = ts[0]+gs[1:]

dfrankoutput.loc[dfrankoutput["Year"]==2006,"TotalSeconds"] = ts

tmp = dfrankoutput[dfrankoutput["Year"]==1997].reset_index()
ts = np.array(tmp["TotalSeconds"])
gs = np.array(tmp["GapSeconds"])
ts[1:] = ts[0]+gs[1:]

dfrankoutput.loc[dfrankoutput["Year"]==1997,"TotalSeconds"] = ts
```

## 4) Write Data to CSV


```python
dfrankoutput.to_csv("../data/TDF_Riders_History.csv")
```


```python
dfstageoutput.to_csv("../data/TDF_Stages_History.csv")
```


```python

```
