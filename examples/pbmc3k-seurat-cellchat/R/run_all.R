scripts <- c(
  "R/01_seurat_pbmc3k.R",
  "R/02_skill_visualizations.R",
  "R/03_cellchat_pbmc3k.R",
  "R/04_cellchat_visualizations.R"
)
for (script in scripts) {
  message("\n=== Running ", script, " ===")
  status <- system2(file.path(R.home("bin"), "Rscript"), shQuote(script))
  if (!identical(status, 0L)) stop("Stage failed: ", script, " (exit ", status, ")")
}
message("All PBMC3K stages completed.")
