# Plot precomputed coordinates only; no embedding or observation is changed.
plot_umap_groups_v2 <- function(data, x = "umap_1", y = "umap_2",
                                group = "cluster", palette = NULL,
                                point_size = 0.55, alpha = 0.82,
                                label_groups = TRUE, label_repel = TRUE,
                                label_size = 3.5, label_box_padding = 0.35,
                                show_legend = FALSE, legend_position = "right",
                                base_size = 11, coordinate_padding = 0.12,
                                title = NULL) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.", call. = FALSE)
  needed <- c(x, y, group)
  if (!is.data.frame(data) || !all(needed %in% names(data))) {
    stop("data must contain: ", paste(needed, collapse = ", "), call. = FALSE)
  }
  if (!is.numeric(data[[x]]) || !is.numeric(data[[y]]) ||
      any(!is.finite(data[[x]])) || any(!is.finite(data[[y]]))) {
    stop("x and y must contain finite numeric coordinates.", call. = FALSE)
  }
  numeric_one <- function(value, label, lower, upper = Inf) {
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) || value < lower || value > upper) {
      stop(label, " is outside its declared visual range.", call. = FALSE)
    }
  }
  numeric_one(point_size, "point_size", 0.05, 10)
  numeric_one(alpha, "alpha", 0, 1)
  numeric_one(label_size, "label_size", 1, 20)
  numeric_one(label_box_padding, "label_box_padding", 0, 5)
  numeric_one(base_size, "base_size", 6, 30)
  numeric_one(coordinate_padding, "coordinate_padding", 0, 1)
  if (!legend_position %in% c("right", "left", "top", "bottom", "none")) stop("legend_position is invalid.", call. = FALSE)
  group_values <- data[[group]]
  if (anyNA(group_values)) stop("group contains missing values.", call. = FALSE)
  group_levels <- if (is.factor(group_values)) levels(droplevels(group_values)) else unique(as.character(group_values))
  plot_data <- data
  plot_data[[group]] <- factor(as.character(group_values), levels = group_levels)
  if (!is.null(palette)) {
    # JSON objects are materialized by the runtime as named lists. Normalize
    # that inert representation without changing the declared colour mapping.
    if (is.list(palette) && !is.data.frame(palette)) {
      palette <- unlist(palette, use.names = TRUE)
    }
    if (!is.character(palette) || is.null(names(palette)) || any(!nzchar(names(palette)))) {
      stop("palette must be a named character mapping.", call. = FALSE)
    }
    missing_colours <- setdiff(group_levels, names(palette))
    if (length(missing_colours)) stop("palette is missing group levels: ", paste(missing_colours, collapse = ", "), call. = FALSE)
    palette <- palette[group_levels]
  }
  p <- ggplot2::ggplot(plot_data, ggplot2::aes(x = .data[[x]], y = .data[[y]], colour = .data[[group]])) +
    ggplot2::geom_point(size = point_size, alpha = alpha, stroke = 0) +
    ggplot2::coord_equal() +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = coordinate_padding)) +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = coordinate_padding)) +
    ggplot2::labs(x = x, y = y, colour = group, title = title) +
    ggplot2::theme_classic(base_size = base_size) +
    ggplot2::theme(legend.position = if (isTRUE(show_legend)) legend_position else "none")
  if (!is.null(palette)) p <- p + ggplot2::scale_colour_manual(values = palette, drop = FALSE)
  if (isTRUE(label_groups)) {
    centres <- stats::aggregate(plot_data[c(x, y)], list(group = plot_data[[group]]), stats::median)
    if (isTRUE(label_repel)) {
      if (!requireNamespace("ggrepel", quietly = TRUE)) stop("Package 'ggrepel' is required when label_repel=TRUE.", call. = FALSE)
      p <- p + ggrepel::geom_label_repel(
        data = centres,
        ggplot2::aes(x = .data[[x]], y = .data[[y]], label = .data[["group"]]),
        inherit.aes = FALSE, size = label_size, fontface = "bold",
        box.padding = label_box_padding, min.segment.length = 0,
        seed = 42, max.overlaps = Inf, label.size = 0.15,
        fill = "white", alpha = 0.82, show.legend = FALSE
      )
    } else {
      p <- p + ggplot2::geom_label(
        data = centres,
        ggplot2::aes(x = .data[[x]], y = .data[[y]], label = .data[["group"]]),
        inherit.aes = FALSE, size = label_size, fontface = "bold",
        label.size = 0.15, fill = "white", alpha = 0.82,
        check_overlap = TRUE, show.legend = FALSE
      )
    }
  }
  p
}
