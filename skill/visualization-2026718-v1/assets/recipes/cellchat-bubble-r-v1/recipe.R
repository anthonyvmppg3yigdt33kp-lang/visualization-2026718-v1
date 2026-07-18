plot_cellchat_bubble <- function(data, source = "source", target = "target",
                                 interaction = "interaction", probability = "probability",
                                 p_value = "p_value", top_n = 30,
                                 p_threshold = 0.05, p_floor = 1e-4,
                                 palette = c("#F7FBFF", "#6BAED6", "#08306B")) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  needed <- c(source, target, interaction, probability, p_value)
  if (!is.data.frame(data) || !all(needed %in% names(data))) stop("Missing columns: ", paste(setdiff(needed, names(data)), collapse = ", "))
  shown <- data[, needed, drop = FALSE]
  names(shown) <- c("source", "target", "interaction", "probability", "p_value")
  shown <- shown[is.finite(shown$probability) & shown$probability >= 0, , drop = FALSE]
  if (!is.null(p_threshold)) shown <- shown[is.na(shown$p_value) | shown$p_value <= p_threshold, , drop = FALSE]
  if (!nrow(shown)) stop("No communication rows remain after the declared filtering.")
  shown <- shown[order(shown$probability, decreasing = TRUE, na.last = NA), , drop = FALSE]
  if (!is.null(top_n)) shown <- utils::head(shown, as.integer(top_n))
  shown$source_target <- paste(shown$source, shown$target, sep = " → ")
  shown$minus_log10_p <- ifelse(is.na(shown$p_value), NA_real_, -log10(pmax(shown$p_value, p_floor)))
  shown$source_target <- factor(shown$source_target, levels = unique(shown$source_target))
  shown$interaction <- factor(shown$interaction, levels = rev(unique(shown$interaction)))
  ggplot2::ggplot(shown, ggplot2::aes(x = .data$source_target, y = .data$interaction)) +
    ggplot2::geom_hline(yintercept = seq_along(levels(shown$interaction)), colour = "#EDF2F7", linewidth = 0.35) +
    ggplot2::geom_vline(xintercept = seq_along(levels(shown$source_target)), colour = "#EDF2F7", linewidth = 0.35) +
    ggplot2::geom_point(ggplot2::aes(fill = .data$probability, size = .data$minus_log10_p), shape = 21, colour = "#253746", stroke = 0.3) +
    ggplot2::scale_fill_gradientn(colours = palette, name = "Communication\nprobability") +
    ggplot2::scale_size_continuous(range = c(1.8, 7), name = expression(-log[10](italic(p)))) +
    ggplot2::labs(x = "Sender → receiver", y = "Ligand–receptor interaction") +
    ggplot2::theme_minimal(base_size = 10) +
    ggplot2::theme(panel.grid = ggplot2::element_blank(), axis.text.x = ggplot2::element_text(angle = 55, hjust = 1, vjust = 1), axis.text.y = ggplot2::element_text(face = "italic"), legend.position = "right", plot.margin = ggplot2::margin(6, 10, 6, 6))
}
