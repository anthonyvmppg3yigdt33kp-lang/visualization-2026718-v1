source("recipe.R")
dat <- utils::read.csv("../../fixtures/umap_points.csv", check.names = FALSE)
p <- plot_umap_groups(dat, group = "cluster", label_groups = TRUE, coordinate_padding = 0.16)
print(p)
