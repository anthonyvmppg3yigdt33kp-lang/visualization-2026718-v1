plot_marker_dotplot <- function(data, cell_type = "cell_type", feature = "gene",
                                average = "avg_expression", percent = "pct_expression",
                                palette = c("#2166AC", "#F7F7F7", "#B2182B"),
                                size_range = c(0.5, 7), size_breaks = c(0, 50, 100),
                                fill_title = "Average expression",
                                size_title = "Percent expressed") {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(cell_type, feature, average, percent)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "))
  if (any(data[[percent]] < 0 | data[[percent]] > 100, na.rm = TRUE)) stop("Percent values must be in [0, 100].")
  if (!is.numeric(size_breaks) || any(!is.finite(size_breaks)) || any(size_breaks < 0 | size_breaks > 100)) stop("size_breaks must be finite values in [0, 100].")
  ggplot2::ggplot(data, ggplot2::aes(x = .data[[cell_type]], y = .data[[feature]])) +
    ggplot2::geom_point(ggplot2::aes(fill = .data[[average]], size = .data[[percent]]), shape = 21, colour = "black", stroke = 0.35) +
    ggplot2::scale_fill_gradientn(colours = palette, na.value = "grey90") +
    ggplot2::scale_size(range = size_range, limits = c(0, 100), breaks = size_breaks) +
    ggplot2::labs(x = NULL, y = NULL, fill = fill_title, size = size_title) +
    ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, hjust = 1), axis.text.y = ggplot2::element_text(face = "italic")) +
    ggplot2::guides(size = ggplot2::guide_legend(order = 1, title.position = "top"), fill = ggplot2::guide_colourbar(order = 2, title.position = "top"))
}
