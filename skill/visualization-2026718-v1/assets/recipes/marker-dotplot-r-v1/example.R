source("recipe.R")
dat <- utils::read.csv("../../fixtures/marker_dot.csv", check.names = FALSE)
p <- plot_marker_dotplot(dat, size_breaks = c(0, 50, 100))
print(p)
