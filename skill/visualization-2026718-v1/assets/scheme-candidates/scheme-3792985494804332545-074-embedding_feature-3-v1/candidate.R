# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-074-b015\n# 提取umap坐标以及特征基因表达\ndf <- FetchData(object =sce.all.int, vars = c(\"umap_1\", \"umap_2\", \"CD3D\"), layer = \"data\")\nhead(df)\n\n# umap_1    umap_2     CD3D\n# SC67mf2_AAACCTGAGAGTAATC -3.541568  5.127461 0.000000\n# SC67mf2_AAACCTGAGCGCTTAT -6.623588 -3.025122 1.430228\n# SC67mf2_AAACCTGAGGACACCA -4.586405  1.513219 0.000000\n\np <- ggplot(df, aes(x= umap_1, y= umap_2 )) +\n  geom_point(data = df %>% filter(CD3D == 0), color = \"#440154FF\", size = 0.6) +\n  ggpointdensity::geom_pointdensity(data = df %>% filter(CD3D > 0), size = 0.6) +\n  viridis::scale_color_viridis() +\n  theme_classic(base_size = 14) +\n  labs(color= \"CD3D\")\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "df")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
