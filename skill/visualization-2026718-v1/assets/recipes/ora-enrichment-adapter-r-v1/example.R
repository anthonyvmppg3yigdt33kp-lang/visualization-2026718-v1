source("recipe.R")
dat <- utils::read.csv("../../fixtures/ora_enrichment_results.csv", check.names = FALSE)
adapted <- adapt_ora_enrichment_table(dat)
stopifnot(
  identical(names(adapted), c(".pathway", ".magnitude", ".count", ".padj", ".direction", ".source_row")),
  all(is.finite(adapted$.magnitude)),
  all(adapted$.padj > 0 & adapted$.padj <= 1)
)
