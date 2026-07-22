# Extract an existing Seurat reduction without recomputing or mutating it.
seurat_embedding_frame_v2 <- function(object, reduction = "umap",
                                      group = "seurat_clusters",
                                      dimensions = c(1L, 2L),
                                      x_name = "umap_1",
                                      y_name = "umap_2",
                                      group_name = "cluster") {
  if (!inherits(object, "Seurat")) stop("object must inherit from 'Seurat'.", call. = FALSE)
  if (!requireNamespace("SeuratObject", quietly = TRUE)) stop("Package 'SeuratObject' is required.", call. = FALSE)
  if (length(dimensions) != 2L || any(!is.finite(dimensions)) ||
      any(dimensions < 1) || any(dimensions != as.integer(dimensions))) {
    stop("dimensions must contain two positive integer indices.", call. = FALSE)
  }
  output_names <- c(x_name, y_name, group_name)
  if (anyNA(output_names) || any(!nzchar(output_names)) || anyDuplicated(output_names)) {
    stop("x_name, y_name and group_name must be unique non-empty names.", call. = FALSE)
  }
  reduction_object <- tryCatch(object[[reduction]], error = function(error) NULL)
  if (is.null(reduction_object)) stop("Reduction not found: ", reduction, call. = FALSE)
  coordinates <- SeuratObject::Embeddings(reduction_object)
  if (max(dimensions) > ncol(coordinates)) stop("Requested dimensions exceed the reduction width.", call. = FALSE)
  metadata <- object[[]]
  if (!group %in% names(metadata)) stop("Metadata column not found: ", group, call. = FALSE)
  if (is.null(rownames(coordinates)) || is.null(rownames(metadata))) {
    stop("Coordinates and metadata must have cell row names.", call. = FALSE)
  }
  if (anyDuplicated(rownames(coordinates)) || anyDuplicated(rownames(metadata))) {
    stop("Coordinates and metadata must have unique cell row names.", call. = FALSE)
  }
  missing_cells <- setdiff(rownames(coordinates), rownames(metadata))
  if (length(missing_cells)) stop("Metadata is missing cells present in the reduction.", call. = FALSE)
  metadata <- metadata[rownames(coordinates), , drop = FALSE]
  if (anyNA(metadata[[group]])) stop("Grouping metadata contains missing values.", call. = FALSE)
  out <- data.frame(
    observation_id = rownames(coordinates),
    x = as.numeric(coordinates[, dimensions[1]]),
    y = as.numeric(coordinates[, dimensions[2]]),
    group = metadata[[group]],
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
  names(out)[2:4] <- output_names
  out
}
