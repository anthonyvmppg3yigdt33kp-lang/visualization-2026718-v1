source("R/helpers.R")
suppressPackageStartupMessages({
  library(Seurat)
  library(CellChat)
  library(future)
})

set.seed(20260718)
future::plan(future::sequential)
options(future.globals.maxSize = 4 * 1024^3)
pbmc <- readRDS(project_path("data", "processed", "pbmc3k_seurat.rds"))
Idents(pbmc) <- "cell_type"

cellchat <- CellChat::createCellChat(object = pbmc, group.by = "cell_type", assay = "RNA")
utils::data("CellChatDB.human", package = "CellChat", envir = environment())
cellchat@DB <- CellChatDB.human
cellchat <- CellChat::subsetData(cellchat)
cellchat <- CellChat::identifyOverExpressedGenes(cellchat, do.fast = FALSE)
cellchat <- CellChat::identifyOverExpressedInteractions(cellchat)
cellchat <- CellChat::computeCommunProb(
  cellchat, type = "triMean", raw.use = TRUE,
  population.size = FALSE, distance.use = FALSE
)
cellchat <- CellChat::filterCommunication(cellchat, min.cells = 10)
cellchat <- CellChat::computeCommunProbPathway(cellchat)
cellchat <- CellChat::aggregateNet(cellchat)
cellchat <- CellChat::netAnalysis_computeCentrality(cellchat, slot.name = "netP")

communications <- CellChat::subsetCommunication(cellchat, slot.name = "net", thresh = 0.05)
if (!is.data.frame(communications) || !nrow(communications)) stop("CellChat produced no ligand-receptor rows at p <= 0.05.")
utils::write.csv(communications, project_path("results", "tables", "cellchat_ligand_receptor_all.csv"), row.names = FALSE)
utils::write.csv(cellchat@net$count, project_path("results", "tables", "cellchat_count_matrix.csv"), row.names = TRUE)
utils::write.csv(cellchat@net$weight, project_path("results", "tables", "cellchat_weight_matrix.csv"), row.names = TRUE)

probability_column <- intersect(c("prob", "probability", "weight"), names(communications))[1]
if (is.na(probability_column)) stop("CellChat communication table lacks a probability/weight column.")
top_communications <- communications[order(communications[[probability_column]], decreasing = TRUE), , drop = FALSE]
top_communications <- utils::head(top_communications, 30)
utils::write.csv(top_communications, project_path("results", "tables", "cellchat_top30_ligand_receptor.csv"), row.names = FALSE)

pathways <- sort(unique(as.character(communications$pathway_name)))
pathways <- pathways[!is.na(pathways) & nzchar(pathways)]
nonzero_edges <- sum(cellchat@net$weight > 0)
summary_table <- data.frame(
  metric = c("cell_groups", "cells", "ligand_receptor_rows_p_le_0.05", "signaling_pathways", "nonzero_aggregate_edges"),
  value = c(length(levels(pbmc$cell_type)), ncol(pbmc), nrow(communications), length(pathways), nonzero_edges),
  stringsAsFactors = FALSE
)
utils::write.csv(summary_table, project_path("results", "tables", "cellchat_summary.csv"), row.names = FALSE)
saveRDS(cellchat, project_path("data", "processed", "pbmc3k_cellchat.rds"), compress = "xz")

write_json(
  list(
    input = list(seurat_object = "data/processed/pbmc3k_seurat.rds", cells = ncol(pbmc), grouping = "cell_type", groups = as.list(levels(pbmc$cell_type))),
    software = list(R = as.character(getRversion()), CellChat = as.character(packageVersion("CellChat")), CellChat_remote_sha = "75253cd0c9e68410e6e721a6d3a0419a1d7e358f"),
    database = "CellChatDB.human bundled with installed CellChat",
    inference = list(overexpressed_genes = TRUE, overexpressed_gene_test = "standard Wilcoxon (do.fast = FALSE; presto is optional)", overexpressed_interactions = TRUE, probability_type = "triMean", raw_use = TRUE, population_size = FALSE, distance_use = FALSE, minimum_cells = 10, communication_threshold = 0.05, future_plan = "sequential", seed = 20260718),
    outputs = list(ligand_receptor_rows = nrow(communications), pathways = length(pathways), nonzero_aggregate_edges = nonzero_edges),
    claim_limits = c("This is model-inferred communication from one public demonstration dataset.", "It does not prove physical ligand-receptor binding, molecular flux, spatial contact, causal signaling or reproducibility across donors.", "CellChat p-values are model-derived and are not a substitute for biological replication.")
  ),
  project_path("results", "run_manifest_cellchat.json")
)
capture_session_info(project_path("results", "logs", "session_info_cellchat.txt"))
message("CellChat complete: ", nrow(communications), " ligand-receptor rows, ", length(pathways), " pathways, ", nonzero_edges, " nonzero aggregate edges.")
complete_stage("03_cellchat_pbmc3k")
