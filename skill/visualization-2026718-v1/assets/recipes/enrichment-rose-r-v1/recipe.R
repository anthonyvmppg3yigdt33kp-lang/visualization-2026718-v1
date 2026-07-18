plot_enrichment_rose <- function(
    data,
    pathway = ".pathway",
    magnitude = ".magnitude",
    count = ".count",
    padj = ".padj",
    direction = ".direction",
    top_n = 20L,
    magnitude_label = "GeneRatio / declared enrichment magnitude",
    direction_palette = NULL,
    label_width = 22L) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  if (!is.data.frame(data)) stop("data must be a data.frame.")
  needed <- c(pathway, magnitude, count, padj, if (!is.null(direction)) direction)
  if (anyDuplicated(needed)) stop("pathway, magnitude, count, padj and optional direction must name distinct columns.")
  missing <- setdiff(needed, names(data))
  if (length(missing)) stop("Missing columns: ", paste(missing, collapse = ", "))
  if (!nrow(data)) stop("data must contain at least one pathway.")
  if (length(top_n) != 1L || !is.finite(top_n) || top_n < 1 || top_n != as.integer(top_n)) stop("top_n must be a positive integer.")
  if (length(label_width) != 1L || !is.finite(label_width) || label_width < 8) stop("label_width must be at least 8.")

  d <- data
  d$.pathway_plot <- trimws(as.character(d[[pathway]]))
  d$.magnitude_plot <- suppressWarnings(as.numeric(d[[magnitude]]))
  d$.count_plot <- suppressWarnings(as.numeric(d[[count]]))
  d$.padj_plot <- suppressWarnings(as.numeric(d[[padj]]))
  d$.direction_plot <- if (is.null(direction)) rep("unspecified", nrow(d)) else trimws(as.character(d[[direction]]))
  if (any(is.na(d$.pathway_plot) | d$.pathway_plot == "")) stop("pathway labels must be non-missing and non-empty.")
  if (any(!is.finite(d$.magnitude_plot) | d$.magnitude_plot < 0)) stop("magnitude values must be finite and non-negative.")
  if (any(!is.finite(d$.count_plot) | d$.count_plot < 0)) stop("count values must be finite and non-negative.")
  if (any(!is.finite(d$.padj_plot) | d$.padj_plot <= 0 | d$.padj_plot > 1)) stop("adjusted P values must be in (0, 1].")
  if (any(is.na(d$.direction_plot) | d$.direction_plot == "")) stop("direction labels must be non-missing and non-empty.")

  d <- d[order(d$.padj_plot, -d$.magnitude_plot, d$.pathway_plot), , drop = FALSE]
  d <- utils::head(d, as.integer(top_n))
  d$.neglog10_padj <- -log10(d$.padj_plot)
  d$.pathway_display <- d$.pathway_plot
  if (anyDuplicated(d$.pathway_display)) {
    d$.pathway_display <- paste0(d$.pathway_display, " [", d$.direction_plot, "]")
  }
  d$.pathway_display <- make.unique(d$.pathway_display)
  wrap_label <- function(value) paste(strwrap(value, width = as.integer(label_width)), collapse = "\n")
  d$.pathway_display <- vapply(d$.pathway_display, wrap_label, character(1))
  d$.pathway_display <- factor(d$.pathway_display, levels = d$.pathway_display)

  directions <- unique(d$.direction_plot)
  if (is.null(direction_palette)) {
    direction_palette <- grDevices::hcl.colors(max(3L, length(directions)), palette = "Dark 3")[seq_along(directions)]
    names(direction_palette) <- directions
    if ("unspecified" %in% directions) direction_palette["unspecified"] <- "grey35"
  } else {
    missing_colors <- setdiff(directions, names(direction_palette))
    if (length(missing_colors)) stop("direction_palette lacks: ", paste(missing_colors, collapse = ", "))
  }

  ggplot2::ggplot(d, ggplot2::aes(x = .data[[".pathway_display"]], y = .data[[".magnitude_plot"]])) +
    ggplot2::geom_col(ggplot2::aes(fill = .data[[".neglog10_padj"]]), width = 0.82, colour = "white", linewidth = 0.25) +
    ggplot2::geom_point(
      ggplot2::aes(size = .data[[".count_plot"]], colour = .data[[".direction_plot"]]),
      shape = 21, fill = "white", stroke = 0.9
    ) +
    ggplot2::coord_polar(clip = "off") +
    ggplot2::scale_fill_gradient(low = "#FEE8C8", high = "#B30000", name = "-log10(adjusted P)") +
    ggplot2::scale_colour_manual(values = direction_palette, name = "Direction/category") +
    ggplot2::scale_size_continuous(range = c(2.2, 6.2), name = "Count") +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0, 0.12))) +
    ggplot2::labs(x = NULL, y = magnitude_label) +
    ggplot2::theme_minimal(base_size = 10) +
    ggplot2::theme(
      panel.grid.minor = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_text(size = 8, colour = "grey15"),
      axis.title.y = ggplot2::element_text(size = 9),
      legend.position = "right",
      plot.margin = ggplot2::margin(12, 18, 12, 18)
    )
}
