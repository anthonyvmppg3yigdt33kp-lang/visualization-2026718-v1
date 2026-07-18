# Extract CellChat ligand-receptor communication rows into a stable plotting
# contract. A list with a `communication` data.frame supports deterministic tests.
cellchat_lr_table <- function(object, slot_name = "net", threshold = 0.05,
                              sources_use = NULL, targets_use = NULL) {
  if (inherits(object, "CellChat") && !requireNamespace("CellChat", quietly = TRUE)) stop("Package 'CellChat' is required.")
  if (is.list(object) && !is.null(object$communication)) {
    raw <- object$communication
  } else if (methods::is(object, "CellChat")) {
    raw <- CellChat::subsetCommunication(
      object, slot.name = slot_name, thresh = threshold,
      sources.use = sources_use, targets.use = targets_use
    )
  } else {
    stop("object must be a CellChat object or a list with a 'communication' data.frame.")
  }
  if (!is.data.frame(raw) || !nrow(raw)) stop("No communication rows were available at the declared threshold.")
  choose <- function(candidates, label, required = TRUE) {
    hit <- candidates[candidates %in% names(raw)][1]
    if (is.na(hit) && required) stop("Communication table is missing ", label, ": expected one of ", paste(candidates, collapse = ", "))
    hit
  }
  source_col <- choose(c("source", "sources"), "source")
  target_col <- choose(c("target", "targets"), "target")
  interaction_col <- choose(c("interaction_name_2", "interaction_name", "interaction", "ligand_receptor"), "interaction")
  probability_col <- choose(c("prob", "probability", "weight"), "probability")
  p_col <- choose(c("pval", "p_value", "p.value", "pvalue"), "p-value", required = FALSE)
  pathway_col <- choose(c("pathway_name", "pathway"), "pathway", required = FALSE)
  out <- data.frame(
    source = as.character(raw[[source_col]]),
    target = as.character(raw[[target_col]]),
    interaction = as.character(raw[[interaction_col]]),
    probability = as.numeric(raw[[probability_col]]),
    p_value = if (is.na(p_col)) NA_real_ else as.numeric(raw[[p_col]]),
    pathway = if (is.na(pathway_col)) NA_character_ else as.character(raw[[pathway_col]]),
    stringsAsFactors = FALSE
  )
  if (any(!is.finite(out$probability)) || any(out$probability < 0)) stop("Communication probabilities/weights must be finite and non-negative.")
  if (any(!is.na(out$p_value) & (!is.finite(out$p_value) | out$p_value < 0 | out$p_value > 1))) stop("p-values must be missing or lie in [0, 1].")
  out$source_target <- paste(out$source, out$target, sep = " → ")
  rownames(out) <- NULL
  attr(out, "cellchat_extraction") <- list(slot_name = slot_name, threshold = threshold)
  out
}
