source("recipe.R")
long <- utils::read.csv("../../fixtures/chord_matrix.csv", check.names = FALSE)
mat <- as.matrix(long[-1]); rownames(mat) <- long[[1]]
cols <- c(T_cell = "#377EB8", B_cell = "#4DAF4A", Myeloid = "#E41A1C")
plot_cellchat_chord(mat, group_colours = cols)
