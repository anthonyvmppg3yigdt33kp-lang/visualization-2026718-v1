source("recipe.R")
dat <- utils::read.csv("../../fixtures/gsea_results.csv", check.names = FALSE)
p <- plot_gsea_summary(dat, set_size = "set_size", wrap_width = 24)
print(p)
