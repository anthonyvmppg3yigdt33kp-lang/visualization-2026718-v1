add_repel_labels <- function(plot, label_data, x, y, label, max_overlaps = 30, seed = 1) {
  if (!inherits(plot, "ggplot")) stop("plot must be a ggplot object.")
  if (!requireNamespace("ggrepel", quietly = TRUE)) stop("Package 'ggrepel' is required.")
  needed <- c(x, y, label)
  if (!is.data.frame(label_data) || !all(needed %in% names(label_data))) stop("label_data is missing required columns.")
  plot + ggrepel::geom_text_repel(
    data = label_data, ggplot2::aes(x = .data[[x]], y = .data[[y]], label = .data[[label]]),
    inherit.aes = FALSE, max.overlaps = max_overlaps, seed = seed, size = 3
  )
}
