# Extract CellChat's aggregate network matrix into the contract used by the
# chord recipe. A list-shaped mock is supported for deterministic testing.
cellchat_interaction_data <- function(object, measure = "weight",
                                      output = c("matrix", "long"), drop_zero = FALSE) {
  output <- match.arg(output)
  if (inherits(object, "CellChat") && !requireNamespace("CellChat", quietly = TRUE)) stop("Package 'CellChat' is required.")
  net <- NULL
  if (is.list(object) && !is.null(object$net)) {
    net <- object$net
  } else if (methods::is(object, "CellChat")) {
    net <- methods::slot(object, "net")
  }
  if (is.null(net) || !is.list(net)) stop("object must be a CellChat object or a list with a 'net' list.")
  if (!measure %in% names(net)) stop("Network measure not found: ", measure)
  matrix_data <- as.matrix(net[[measure]])
  storage.mode(matrix_data) <- "double"
  if (nrow(matrix_data) != ncol(matrix_data)) stop("The selected CellChat aggregate network must be square.")
  if (is.null(rownames(matrix_data)) || is.null(colnames(matrix_data))) stop("The network needs source and target names.")
  if (!setequal(rownames(matrix_data), colnames(matrix_data))) stop("Source and target node sets must match.")
  matrix_data <- matrix_data[rownames(matrix_data), rownames(matrix_data), drop = FALSE]
  if (any(!is.finite(matrix_data)) || any(matrix_data < 0)) stop("Network weights must be finite and non-negative.")
  if (output == "matrix") return(matrix_data)
  long <- as.data.frame(as.table(matrix_data), stringsAsFactors = FALSE)
  names(long) <- c("source", "target", "weight")
  if (isTRUE(drop_zero)) long <- long[long$weight != 0, , drop = FALSE]
  rownames(long) <- NULL
  long
}
