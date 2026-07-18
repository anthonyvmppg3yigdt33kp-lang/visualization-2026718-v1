source("recipe.R")
dat <- utils::read.csv("../../fixtures/group_values.csv", check.names = FALSE)
p <- plot_box_jitter(dat, sample = "sample")
print(p)
