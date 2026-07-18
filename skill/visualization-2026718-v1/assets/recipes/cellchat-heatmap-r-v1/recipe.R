plot_cellchat_heatmap <- function(matrix_data, transform = c("none", "log1p"),
                                  colours = c("#F7FBFF", "#6BAED6", "#08306B"),
                                  name = "Communication weight",
                                  cluster_rows = FALSE, cluster_columns = FALSE) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("Package 'ComplexHeatmap' is required.")
  if (!requireNamespace("circlize", quietly = TRUE)) stop("Package 'circlize' is required.")
  transform <- match.arg(transform)
  x <- as.matrix(matrix_data)
  storage.mode(x) <- "double"
  if (!length(x) || any(!is.finite(x)) || any(x < 0)) stop("matrix_data must contain finite non-negative values.")
  displayed <- if (transform == "log1p") log1p(x) else x
  maximum <- max(displayed)
  if (maximum <= 0) maximum <- 1
  colour_function <- circlize::colorRamp2(c(0, maximum / 2, maximum), colours)
  ComplexHeatmap::Heatmap(
    displayed, name = name, col = colour_function,
    cluster_rows = isTRUE(cluster_rows), cluster_columns = isTRUE(cluster_columns),
    rect_gp = grid::gpar(col = "white", lwd = 0.6),
    row_names_gp = grid::gpar(fontsize = 9),
    column_names_gp = grid::gpar(fontsize = 9),
    column_title = paste0("Aggregate inferred communication", if (transform == "log1p") " (log1p)" else ""),
    row_title = "Sender", column_names_rot = 45
  )
}
