plot_gsea_summary <- function(data, pathway = "pathway", nes = "nes", padj = "padj",
                              set_size = NULL, alpha_cutoff = 0.05, max_pathways = 20,
                              wrap_width = 24) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(pathway, nes, padj, if (!is.null(set_size)) set_size)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "))
  if (any(!is.finite(data[[nes]]))) stop("NES values must all be finite.")
  if (any(!is.finite(data[[padj]]) | data[[padj]] <= 0 | data[[padj]] > 1)) {
    stop("Adjusted P values must all be finite and in (0, 1]; replace underflow zeros explicitly before plotting.")
  }
  if (length(wrap_width) != 1 || !is.finite(wrap_width) || wrap_width < 8) stop("wrap_width must be a number >= 8.")
  d <- data
  d$.nes <- as.numeric(d[[nes]])
  d$.padj <- as.numeric(d[[padj]])
  d$.pathway <- as.character(d[[pathway]])
  d$.significant <- d$.padj < alpha_cutoff
  d <- d[order(d$.padj, -abs(d$.nes)), , drop = FALSE]
  d <- utils::head(d, max_pathways)
  d$.pathway <- factor(d$.pathway, levels = rev(d$.pathway))
  wrap_pathway <- function(labels) {
    vapply(gsub("_", " ", labels, fixed = TRUE), function(value) paste(strwrap(value, width = wrap_width), collapse = "\n"), character(1))
  }
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .data[[".nes"]], y = .data[[".pathway"]], colour = .data[[".padj"]])) +
    ggplot2::geom_vline(xintercept = 0, colour = "grey60", linewidth = 0.35) +
    ggplot2::geom_segment(ggplot2::aes(x = 0, xend = .data[[".nes"]], yend = .data[[".pathway"]]), linewidth = 0.7) +
    ggplot2::geom_point(ggplot2::aes(shape = .data[[".significant"]]), size = 3) +
    ggplot2::scale_colour_viridis_c(trans = "log10", direction = -1, name = "adjusted P") +
    ggplot2::scale_shape_manual(values = c(`TRUE` = 16, `FALSE` = 1), name = paste0("adjusted P < ", alpha_cutoff)) +
    ggplot2::scale_y_discrete(labels = wrap_pathway) +
    ggplot2::labs(x = "Normalized enrichment score (NES)", y = NULL) + ggplot2::theme_classic(base_size = 11) +
    ggplot2::theme(legend.title = ggplot2::element_text(size = 9), legend.text = ggplot2::element_text(size = 8))
  if (!is.null(set_size)) p <- p + ggplot2::geom_point(ggplot2::aes(size = .data[[set_size]])) + ggplot2::labs(size = "Set size")
  p
}
