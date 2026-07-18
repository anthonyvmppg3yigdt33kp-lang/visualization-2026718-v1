source("recipe.R")
# Trusted local input only; never readRDS() from an untrusted source.
cellchat <- readRDS("pbmc3k_cellchat.rds")
communication <- cellchat_lr_table(cellchat, threshold = 0.05)
