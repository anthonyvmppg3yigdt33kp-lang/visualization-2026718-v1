source("recipe.R")
data <- utils::read.csv("../../fixtures/umap_points.csv", check.names = FALSE)
plot_umap_groups_v2(data, group = "cluster", label_groups = TRUE)
