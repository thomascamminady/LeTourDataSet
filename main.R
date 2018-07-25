library(tidyverse)
df <- read_csv("allriders.csv", 
               col_types = cols(
                 year = col_integer(),
                 rank = col_integer(),
                 name = col_character(),
                 id = col_integer(),
                 team = col_character(),
                 time = col_character(),
                 h = col_integer(),
                 m = col_integer(),
                 s = col_integer()
               )
)



