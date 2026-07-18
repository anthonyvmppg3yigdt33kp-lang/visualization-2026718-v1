source("recipe.R")
dat <- utils::read.csv("../../fixtures/roc_scores.csv", check.names = FALSE)
result <- plot_roc_curve(dat, positive = "Case")
print(result$plot)
result$auc
