# Generalized from the local plotting library. No file I/O or data mutation.
plot_umap_groups <- function(data, x = "umap_1", y = "umap_2", group = "cluster",
                             palette = NULL, point_size = 0.6, alpha = 0.75,
                             label_groups = FALSE, coordinate_padding = 0.16) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(x, y, group)
  if (!is.data.frame(data) || !all(needed %in% names(data))) {
    stop("data must be a data.frame containing: ", paste(needed, collapse = ", "))
  }
  if (!is.numeric(data[[x]]) || !is.numeric(data[[y]])) stop("x and y must be numeric.")
  if (length(coordinate_padding) != 1 || !is.finite(coordinate_padding) || coordinate_padding < 0) stop("coordinate_padding must be a non-negative number.")
  p <- ggplot2::ggplot(data, ggplot2::aes(x = .data[[x]], y = .data[[y]], colour = .data[[group]])) +
    ggplot2::geom_point(size = point_size, alpha = alpha, stroke = 0) +
    ggplot2::coord_equal() +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = coordinate_padding)) +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = coordinate_padding)) +
    ggplot2::labs(x = x, y = y, colour = group) +
    ggplot2::theme_classic(base_size = 11)
  if (!is.null(palette)) p <- p + ggplot2::scale_colour_manual(values = palette)
  if (isTRUE(label_groups)) {
    centres <- stats::aggregate(data[c(x, y)], list(group = data[[group]]), stats::median)
    p <- p + ggplot2::geom_text(
      data = centres,
      ggplot2::aes(x = .data[[x]], y = .data[[y]], label = .data[["group"]]),
      inherit.aes = FALSE, fontface = "bold", check_overlap = TRUE
    )
  }
  p
}
