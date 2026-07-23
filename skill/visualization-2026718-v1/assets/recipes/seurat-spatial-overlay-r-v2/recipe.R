# Coordinate-faithful Visium overlays with a declared-only visual parameter set.
.seurat_spatial_contract_v2 <- function(object, assay, image, image_scale) {
  if (!inherits(object, "Seurat")) stop("object must inherit from 'Seurat'.", call. = FALSE)
  if (!requireNamespace("Seurat", quietly = TRUE)) stop("Package 'Seurat' is required.", call. = FALSE)
  if (!requireNamespace("SeuratObject", quietly = TRUE)) stop("Package 'SeuratObject' is required.", call. = FALSE)
  if (!is.character(assay) || length(assay) != 1L || !nzchar(assay) || !assay %in% SeuratObject::Assays(object)) {
    stop("assay must name an existing assay.", call. = FALSE)
  }
  assay_images <- Seurat::Images(object, assay = assay)
  if (!length(assay_images)) stop("No spatial image is associated with assay '", assay, "'.", call. = FALSE)
  if (is.null(image)) {
    if (length(assay_images) != 1L) stop("Multiple images are associated with the assay; select image explicitly.", call. = FALSE)
    image <- assay_images[[1L]]
  }
  if (!is.character(image) || length(image) != 1L || !image %in% assay_images) {
    stop("image must name one image associated with the selected assay.", call. = FALSE)
  }
  spatial_image <- object[[image]]
  if (!identical(SeuratObject::DefaultAssay(spatial_image), assay)) {
    stop("The selected image is not registered to the selected assay.", call. = FALSE)
  }
  scale_factors <- Seurat::ScaleFactors(spatial_image)
  for (scale_name in unique(c("spot", image_scale))) {
    value <- scale_factors[[scale_name]]
    if (is.null(value) || length(value) != 1L || !is.finite(value) || value <= 0) {
      stop("Missing or invalid '", scale_name, "' scale factor.", call. = FALSE)
    }
  }
  assay_barcodes <- SeuratObject::Cells(object[[assay]])
  image_barcodes <- SeuratObject::Cells(spatial_image)
  raw_coordinates <- Seurat::GetTissueCoordinates(spatial_image, scale = NULL)
  scaled_coordinates <- Seurat::GetTissueCoordinates(spatial_image, scale = image_scale)
  coordinate_barcodes <- rownames(raw_coordinates)
  if (!length(assay_barcodes) || !length(image_barcodes) || is.null(coordinate_barcodes)) {
    stop("Assay, image and coordinates must contain barcode identities.", call. = FALSE)
  }
  if (anyDuplicated(assay_barcodes) || anyDuplicated(image_barcodes) || anyDuplicated(coordinate_barcodes)) {
    stop("Assay, image and coordinate barcodes must be unique.", call. = FALSE)
  }
  if (!setequal(image_barcodes, coordinate_barcodes)) {
    stop(
      "Image barcode-coordinate reconciliation failed (missing coordinates: ",
      length(setdiff(image_barcodes, coordinate_barcodes)),
      "; orphan coordinates: ", length(setdiff(coordinate_barcodes, image_barcodes)), ").",
      call. = FALSE
    )
  }
  if (!setequal(assay_barcodes, image_barcodes)) {
    stop(
      "Assay/image barcode reconciliation failed (image barcodes absent from assay: ",
      length(setdiff(image_barcodes, assay_barcodes)),
      "; assay barcodes absent from image: ", length(setdiff(assay_barcodes, image_barcodes)), ").",
      call. = FALSE
    )
  }
  if (ncol(raw_coordinates) < 2L || ncol(scaled_coordinates) < 2L) {
    stop("Tissue coordinates must contain two spatial dimensions.", call. = FALSE)
  }
  raw_numeric <- vapply(raw_coordinates, is.numeric, logical(1))
  scaled_numeric <- vapply(scaled_coordinates, is.numeric, logical(1))
  if (sum(raw_numeric) < 2L || sum(scaled_numeric) < 2L ||
      any(!is.finite(as.matrix(raw_coordinates[, raw_numeric, drop = FALSE]))) ||
      any(!is.finite(as.matrix(scaled_coordinates[, scaled_numeric, drop = FALSE])))) {
    stop("Tissue coordinates must contain two finite numeric dimensions before and after scaling.", call. = FALSE)
  }
  list(image = image, barcodes = image_barcodes, coordinate_rows = nrow(raw_coordinates))
}

plot_seurat_spatial_overlay_v2 <- function(
    object, mode = c("identity", "feature"), assay = "Spatial",
    feature_assay = NULL, image = NULL, group_by = NULL, features = NULL,
    identity_palette = NULL, feature_palette = c("grey90", "#2166AC"),
    crop = TRUE, label = FALSE, label_size = 3.5, label_repel = TRUE,
    pt_size_factor = 1.6, spot_alpha = 1, image_alpha = 1,
    image_scale = c("lowres", "hires"), base_size = 11,
    legend_position = "right", title = NULL) {
  mode <- match.arg(mode)
  image_scale <- match.arg(image_scale)
  logical_one <- function(value, label) {
    if (!is.logical(value) || length(value) != 1L || is.na(value)) stop(label, " must be TRUE or FALSE.", call. = FALSE)
  }
  numeric_one <- function(value, label, lower, upper = Inf) {
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) || value < lower || value > upper) stop(label, " is outside its declared visual range.", call. = FALSE)
  }
  logical_one(crop, "crop")
  logical_one(label, "label")
  logical_one(label_repel, "label_repel")
  numeric_one(label_size, "label_size", 1, 20)
  numeric_one(pt_size_factor, "pt_size_factor", 0.1, 10)
  numeric_one(spot_alpha, "spot_alpha", 0, 1)
  numeric_one(image_alpha, "image_alpha", 0, 1)
  numeric_one(base_size, "base_size", 6, 30)
  if (!legend_position %in% c("right", "left", "top", "bottom", "none")) stop("legend_position is invalid.", call. = FALSE)
  if (is.list(identity_palette) && !is.data.frame(identity_palette)) {
    identity_palette <- unlist(identity_palette, use.names = TRUE)
  }
  if (!is.null(identity_palette) && (!is.character(identity_palette) || !length(identity_palette))) stop("identity_palette must be NULL or a non-empty character vector.", call. = FALSE)
  if (!is.character(feature_palette) || length(feature_palette) < 2L) stop("feature_palette must contain at least two low-to-high colours.", call. = FALSE)
  contract <- .seurat_spatial_contract_v2(object, assay, image, image_scale)
  plot_object <- object
  SeuratObject::DefaultAssay(plot_object) <- assay
  if (mode == "identity") {
    if (!is.null(feature_assay) || !is.null(features)) stop("feature_assay and features are valid only in feature mode.", call. = FALSE)
    if (!is.null(group_by)) {
      if (!is.character(group_by) || length(group_by) != 1L || !nzchar(group_by) || !group_by %in% colnames(plot_object[[]])) {
        stop("group_by must name one existing metadata column.", call. = FALSE)
      }
      if (anyNA(plot_object[[]][contract$barcodes, group_by, drop = TRUE])) stop("group_by contains missing values for selected image barcodes.", call. = FALSE)
    } else if (anyNA(SeuratObject::Idents(plot_object)[contract$barcodes])) {
      stop("Active identities contain missing values for selected image barcodes.", call. = FALSE)
    }
    plot <- Seurat::SpatialDimPlot(
      object = plot_object, group.by = group_by, images = contract$image,
      cols = identity_palette, crop = crop, label = label,
      label.size = label_size, repel = label_repel, combine = TRUE,
      pt.size.factor = pt_size_factor, alpha = c(spot_alpha, spot_alpha),
      image.alpha = image_alpha, image.scale = image_scale
    )
  } else {
    if (!is.null(group_by)) stop("group_by is valid only in identity mode.", call. = FALSE)
    if (!is.character(features) || !length(features) || anyNA(features) || any(!nzchar(features))) stop("features must contain non-empty feature names.", call. = FALSE)
    if (is.null(feature_assay)) feature_assay <- assay
    if (!is.character(feature_assay) || length(feature_assay) != 1L || !feature_assay %in% SeuratObject::Assays(plot_object)) stop("feature_assay must name one existing assay.", call. = FALSE)
    feature_barcodes <- SeuratObject::Cells(plot_object[[feature_assay]])
    if (!setequal(contract$barcodes, feature_barcodes)) stop("Feature-assay/image barcode reconciliation failed.", call. = FALSE)
    if (!length(SeuratObject::Layers(plot_object[[feature_assay]], search = "data"))) stop("The feature assay has no data layer; normalize explicitly before plotting.", call. = FALSE)
    features <- unique(features)
    missing_features <- setdiff(features, rownames(plot_object[[feature_assay]]))
    if (length(missing_features)) stop("Feature(s) absent from feature_assay: ", paste(missing_features, collapse = ", "), call. = FALSE)
    SeuratObject::DefaultAssay(plot_object) <- feature_assay
    plot <- Seurat::SpatialFeaturePlot(
      object = plot_object, features = features, images = contract$image,
      crop = crop, combine = TRUE,
      pt.size.factor = pt_size_factor, alpha = c(spot_alpha, spot_alpha),
      image.alpha = image_alpha, image.scale = image_scale
    )
    # SpatialFeaturePlot fixes its own continuous palette in Seurat 5.5.0.
    # Replace colours only after the official wrapper has built each panel;
    # values, limits, transformations and feature-specific scaling are retained.
    feature_scale <- ggplot2::scale_fill_gradientn(colours = feature_palette)
    plot <- if (inherits(plot, "patchwork")) {
      suppressMessages(plot & feature_scale)
    } else {
      suppressMessages(plot + feature_scale)
    }
  }
  if (!inherits(plot, c("gg", "ggplot", "patchwork"))) stop("Seurat returned an unsupported plot object.", call. = FALSE)
  style <- ggplot2::theme(text = ggplot2::element_text(size = base_size), legend.position = legend_position)
  if (inherits(plot, "patchwork")) {
    plot <- plot & style
    if (!is.null(title)) {
      if (!requireNamespace("patchwork", quietly = TRUE)) stop("Package 'patchwork' is required for a multipanel title.", call. = FALSE)
      plot <- plot + patchwork::plot_annotation(title = title)
    }
  } else {
    plot <- plot + style + ggplot2::labs(title = title)
  }
  plot
}
