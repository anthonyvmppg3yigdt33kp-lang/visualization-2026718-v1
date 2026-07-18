export_publication_plot <- function(plot, path, width, height, units = "in", dpi = 600, bg = "white") {
  if (!inherits(plot, c("ggplot", "patchwork"))) stop("plot must be a ggplot or patchwork object.")
  if (!is.character(path) || length(path) != 1L || !nzchar(path)) stop("path must be an explicit non-empty file path.")
  ext <- tolower(tools::file_ext(path))
  if (!ext %in% c("pdf", "svg", "png", "tif", "tiff")) stop("Supported formats: pdf, svg, png, tif, tiff.")
  if (!is.numeric(width) || !is.numeric(height) || width <= 0 || height <= 0) stop("width and height must be positive.")
  ggplot2::ggsave(filename = path, plot = plot, width = width, height = height, units = units, dpi = dpi, bg = bg, limitsize = TRUE)
  invisible(normalizePath(path, winslash = "/", mustWork = FALSE))
}
