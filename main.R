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


ggplot(data=summary)+
  geom_point(aes(x=year,y=km,colour="Distance"))+
  geom_point(aes(x=year,y=avgpace*100,colour="Pace"))+
  scale_y_continuous(sec.axis = sec_axis(~.*0.01, name = "Avg. Pace in km/h"))+
  scale_colour_manual(values = c("blue", "red"))+
  labs(y = "Distance in km",
              x = "Year",
              colour = "Parameter")+
  theme(legend.position = c(0.8, 0.9))+
  ggtitle("Le Tour de France")+
  theme_minimal()



df$overalltime <- df$h*3600+df$m*60+df$s
ggplot(data=df,aes(group=year,y=df$overalltime))+
  geom_boxplot()

ggplot(data=df)+geom_point(aes(x=year,y=overalltime))

