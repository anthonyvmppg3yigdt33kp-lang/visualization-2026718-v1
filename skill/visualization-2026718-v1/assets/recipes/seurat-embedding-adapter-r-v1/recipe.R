# Convert a caller-supplied Seurat reduction and metadata column into the
# backend-neutral data-frame contract consumed by umap-dataframe-r-v1.
seurat_embedding_frame <- function(object, reduction = "umap", group = "seurat_clusters",
                                   dimensions = c(1L, 2L), x_name = "umap_1",
                                   y_name = "umap_2", group_name = "cluster") {
  if (!inherits(object, "Seurat")) stop("object must inherit from 'Seurat'.")
  if (!requireNamespace("SeuratObject", quietly = TRUE)) stop("Package 'SeuratObject' is required to read a Seurat object.")
  if (length(dimensions) != 2L || any(!is.finite(dimensions)) || any(dimensions < 1) || any(dimensions != as.integer(dimensions))) {
    stop("dimensions must contain two positive integer indices.")
  }
  reduction_object <- tryCatch(object[[reduction]], error = function(e) NULL)
  if (is.null(reduction_object)) stop("Reduction not found: ", reduction)
  coordinates <- SeuratObject::Embeddings(reduction_object)
  if (max(dimensions) > ncol(coordinates)) stop("Requested dimensions exceed the reduction width.")
  metadata <- object[[]]
  if (!group %in% names(metadata)) stop("Metadata column not found: ", group)
  if (is.null(rownames(coordinates)) || is.null(rownames(metadata))) stop("Coordinates and metadata must have cell row names.")
  missing_cells <- setdiff(rownames(coordinates), rownames(metadata))
  if (length(missing_cells)) stop("Metadata is missing cells present in the reduction.")
  metadata <- metadata[rownames(coordinates), , drop = FALSE]
  out <- data.frame(
    observation_id = rownames(coordinates),
    x = as.numeric(coordinates[, dimensions[1]]),
    y = as.numeric(coordinates[, dimensions[2]]),
    group = metadata[[group]],
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
  names(out)[2:4] <- c(x_name, y_name, group_name)
  out
}
