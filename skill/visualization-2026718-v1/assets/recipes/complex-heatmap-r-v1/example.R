source("recipe.R")
dat <- utils::read.csv("../../fixtures/heatmap_matrix.csv", check.names = FALSE)
mat <- as.matrix(dat[-1]); rownames(mat) <- dat[[1]]
ht <- plot_annotated_heatmap(
  mat,
  row_group = c("Proliferation", "Proliferation", "Immune", "Immune", "Stroma", "Stress"),
  row_title_fontsize = 8
)
ComplexHeatmap::draw(ht)
