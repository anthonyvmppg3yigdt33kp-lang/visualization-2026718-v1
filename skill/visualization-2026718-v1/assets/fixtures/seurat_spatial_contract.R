# Synthetic contract fixture only. It is not biological evidence and must not
# replace execution on a real Visium object.
make_seurat_spatial_contract_fixture <- function() {
  if (!requireNamespace("Seurat", quietly = TRUE) ||
      !requireNamespace("SeuratObject", quietly = TRUE) ||
      !requireNamespace("Matrix", quietly = TRUE)) {
    stop("Seurat, SeuratObject, and Matrix are required for this contract fixture.")
  }

  barcodes <- c("AAAC-1", "AAAG-1", "AAAT-1")
  counts <- Matrix::Matrix(
    matrix(
      c(4, 1, 0, 0, 2, 5),
      nrow = 2L,
      dimnames = list(c("Hpca", "Ttr"), barcodes)
    ),
    sparse = TRUE
  )
  metadata <- data.frame(
    cluster = factor(c("A", "A", "B"), levels = c("A", "B")),
    row.names = barcodes
  )
  object <- SeuratObject::CreateSeuratObject(
    counts = counts,
    assay = "Spatial",
    meta.data = metadata,
    project = "spatial-contract-fixture"
  )
  SeuratObject::Idents(object) <- "cluster"

  image_array <- array(1, dim = c(24L, 24L, 4L))
  image_array[, , 1L] <- 0.96
  image_array[, , 2L] <- 0.92
  image_array[, , 3L] <- 0.88
  image_array[, , 4L] <- 1
  coordinates <- data.frame(
    tissue = rep(1L, 3L),
    row = c(1L, 1L, 2L),
    col = c(1L, 2L, 1L),
    imagerow = c(6, 12, 18),
    imagecol = c(6, 18, 12),
    row.names = barcodes
  )
  spatial_image <- methods::new(
    "VisiumV1",
    image = image_array,
    scale.factors = Seurat::scalefactors(spot = 1, fiducial = 1, hires = 1, lowres = 1),
    coordinates = coordinates,
    spot.radius = 0.04,
    assay = "Spatial",
    key = "slice1_",
    misc = list()
  )
  object[["slice1"]] <- spatial_image
  object
}
