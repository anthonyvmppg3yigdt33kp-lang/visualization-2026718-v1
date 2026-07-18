compose_shared_legend <- function(plots, ncol = NULL, position = "right") {
  if (!requireNamespace("patchwork", quietly = TRUE)) stop("Package 'patchwork' is required.")
  if (!is.list(plots) || !length(plots) || !all(vapply(plots, inherits, logical(1), what = "ggplot"))) stop("plots must be a non-empty list of ggplot objects.")
  patchwork::wrap_plots(plots, ncol = ncol, guides = "collect") & ggplot2::theme(legend.position = position)
}
