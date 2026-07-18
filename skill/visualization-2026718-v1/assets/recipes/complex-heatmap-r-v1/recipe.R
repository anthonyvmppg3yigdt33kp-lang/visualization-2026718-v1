plot_annotated_heatmap <- function(matrix_data, row_group = NULL, column_group = NULL,
                                   significance = NULL,
                                   colours = c("#006D5B", "#F7F7F7", "#E66101"),
                                   limits = NULL, name = "value",
                                   row_title_fontsize = 8) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("Package 'ComplexHeatmap' is required.")
  if (!requireNamespace("circlize", quietly = TRUE)) stop("Package 'circlize' is required.")
  x <- as.matrix(matrix_data)
  storage.mode(x) <- "double"
  if (!length(x) || any(!is.finite(x), na.rm = TRUE)) stop("matrix_data must contain finite numeric values or NA.")
  if (is.null(limits)) {
    lim <- max(abs(x), na.rm = TRUE)
    if (!is.finite(lim) || lim == 0) lim <- 1
    limits <- c(-lim, 0, lim)
  }
  if (length(limits) != 3 || limits[1] >= limits[2] || limits[2] >= limits[3]) stop("limits must be three increasing values.")
  if (length(row_title_fontsize) != 1 || !is.finite(row_title_fontsize) || row_title_fontsize <= 0) stop("row_title_fontsize must be a positive number.")
  col_fun <- circlize::colorRamp2(limits, colours)
  top_anno <- NULL
  if (!is.null(column_group)) {
    if (length(column_group) != ncol(x)) stop("column_group length must equal ncol(matrix_data).")
    top_anno <- ComplexHeatmap::HeatmapAnnotation(group = column_group)
  }
  split <- NULL
  if (!is.null(row_group)) {
    if (length(row_group) != nrow(x)) stop("row_group length must equal nrow(matrix_data).")
    split <- row_group
  }
  cell_fun <- NULL
  if (!is.null(significance)) {
    significance <- as.matrix(significance)
    if (!identical(dim(significance), dim(x))) stop("significance must have the same dimensions as matrix_data.")
    cell_fun <- function(j, i, x0, y0, width, height, fill) {
      if (!is.na(significance[i, j]) && nzchar(as.character(significance[i, j]))) {
        grid::grid.text(as.character(significance[i, j]), x0, y0, gp = grid::gpar(fontsize = 8))
      }
    }
  }
  ComplexHeatmap::Heatmap(
    x, name = name, col = col_fun, cluster_rows = FALSE, cluster_columns = FALSE,
    row_split = split, top_annotation = top_anno, cell_fun = cell_fun,
    row_names_gp = grid::gpar(fontsize = 9), column_names_gp = grid::gpar(fontsize = 9),
    row_title_gp = grid::gpar(fontsize = row_title_fontsize)
  )
}
