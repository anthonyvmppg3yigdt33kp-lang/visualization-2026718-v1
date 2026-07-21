# Coordinate-faithful Visium spot overlays for caller-supplied Seurat objects.
#
# The recipe validates the Spatial assay, image association, scale factors, and
# barcode/coordinate reconciliation before delegating drawing to Seurat's
# SpatialDimPlot or SpatialFeaturePlot. It does not reconstruct coordinates or
# alter the caller's object.

.seurat_spatial_contract <- function(object, assay, image, image_scale) {
  if (!inherits(object, "Seurat")) {
    stop("object must inherit from 'Seurat'.", call. = FALSE)
  }
  if (!requireNamespace("Seurat", quietly = TRUE)) {
    stop("Package 'Seurat' is required.", call. = FALSE)
  }
  if (!requireNamespace("SeuratObject", quietly = TRUE)) {
    stop("Package 'SeuratObject' is required.", call. = FALSE)
  }
  if (!is.character(assay) || length(assay) != 1L || !nzchar(assay)) {
    stop("assay must be one non-empty name.", call. = FALSE)
  }
  if (!assay %in% SeuratObject::Assays(object)) {
    stop("Assay not found: ", assay, call. = FALSE)
  }

  assay_images <- Seurat::Images(object, assay = assay)
  if (!length(assay_images)) {
    stop("No spatial image is associated with assay '", assay, "'.", call. = FALSE)
  }
  if (is.null(image)) {
    if (length(assay_images) != 1L) {
      stop(
        "Multiple images are associated with assay '", assay,
        "'; select one explicitly with image=.",
        call. = FALSE
      )
    }
    image <- assay_images[[1L]]
  }
  if (!is.character(image) || length(image) != 1L || !nzchar(image)) {
    stop("image must be one non-empty image name.", call. = FALSE)
  }
  if (!image %in% assay_images) {
    stop("Image '", image, "' is not associated with assay '", assay, "'.", call. = FALSE)
  }

  spatial_image <- object[[image]]
  image_assay <- SeuratObject::DefaultAssay(spatial_image)
  if (!identical(image_assay, assay)) {
    stop(
      "Image '", image, "' declares assay '", image_assay,
      "', not '", assay, "'.",
      call. = FALSE
    )
  }

  scale_factors <- tryCatch(
    Seurat::ScaleFactors(spatial_image),
    error = function(error) {
      stop("Could not read image scale factors: ", conditionMessage(error), call. = FALSE)
    }
  )
  required_scales <- unique(c("spot", image_scale))
  scale_values <- vapply(
    required_scales,
    function(scale_name) {
      value <- scale_factors[[scale_name]]
      if (is.null(value) || length(value) != 1L || !is.finite(value) || value <= 0) {
        stop("Missing or invalid '", scale_name, "' scale factor.", call. = FALSE)
      }
      as.numeric(value)
    },
    numeric(1)
  )

  assay_barcodes <- SeuratObject::Cells(object[[assay]])
  image_barcodes <- SeuratObject::Cells(spatial_image)
  raw_coordinates <- Seurat::GetTissueCoordinates(spatial_image, scale = NULL)
  scaled_coordinates <- Seurat::GetTissueCoordinates(spatial_image, scale = image_scale)
  coordinate_barcodes <- rownames(raw_coordinates)

  if (!length(assay_barcodes) || !length(image_barcodes)) {
    stop("Assay and image must both contain barcodes.", call. = FALSE)
  }
  if (is.null(coordinate_barcodes) || any(!nzchar(coordinate_barcodes))) {
    stop("Tissue coordinates must use barcodes as row names.", call. = FALSE)
  }
  if (anyDuplicated(image_barcodes) || anyDuplicated(coordinate_barcodes)) {
    stop("Image barcodes and coordinate row names must be unique.", call. = FALSE)
  }
  if (!setequal(image_barcodes, coordinate_barcodes)) {
    missing_coordinates <- setdiff(image_barcodes, coordinate_barcodes)
    orphan_coordinates <- setdiff(coordinate_barcodes, image_barcodes)
    stop(
      "Image barcode-coordinate reconciliation failed (missing coordinates: ",
      length(missing_coordinates), "; orphan coordinates: ",
      length(orphan_coordinates), ").",
      call. = FALSE
    )
  }
  missing_assay_barcodes <- setdiff(image_barcodes, assay_barcodes)
  missing_image_barcodes <- setdiff(assay_barcodes, image_barcodes)
  if (length(missing_assay_barcodes) || length(missing_image_barcodes)) {
    stop(
      "Assay/image barcode-coordinate reconciliation failed (image barcodes absent from assay: ",
      length(missing_assay_barcodes), "; assay barcodes absent from image coordinates: ",
      length(missing_image_barcodes), ").",
      call. = FALSE
    )
  }
  if (ncol(raw_coordinates) < 2L || ncol(scaled_coordinates) < 2L) {
    stop("Tissue coordinates must contain two spatial dimensions.", call. = FALSE)
  }
  raw_numeric <- vapply(raw_coordinates, is.numeric, logical(1))
  scaled_numeric <- vapply(scaled_coordinates, is.numeric, logical(1))
  if (sum(raw_numeric) < 2L || sum(scaled_numeric) < 2L) {
    stop("Tissue coordinate dimensions must be numeric.", call. = FALSE)
  }
  if (
    any(!is.finite(as.matrix(raw_coordinates[, raw_numeric, drop = FALSE]))) ||
      any(!is.finite(as.matrix(scaled_coordinates[, scaled_numeric, drop = FALSE])))
  ) {
    stop("Tissue coordinates must be finite before and after scaling.", call. = FALSE)
  }

  list(
    image = image,
    barcodes = image_barcodes,
    scale_factors = scale_values,
    coordinate_rows = nrow(raw_coordinates)
  )
}


plot_seurat_spatial_overlay <- function(
    object,
    mode = c("identity", "feature"),
    assay = "Spatial",
    feature_assay = NULL,
    image = NULL,
    group_by = NULL,
    features = NULL,
    cols = NULL,
    crop = TRUE,
    label = FALSE,
    label_size = 3.5,
    label_repel = TRUE,
    pt_size_factor = 1.6,
    spot_alpha = 1,
    image_alpha = 1,
    image_scale = c("lowres", "hires")) {
  mode <- match.arg(mode)
  image_scale <- match.arg(image_scale)
  if (!is.logical(crop) || length(crop) != 1L || is.na(crop)) {
    stop("crop must be TRUE or FALSE.", call. = FALSE)
  }
  if (!is.logical(label) || length(label) != 1L || is.na(label)) {
    stop("label must be TRUE or FALSE.", call. = FALSE)
  }
  if (!is.numeric(label_size) || length(label_size) != 1L ||
      !is.finite(label_size) || label_size <= 0) {
    stop("label_size must be one positive finite number.", call. = FALSE)
  }
  if (!is.logical(label_repel) || length(label_repel) != 1L || is.na(label_repel)) {
    stop("label_repel must be TRUE or FALSE.", call. = FALSE)
  }
  if (!is.numeric(pt_size_factor) || length(pt_size_factor) != 1L ||
      !is.finite(pt_size_factor) || pt_size_factor <= 0) {
    stop("pt_size_factor must be one positive finite number.", call. = FALSE)
  }
  if (!is.numeric(spot_alpha) || length(spot_alpha) != 1L ||
      !is.finite(spot_alpha) || spot_alpha < 0 || spot_alpha > 1) {
    stop("spot_alpha must be one finite number in [0, 1].", call. = FALSE)
  }
  if (!is.numeric(image_alpha) || length(image_alpha) != 1L ||
      !is.finite(image_alpha) || image_alpha < 0 || image_alpha > 1) {
    stop("image_alpha must be one finite number in [0, 1].", call. = FALSE)
  }

  contract <- .seurat_spatial_contract(object, assay, image, image_scale)

  # R uses copy-on-modify here: the caller's object remains unchanged while the
  # selected Spatial assay becomes explicit for Seurat's plotting API.
  plot_object <- object
  SeuratObject::DefaultAssay(plot_object) <- assay

  if (mode == "identity") {
    if (!is.null(feature_assay)) {
      stop("feature_assay is only valid when mode='feature'.", call. = FALSE)
    }
    if (!is.null(features)) {
      stop("features is only valid when mode='feature'.", call. = FALSE)
    }
    if (!is.null(group_by)) {
      if (!is.character(group_by) || length(group_by) != 1L || !nzchar(group_by)) {
        stop("group_by must be NULL or one non-empty metadata column.", call. = FALSE)
      }
      metadata <- plot_object[[]]
      if (!group_by %in% colnames(metadata)) {
        stop("Metadata column not found: ", group_by, call. = FALSE)
      }
      if (anyNA(metadata[contract$barcodes, group_by, drop = TRUE])) {
        stop("group_by contains missing values for selected image barcodes.", call. = FALSE)
      }
    } else {
      identities <- SeuratObject::Idents(plot_object)[contract$barcodes]
      if (anyNA(identities)) {
        stop("Active identities contain missing values for selected image barcodes.", call. = FALSE)
      }
    }
    plot <- Seurat::SpatialDimPlot(
      object = plot_object,
      group.by = group_by,
      images = contract$image,
      cols = cols,
      crop = crop,
      label = label,
      label.size = label_size,
      repel = label_repel,
      combine = TRUE,
      pt.size.factor = pt_size_factor,
      alpha = c(spot_alpha, spot_alpha),
      image.alpha = image_alpha,
      image.scale = image_scale
    )
  } else {
    if (!is.null(group_by)) {
      stop("group_by is only valid when mode='identity'.", call. = FALSE)
    }
    if (!is.character(features) || !length(features) || any(!nzchar(features))) {
      stop("features must contain at least one non-empty feature name.", call. = FALSE)
    }
    if (is.null(feature_assay)) {
      feature_assay <- assay
    }
    if (!is.character(feature_assay) || length(feature_assay) != 1L || !nzchar(feature_assay)) {
      stop("feature_assay must be NULL or one non-empty assay name.", call. = FALSE)
    }
    if (!feature_assay %in% SeuratObject::Assays(plot_object)) {
      stop("Feature assay not found: ", feature_assay, call. = FALSE)
    }
    feature_barcodes <- SeuratObject::Cells(plot_object[[feature_assay]])
    missing_feature_barcodes <- setdiff(contract$barcodes, feature_barcodes)
    orphan_feature_barcodes <- setdiff(feature_barcodes, contract$barcodes)
    if (length(missing_feature_barcodes) || length(orphan_feature_barcodes)) {
      stop(
        "Feature-assay/image barcode-coordinate reconciliation failed (image barcodes absent from feature assay: ",
        length(missing_feature_barcodes), "; feature-assay barcodes absent from image coordinates: ",
        length(orphan_feature_barcodes), ").",
        call. = FALSE
      )
    }
    data_layers <- SeuratObject::Layers(plot_object[[feature_assay]], search = "data")
    if (!length(data_layers)) {
      stop(
        "Feature assay '", feature_assay,
        "' has no data layer; normalize it explicitly before plotting.",
        call. = FALSE
      )
    }
    features <- unique(features)
    missing_features <- setdiff(features, rownames(plot_object[[feature_assay]]))
    if (length(missing_features)) {
      stop("Feature(s) absent from assay '", feature_assay, "': ", paste(missing_features, collapse = ", "), call. = FALSE)
    }
    SeuratObject::DefaultAssay(plot_object) <- feature_assay
    plot <- Seurat::SpatialFeaturePlot(
      object = plot_object,
      features = features,
      images = contract$image,
      crop = crop,
      combine = TRUE,
      pt.size.factor = pt_size_factor,
      alpha = c(spot_alpha, spot_alpha),
      image.alpha = image_alpha,
      image.scale = image_scale
    )
  }

  if (!inherits(plot, c("gg", "ggplot", "patchwork"))) {
    stop("Seurat returned an unsupported plot object.", call. = FALSE)
  }
  plot
}
