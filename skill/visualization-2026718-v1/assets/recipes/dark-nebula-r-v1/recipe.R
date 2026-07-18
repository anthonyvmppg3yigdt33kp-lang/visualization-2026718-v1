add_dark_nebula <- function(plot, palette = NULL, halo_size = 2.2,
                            halo_alpha = 0.08, background = "#081018",
                            foreground = "#E8EEF4") {
  if (!inherits(plot, "ggplot")) stop("plot must be a ggplot object.")
  if (!is.numeric(halo_size) || length(halo_size) != 1L || halo_size <= 0) stop("halo_size must be positive.")
  if (!is.numeric(halo_alpha) || length(halo_alpha) != 1L || halo_alpha < 0 || halo_alpha > 1) stop("halo_alpha must be in [0, 1].")
  halo <- ggplot2::geom_point(size = halo_size, alpha = halo_alpha, stroke = 0, show.legend = FALSE)
  plot$layers <- append(list(halo), plot$layers)
  plot <- plot + ggplot2::theme_void(base_size = 11) +
    ggplot2::theme(
      panel.background = ggplot2::element_rect(fill = background, colour = NA),
      plot.background = ggplot2::element_rect(fill = background, colour = NA),
      legend.background = ggplot2::element_rect(fill = background, colour = NA),
      legend.key = ggplot2::element_rect(fill = background, colour = NA),
      legend.text = ggplot2::element_text(colour = foreground),
      legend.title = ggplot2::element_text(colour = foreground),
      text = ggplot2::element_text(colour = foreground),
      plot.margin = ggplot2::margin(8, 8, 8, 8)
    )
  if (!is.null(palette)) plot <- plot + ggplot2::scale_colour_manual(values = palette)
  plot
}
