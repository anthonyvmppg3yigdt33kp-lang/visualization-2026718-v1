source("../ora-enrichment-adapter-r-v1/recipe.R")
source("recipe.R")
dat <- utils::read.csv("../../fixtures/ora_enrichment_results.csv", check.names = FALSE)
adapted <- adapt_ora_enrichment_table(
  dat,
  pathway = "pathway",
  magnitude = "GeneRatio",
  count = "Count",
  padj = "p.adjust",
  direction = "direction"
)
p <- plot_enrichment_rose(adapted, top_n = 8L)
stopifnot(inherits(p, "ggplot"))
