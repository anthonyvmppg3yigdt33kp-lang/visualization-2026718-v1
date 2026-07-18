.parse_ora_magnitude <- function(values, field_name) {
  if (is.numeric(values)) return(as.numeric(values))
  text <- trimws(as.character(values))
  parsed <- vapply(text, function(value) {
    if (grepl("^[+-]?[0-9]*\\.?[0-9]+/[+-]?[0-9]*\\.?[0-9]+$", value)) {
      parts <- as.numeric(strsplit(value, "/", fixed = TRUE)[[1]])
      if (length(parts) != 2L || !is.finite(parts[2]) || parts[2] <= 0) return(NA_real_)
      return(parts[1] / parts[2])
    }
    suppressWarnings(as.numeric(value))
  }, numeric(1))
  if (any(!is.finite(parsed))) {
    stop(field_name, " must contain finite numeric values or numerator/denominator ratios.")
  }
  parsed
}


adapt_ora_enrichment_table <- function(
    data,
    pathway = "pathway",
    magnitude = "GeneRatio",
    count = "Count",
    padj = "p.adjust",
    direction = NULL) {
  if (!is.data.frame(data)) stop("data must be a data.frame.")
  needed <- c(pathway, magnitude, count, padj, if (!is.null(direction)) direction)
  if (anyDuplicated(needed)) stop("pathway, magnitude, count, padj and optional direction must name distinct columns.")
  missing <- setdiff(needed, names(data))
  if (length(missing)) stop("Missing columns: ", paste(missing, collapse = ", "))
  if (!nrow(data)) stop("data must contain at least one ORA result.")

  pathways <- trimws(as.character(data[[pathway]]))
  magnitudes <- .parse_ora_magnitude(data[[magnitude]], magnitude)
  counts <- suppressWarnings(as.numeric(data[[count]]))
  adjusted_p <- suppressWarnings(as.numeric(data[[padj]]))
  directions <- if (is.null(direction)) rep("unspecified", nrow(data)) else trimws(as.character(data[[direction]]))

  if (any(is.na(pathways) | pathways == "")) stop("pathway labels must be non-missing and non-empty.")
  if (any(!is.finite(magnitudes) | magnitudes < 0)) stop("magnitude values must be finite and non-negative.")
  if (any(!is.finite(counts) | counts < 0)) stop("Count values must be finite and non-negative.")
  if (any(!is.finite(adjusted_p) | adjusted_p <= 0 | adjusted_p > 1)) {
    stop("Adjusted P values must be finite and in (0, 1]; replace numerical-underflow zeros explicitly.")
  }
  if (any(is.na(directions) | directions == "")) stop("direction labels must be non-missing and non-empty when supplied.")

  data.frame(
    .pathway = pathways,
    .magnitude = magnitudes,
    .count = counts,
    .padj = adjusted_p,
    .direction = directions,
    .source_row = seq_len(nrow(data)),
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
}
