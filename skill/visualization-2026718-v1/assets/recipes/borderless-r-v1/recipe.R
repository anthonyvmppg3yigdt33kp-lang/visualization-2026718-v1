remove_plot_frame <- function(plot, keep_labels = FALSE) {
  if (!inherits(plot, "ggplot")) stop("plot must be a ggplot object.")
  text_element <- if (isTRUE(keep_labels)) ggplot2::element_text() else ggplot2::element_blank()
  plot + ggplot2::theme(
    panel.border = ggplot2::element_blank(), panel.grid = ggplot2::element_blank(),
    axis.line = ggplot2::element_blank(), axis.ticks = ggplot2::element_blank(),
    axis.text = text_element, axis.title = text_element
  )
}
