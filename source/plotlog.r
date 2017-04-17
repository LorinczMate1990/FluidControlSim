#!/usr/bin/r -i

library('reshape')
library('ggplot2')

logfile = readline(prompt = "Melyik log-fájlt ábrázoljam?\n")
path = paste("logs/", logfile, ".log", sep="")

print(path)

logdata = read.csv(path)

data_melted = melt(logdata, id=c('timestamp'))
p <- ggplot(data_melted, aes(x=timestamp, y=value, color=variable, group=variable)) + geom_line(aes(linetype=variable))
print(p)
