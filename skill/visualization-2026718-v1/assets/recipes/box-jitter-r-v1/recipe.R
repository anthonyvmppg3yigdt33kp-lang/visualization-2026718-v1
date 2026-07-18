plot_box_jitter <- function(data, group = "group", value = "value", sample = NULL,
                            palette = NULL, point_size = 2, jitter_width = 0.12,
                            show_mean = TRUE) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(group, value, if (!is.null(sample)) sample)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "))
  p <- ggplot2::ggplot(data, ggplot2::aes(x = .data[[group]], y = .data[[value]], fill = .data[[group]])) +
    ggplot2::geom_boxplot(width = 0.55, outlier.shape = NA, alpha = 0.55, colour = "black") +
    ggplot2::geom_jitter(ggplot2::aes(colour = .data[[group]]), width = jitter_width, height = 0, size = point_size, alpha = 0.85, show.legend = FALSE) +
    ggplot2::labs(x = NULL, y = value, fill = group) + ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(legend.position = "none")
  if (isTRUE(show_mean)) p <- p + ggplot2::stat_summary(fun = mean, geom = "point", shape = 23, size = 3, fill = "white", colour = "black")
  if (!is.null(palette)) p <- p + ggplot2::scale_fill_manual(values = palette) + ggplot2::scale_colour_manual(values = palette)
  p
}
