# Reference-only, source-safe candidate source fragment.
candidate_source <- function() {
  return("# source block: article-3792985494804332545-065-b005\n# Retrieve mutation data of \"msk_impact_2017\" from cBioPortal\nmutation.dat <- getMutationsFromCbioportal(\"msk_impact_2017\", \"TP53\")\nmutation.dat\n\n# \"cbioportal\" chart theme\nplot.options <- g3Lollipop.theme(theme.name = \"cbioportal\",\n                                 title.text = \"TP53 gene (cbioportal theme)\",\n                                 y.axis.label = \"# of TP53 Mutations\")\n\ng3Lollipop(mutation.dat,\n           gene.symbol = \"TP53\",\n           btn.style = \"gray\", # gray-style chart download buttons\n           plot.options = plot.options,\n")
}
