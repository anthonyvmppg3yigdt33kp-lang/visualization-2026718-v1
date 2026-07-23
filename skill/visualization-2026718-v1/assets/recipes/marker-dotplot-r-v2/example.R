source("recipe.R")
data <- utils::read.csv("../../fixtures/marker_dot.csv", check.names = FALSE)
plot_marker_dotplot_v2(data)
