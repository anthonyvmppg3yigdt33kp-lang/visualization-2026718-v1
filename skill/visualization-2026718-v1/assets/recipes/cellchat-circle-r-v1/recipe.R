plot_cellchat_circle <- function(adjacency, group_colours = NULL,
                                 vertex_weight = NULL, edge_width_max = 8,
                                 edge_alpha = 0.45, label_size = 0.9,
                                 title = "Inferred communication weight") {
  if (!requireNamespace("igraph", quietly = TRUE)) stop("Package 'igraph' is required.")
  x <- as.matrix(adjacency)
  storage.mode(x) <- "double"
  if (nrow(x) != ncol(x)) stop("adjacency must be square.")
  if (is.null(rownames(x)) || is.null(colnames(x))) stop("adjacency needs row and column names.")
  if (!setequal(rownames(x), colnames(x))) stop("row and column node sets must match.")
  x <- x[rownames(x), rownames(x), drop = FALSE]
  if (any(!is.finite(x)) || any(x < 0)) stop("adjacency must contain finite non-negative weights.")
  nodes <- rownames(x)
  if (is.null(group_colours)) {
    hues <- seq(15, 375, length.out = length(nodes) + 1L)[seq_along(nodes)]
    group_colours <- stats::setNames(grDevices::hcl(h = hues, c = 75, l = 60), nodes)
  }
  if (is.null(names(group_colours)) || !all(nodes %in% names(group_colours))) stop("group_colours must be named for every node.")
  if (is.null(vertex_weight)) vertex_weight <- rowSums(x) + colSums(x)
  if (length(vertex_weight) != length(nodes)) stop("vertex_weight must have one value per node.")
  vertex_weight <- as.numeric(vertex_weight)
  vertex_size <- if (diff(range(vertex_weight)) == 0) rep(24, length(nodes)) else 18 + 18 * (vertex_weight - min(vertex_weight)) / diff(range(vertex_weight))
  graph <- igraph::graph_from_adjacency_matrix(x, mode = "directed", weighted = TRUE, diag = TRUE)
  weights <- igraph::E(graph)$weight
  widths <- if (!length(weights)) numeric() else if (max(weights) == 0) rep(0.5, length(weights)) else pmax(0.35, weights / max(weights) * edge_width_max)
  igraph::plot.igraph(
    graph, layout = igraph::layout_in_circle(graph), rescale = TRUE,
    vertex.color = unname(group_colours[igraph::V(graph)$name]),
    vertex.frame.color = "white", vertex.size = vertex_size,
    vertex.label.color = "#17202A", vertex.label.cex = label_size,
    vertex.label.family = "sans", edge.width = widths,
    edge.color = grDevices::adjustcolor("#34495E", alpha.f = edge_alpha),
    edge.arrow.size = 0.38, edge.curved = 0.16, margin = 0.16,
    main = title
  )
  invisible(list(adjacency = x, vertex_weight = vertex_weight, edge_width_max = edge_width_max))
}
