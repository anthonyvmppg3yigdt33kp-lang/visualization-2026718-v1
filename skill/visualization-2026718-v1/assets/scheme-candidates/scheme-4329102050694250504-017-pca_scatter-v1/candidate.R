# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-017-b003\n# 绘图\np <- ggplot(pca_df, aes(x = PC1, y = PC2, color = group)) +\n  geom_point(size = 3, alpha = 0.8) +\n  geom_text_repel(aes(label = sample), size = 3) +  # 使用 ggrepel 避免重叠\n  stat_ellipse(aes(fill = group), alpha = 0.2, geom = \"polygon\") +\n  labs(x = paste0(\"PC1 (\", round(var_explained[1]*100, 2), \"%)\"),\n       y = paste0(\"PC2 (\", round(var_explained[2]*100, 2), \"%)\")) +\n  theme_bw() +\n  theme()\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("y", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
