add_arrow_axes <- function(plot, line_width = 0.45, arrow_length_mm = 2.5) {
  if (!inherits(plot, "ggplot")) stop("plot must be a ggplot object.")
  plot + ggplot2::theme(
    axis.line = ggplot2::element_line(
      linewidth = line_width,
      arrow = grid::arrow(length = grid::unit(arrow_length_mm, "mm"), type = "closed")
    ),
    panel.border = ggplot2::element_blank(),
    panel.grid = ggplot2::element_blank()
  )
}
