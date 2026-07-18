source("recipe.R")
dat <- utils::read.csv("../../fixtures/volcano_markers.csv", check.names = FALSE)
p <- plot_grouped_volcano(dat, top_n = 2, legend_position = "bottom")
print(p)
