plot_marker_dotplot_v2 <- function(data, cell_type = "cell_type", feature = "gene",
                                   average = "avg_expression", percent = "pct_expression",
                                   palette = c("#2166AC", "#F7F7F7", "#B2182B"),
                                   size_range = c(0.5, 7), size_breaks = c(0, 50, 100),
                                   fill_title = "Scaled average expression",
                                   size_title = "Percent expressed",
                                   base_size = 11, x_text_angle = 90,
                                   x_text_size = 9, y_text_size = 9,
                                   legend_position = "right", point_border_colour = "black",
                                   point_border_width = 0.3, title = NULL) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.", call. = FALSE)
  needed <- c(cell_type, feature, average, percent)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "), call. = FALSE)
  if (!is.numeric(data[[average]]) || !is.numeric(data[[percent]])) stop("average and percent columns must be numeric.", call. = FALSE)
  if (any(!is.finite(data[[average]]), na.rm = TRUE) || any(!is.finite(data[[percent]]), na.rm = TRUE)) stop("average and percent values must be finite.", call. = FALSE)
  if (any(data[[percent]] < 0 | data[[percent]] > 100, na.rm = TRUE)) stop("Percent values must be in [0, 100].", call. = FALSE)
  if (!is.character(palette) || length(palette) < 2L) stop("palette must contain at least two colours.", call. = FALSE)
  if (!is.numeric(size_range) || length(size_range) != 2L || any(!is.finite(size_range)) || any(size_range <= 0) || size_range[1] > size_range[2]) stop("size_range must contain two ordered positive values.", call. = FALSE)
  if (!is.numeric(size_breaks) || any(!is.finite(size_breaks)) || any(size_breaks < 0 | size_breaks > 100)) stop("size_breaks must be finite values in [0, 100].", call. = FALSE)
  if (!legend_position %in% c("right", "left", "top", "bottom", "none")) stop("legend_position is invalid.", call. = FALSE)
  numeric_range <- function(value, label, lower, upper) {
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) || value < lower || value > upper) stop(label, " is outside its declared visual range.", call. = FALSE)
  }
  numeric_range(base_size, "base_size", 6, 30)
  numeric_range(x_text_angle, "x_text_angle", 0, 90)
  numeric_range(x_text_size, "x_text_size", 5, 30)
  numeric_range(y_text_size, "y_text_size", 5, 30)
  numeric_range(point_border_width, "point_border_width", 0, 3)
  ggplot2::ggplot(data, ggplot2::aes(x = .data[[cell_type]], y = .data[[feature]])) +
    ggplot2::geom_point(
      ggplot2::aes(fill = .data[[average]], size = .data[[percent]]),
      shape = 21, colour = point_border_colour, stroke = point_border_width
    ) +
    ggplot2::scale_fill_gradientn(colours = palette, na.value = "grey90") +
    ggplot2::scale_size(range = size_range, limits = c(0, 100), breaks = size_breaks) +
    ggplot2::labs(x = NULL, y = NULL, fill = fill_title, size = size_title, title = title) +
    ggplot2::theme_classic(base_size = base_size) +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(angle = x_text_angle, hjust = 1, vjust = 0.5, size = x_text_size),
      axis.text.y = ggplot2::element_text(face = "italic", size = y_text_size),
      legend.position = legend_position
    ) +
    ggplot2::guides(
      size = ggplot2::guide_legend(order = 1, title.position = "top"),
      fill = ggplot2::guide_colourbar(order = 2, title.position = "top")
    )
}
