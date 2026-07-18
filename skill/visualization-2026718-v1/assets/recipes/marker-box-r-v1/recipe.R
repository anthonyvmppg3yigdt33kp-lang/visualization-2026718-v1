add_marker_box <- function(plot, xmin, xmax, ymin, ymax, colour = "black", linewidth = 0.45, linetype = 1) {
  if (!inherits(plot, "ggplot")) stop("plot must be a ggplot object.")
  bounds <- c(xmin, xmax, ymin, ymax)
  if (any(!is.finite(bounds)) || xmin >= xmax || ymin >= ymax) stop("Provide finite ordered rectangle bounds.")
  plot + ggplot2::annotate("rect", xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax,
                           fill = NA, colour = colour, linewidth = linewidth, linetype = linetype)
}
