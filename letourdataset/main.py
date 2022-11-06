from typing import Literal
from letourdataset.TourDataFactory import TourDataFactory

tdf = TourDataFactory()

tdf.download()

index: bool = False
tdf.get_df("TourInfo").to_csv("data/TourInfo.csv", index=index)
tdf.get_df("Rankings").to_csv("data/Rankings.csv", index=index)
tdf.get_df("Starters").to_csv("data/Starters.csv", index=index)
tdf.get_df("Stages").to_csv("data/Stages.csv", index=index)
tdf.get_df("StageWinners").to_csv("data/StageWinners.csv", index=index)
tdf.get_df("JerseyWearers").to_csv("data/JerseyWearers.csv", index=index)
