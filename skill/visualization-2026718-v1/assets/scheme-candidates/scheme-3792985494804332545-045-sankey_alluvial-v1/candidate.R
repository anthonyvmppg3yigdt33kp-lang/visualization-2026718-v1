# Reference-only, source-safe candidate source fragment.
candidate_source <- function() {
  return("# source block: article-3792985494804332545-045-b010\n# Use viridis scales.\nsample\nhead(sample)\n# Generate a more fine-grained clustering.\nsample$annotation <- ifelse(sample$seurat_clusters %in% c(\"0\", \"3\"), \"A\", \"B\")\ntable(sample$annotation, sample$seurat_clusters)\np <- do_AlluvialPlot(sample = sample, first_group = \"annotation\",last_group = \"seurat_clusters\",\n                     fill.by = \"annotation\",stratum.fill = \"grey80\")\np\n")
}
