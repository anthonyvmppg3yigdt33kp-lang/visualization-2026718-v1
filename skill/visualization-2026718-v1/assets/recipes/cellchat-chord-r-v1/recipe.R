plot_cellchat_chord <- function(adjacency, group_colours = NULL, transparency = 0.65,
                                link_border = NA, directional = TRUE) {
  if (!requireNamespace("circlize", quietly = TRUE)) stop("Package 'circlize' is required.")
  x <- as.matrix(adjacency)
  storage.mode(x) <- "double"
  if (nrow(x) != ncol(x)) stop("adjacency must be square.")
  if (is.null(rownames(x)) || is.null(colnames(x))) stop("adjacency needs row and column names.")
  if (!setequal(rownames(x), colnames(x))) stop("row and column node sets must match.")
  x <- x[rownames(x), rownames(x), drop = FALSE]
  if (any(x < 0, na.rm = TRUE)) stop("Interaction weights must be non-negative.")
  if (!is.null(group_colours) && !all(rownames(x) %in% names(group_colours))) stop("group_colours must be named for every node.")
  on.exit(circlize::circos.clear(), add = TRUE)
  circlize::circos.clear()
  circlize::chordDiagram(
    x, grid.col = group_colours, transparency = transparency,
    directional = if (directional) 1 else 0,
    direction.type = if (directional) c("arrows", "diffHeight") else "diffHeight",
    link.arr.type = if (directional) "big.arrow" else "triangle",
    link.border = link_border, annotationTrack = c("grid", "name")
  )
  invisible(list(adjacency = x, directional = directional))
}
