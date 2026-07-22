# Summarize an existing Seurat expression layer without normalization or mutation.
seurat_marker_summary_v2 <- function(object, features, group = "seurat_clusters",
                                     assay = NULL, layer = "data",
                                     average_transform = c("expm1", "identity"),
                                     scale_average = FALSE, scale_clip = 2.5) {
  if (!inherits(object, "Seurat")) stop("object must inherit from 'Seurat'.", call. = FALSE)
  if (!requireNamespace("SeuratObject", quietly = TRUE)) stop("Package 'SeuratObject' is required.", call. = FALSE)
  if (!requireNamespace("Matrix", quietly = TRUE)) stop("Package 'Matrix' is required.", call. = FALSE)
  average_transform <- match.arg(average_transform)
  features <- unique(as.character(features))
  if (!length(features) || anyNA(features) || any(!nzchar(features))) {
    stop("features must contain unique non-empty feature names.", call. = FALSE)
  }
  if (!is.numeric(scale_clip) || length(scale_clip) != 1L || !is.finite(scale_clip) || scale_clip <= 0) {
    stop("scale_clip must be one positive finite number.", call. = FALSE)
  }
  metadata <- object[[]]
  if (!group %in% names(metadata)) stop("Metadata column not found: ", group, call. = FALSE)
  if (is.null(assay)) assay <- SeuratObject::DefaultAssay(object)
  expression <- SeuratObject::LayerData(object, assay = assay, layer = layer)
  available <- intersect(features, rownames(expression))
  missing <- setdiff(features, rownames(expression))
  if (length(missing)) warning("Features absent from the selected assay/layer were omitted: ", paste(missing, collapse = ", "))
  if (!length(available)) stop("None of the requested features are present in the selected assay/layer.", call. = FALSE)
  if (is.null(colnames(expression)) || is.null(rownames(metadata))) stop("Expression and metadata need cell names.", call. = FALSE)
  if (anyDuplicated(colnames(expression)) || anyDuplicated(rownames(metadata))) stop("Expression and metadata cell names must be unique.", call. = FALSE)
  absent_cells <- setdiff(colnames(expression), rownames(metadata))
  if (length(absent_cells)) stop("Metadata is missing cells present in the expression layer.", call. = FALSE)
  metadata <- metadata[colnames(expression), , drop = FALSE]
  groups <- metadata[[group]]
  if (anyNA(groups)) stop("Grouping metadata contains missing values.", call. = FALSE)
  group_levels <- if (is.factor(groups)) levels(droplevels(groups)) else unique(as.character(groups))
  groups <- factor(as.character(groups), levels = group_levels)
  expression <- expression[available, , drop = FALSE]

  rows <- lapply(group_levels, function(level) {
    selected <- which(groups == level)
    values <- expression[, selected, drop = FALSE]
    average_values <- if (average_transform == "expm1") Matrix::rowMeans(expm1(values)) else Matrix::rowMeans(values)
    data.frame(
      cell_type = level,
      gene = available,
      avg_expression_unscaled = as.numeric(average_values),
      pct_expression = as.numeric(Matrix::rowMeans(values > 0) * 100),
      stringsAsFactors = FALSE
    )
  })
  result <- do.call(rbind, rows)
  result$avg_expression <- result$avg_expression_unscaled
  if (isTRUE(scale_average)) {
    result$avg_expression <- stats::ave(result$avg_expression_unscaled, result$gene, FUN = function(value) {
      spread <- stats::sd(value)
      if (length(value) < 2L || !is.finite(spread) || spread == 0) return(rep(0, length(value)))
      pmax(-scale_clip, pmin(scale_clip, as.numeric(scale(value))))
    })
  }
  result$cell_type <- factor(result$cell_type, levels = group_levels)
  result$gene <- factor(result$gene, levels = rev(available))
  attr(result, "aggregation") <- list(
    assay = assay, layer = layer, average_transform = average_transform,
    scale_average = isTRUE(scale_average), scale_clip = scale_clip,
    denominator = "cells within displayed group"
  )
  rownames(result) <- NULL
  result
}
