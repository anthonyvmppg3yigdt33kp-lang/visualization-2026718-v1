plot_grouped_volcano <- function(data, cluster = "cluster", effect = "log2fc", padj = "padj", label = "gene",
                                 alpha_cutoff = 0.05, top_n = 3,
                                 significant_colour = "#F05F63", nonsignificant_colour = "#202020",
                                 legend_position = "bottom") {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(cluster, effect, padj, label)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "))
  if (!legend_position %in% c("bottom", "right", "none")) stop("legend_position must be 'bottom', 'right', or 'none'.")
  d <- data
  d$.cluster <- factor(d[[cluster]], levels = unique(d[[cluster]]))
  d$.effect <- as.numeric(d[[effect]])
  d$.significant <- is.finite(d[[padj]]) & d[[padj]] < alpha_cutoff
  ord <- order(d$.cluster, -abs(d$.effect), na.last = NA)
  top <- d[ord, , drop = FALSE]
  top <- top[ave(seq_len(nrow(top)), top$.cluster, FUN = seq_along) <= top_n & top$.significant, , drop = FALSE]
  p <- ggplot2::ggplot(d, ggplot2::aes(x = .data[[".cluster"]], y = .data[[".effect"]], colour = .data[[".significant"]])) +
    ggplot2::geom_jitter(width = 0.28, height = 0, size = 1, alpha = 0.75) +
    ggplot2::geom_hline(yintercept = 0, linewidth = 0.3) +
    ggplot2::scale_colour_manual(values = c(`TRUE` = significant_colour, `FALSE` = nonsignificant_colour), name = paste0("adjusted P < ", alpha_cutoff)) +
    ggplot2::labs(x = "Group", y = effect) + ggplot2::theme_classic(base_size = 11) +
    ggplot2::guides(colour = ggplot2::guide_legend(title.position = "top", nrow = 1, byrow = TRUE, override.aes = list(size = 2, alpha = 1))) +
    ggplot2::theme(legend.position = legend_position, legend.direction = "horizontal", legend.justification = "left")
  if (nrow(top)) {
    if (requireNamespace("ggrepel", quietly = TRUE)) {
      p <- p + ggrepel::geom_text_repel(data = top, ggplot2::aes(label = .data[[label]]), size = 3, max.overlaps = Inf, show.legend = FALSE)
    } else {
      p <- p + ggplot2::geom_text(data = top, ggplot2::aes(label = .data[[label]]), size = 3, check_overlap = TRUE, show.legend = FALSE, vjust = -0.5)
    }
  }
  p
}
