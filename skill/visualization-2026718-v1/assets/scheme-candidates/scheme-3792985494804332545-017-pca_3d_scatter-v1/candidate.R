# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-017-b003\n#  Step 3: Plot\nplot.data <- plot.data %>%\n  mutate(ID=rownames(plot.data),\n         Type=meta$Type,\n         TypeColor=color.bin[as.numeric(as.factor(Type))])\nhead(plot.data)\n\nscatterplot3d(x = plot.data$PC2,\n              y = plot.data$PC1,\n              z = plot.data$PC3,\n              color = plot.data$TypeColor,\n              pch = 16, cex.symbols = 1,\n              scale.y = 0.7, angle = 45,\n              xlab = paste0(\"PC2(\",round(var_explained[2,2], digits = 2),\"%)\"),\n              ylab = paste0(\"PC1(\", round(var_explained[1,2], digits = 2),\"%)\"),\n              zlab = paste0(\"PC3(\",round(var_explained[3,2], digits = 2),\"%)\"),\n              main=\"Protein\",\n              col.axis = \"#444444\", col.grid = \"#CCCCCC\")\nlegend(\"bottom\", legend = levels(as.factor(meta$Type)),\n       col =  color.bin,  pch = 16,title = \"Tissue\",\n       inset = -0.15, xpd = TRUE, horiz = TRUE)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("inset", "col", "col.axis", "main", "zlab", "ylab", "xlab", "scale.y", "pch", "color", "z", "y", "TypeColor", "Type", "plot.data")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
