plot_roc_curve <- function(data, outcome = "outcome", score = "score", positive = NULL,
                           direction = "auto", line_colour = "#2166AC") {
  if (!requireNamespace("pROC", quietly = TRUE)) stop("Package 'pROC' is required.")
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Package 'ggplot2' is required.")
  if (!is.data.frame(data) || !all(c(outcome, score) %in% names(data))) stop("data must contain outcome and score columns.")
  y <- factor(data[[outcome]])
  if (nlevels(y) != 2) stop("outcome must have exactly two observed levels.")
  if (!is.null(positive)) {
    if (!positive %in% levels(y)) stop("positive must be an observed outcome level.")
    y <- stats::relevel(y, ref = setdiff(levels(y), positive)[1])
  }
  roc_obj <- pROC::roc(response = y, predictor = as.numeric(data[[score]]), direction = direction, quiet = TRUE)
  curve <- data.frame(fpr = 1 - roc_obj$specificities, sensitivity = roc_obj$sensitivities)
  auc_value <- as.numeric(pROC::auc(roc_obj))
  p <- ggplot2::ggplot(curve, ggplot2::aes(x = .data[["fpr"]], y = .data[["sensitivity"]])) +
    ggplot2::geom_abline(slope = 1, intercept = 0, colour = "grey70", linewidth = 0.4) +
    ggplot2::geom_path(colour = line_colour, linewidth = 0.9) +
    ggplot2::coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    ggplot2::annotate("text", x = 0.65, y = 0.12, label = sprintf("AUC = %.3f", auc_value), hjust = 0) +
    ggplot2::labs(x = "1 - Specificity", y = "Sensitivity") + ggplot2::theme_classic(base_size = 11)
  structure(list(plot = p, roc = roc_obj, auc = auc_value), class = "plot_recipe_roc")
}
