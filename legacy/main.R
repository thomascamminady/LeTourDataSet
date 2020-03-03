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

summary <- read_csv("summary.csv",
                    col_types=cols(
                      year = col_integer(),
                      stages = col_integer(),
                      km = col_double(),
                      avgpace = col_double()
                    ))


# Postprocessing
colnames(df)[colnames(df)=="time"] <- "result"

df$resulttype = "time"

df[df$year==1905,]$resulttype = "empty"
df[df$year==1906,]$resulttype = "empty"
df[df$year==1908,]$resulttype = "empty"

df[df$year==1907,]$resulttype = "points"
df[df$year==1909,]$resulttype = "points"
df[df$year==1910,]$resulttype = "points"
df[df$year==1911,]$resulttype = "points"
df[df$year==1912,]$resulttype = "points"

# add point category
df$points = 0

# for the years were we have points, we mae an error and stored the result as time, shift this to points
df[df$year==1907,]$points = df[df$year==1907,]$h
df[df$year==1909,]$points = df[df$year==1909,]$h
df[df$year==1910,]$points = df[df$year==1910,]$h
df[df$year==1911,]$points = df[df$year==1911,]$h
df[df$year==1912,]$points = df[df$year==1912,]$h

# set time for these entries to zero
df[df$year==1907,]$h = 0
df[df$year==1909,]$h = 0
df[df$year==1910,]$h = 0
df[df$year==1911,]$h = 0
df[df$year==1912,]$h = 0

# weird thing for the last riders in the 1909 tour, there we have entries for minutes and sec though the points were stored. also they are all the same
# kill them
df[df$year==1909,]$m = 0
df[df$year==1909,]$s = 0
# same for 1912
df[df$year==1909,]$m = 0
df[df$year==1909,]$s = 0

df <- df[,c(1,2,3,4,5,6,10,7,8,9,11)]
colnames(df)[colnames(df)=="result"] <- "resultstring"

df2 <- df
df2$distance = 0
df2$stages = 0
df2$touravgpace = 0
for (idx in 1:9040){
  dist = summary[summary$year==df[idx,]$year,]$km
  stages = summary[summary$year==df[idx,]$year,]$stages
  avgpace = summary[summary$year==df[idx,]$year,]$avgpace
  df2[idx,]$distance = dist
  df2[idx,]$stages = stages
  df2[idx,]$touravgpace = avgpace
  
}
df2$personalavgpace = 0
for (idx in 1:9040){
  if (df2[idx,]$resulttype == "time") {
    l = df2[idx,]$distance
    t = df2[idx,]$h*3600+df2[idx,]$m*60+df2[idx,]$s
    x = l/t*3600
    df2[idx,]$personalavgpace = x  
  }
}
colnames(df2)[colnames(df2)=="touravgpace"] <- "winneravgpace"
colnames(df2)[colnames(df2)=="winneravgpace"] <- "avgpace_from_summary"
colnames(df2)[colnames(df2)=="avgpace_from_summary"] <- "tour_avgpace_from_summary"

df <- df2



write_csv(df,'allriders_v2.csv')



