source("recipe.R")
mock <- list(net = list(weight = matrix(
  c(0, 0.4, 0.7, 0.3, 0, 0.2, 0.5, 0.1, 0),
  nrow = 3, byrow = TRUE,
  dimnames = list(c("T_cell", "B_cell", "Myeloid"), c("T_cell", "B_cell", "Myeloid"))
)))
matrix_result <- cellchat_interaction_data(mock, output = "matrix")
long_result <- cellchat_interaction_data(mock, output = "long", drop_zero = TRUE)
stopifnot(is.matrix(matrix_result), all(c("source", "target", "weight") %in% names(long_result)))
