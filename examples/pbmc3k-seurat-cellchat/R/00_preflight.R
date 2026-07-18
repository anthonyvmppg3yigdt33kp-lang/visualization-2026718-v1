source("R/helpers.R")
skill_root <- Sys.getenv("VIS_SKILL_ROOT")
if (!nzchar(skill_root) || !file.exists(file.path(skill_root, "SKILL.md"))) stop("Set VIS_SKILL_ROOT.")
project_scripts <- list.files(project_path("R"), pattern = "\\.R$", full.names = TRUE)
skill_scripts <- list.files(file.path(skill_root, "assets", "recipes"), pattern = "recipe\\.R$", recursive = TRUE, full.names = TRUE)
parse_failures <- character()
for (path in c(project_scripts, skill_scripts)) {
  tryCatch(parse(path, keep.source = TRUE), error = function(error) {
    parse_failures <<- c(parse_failures, paste(path, conditionMessage(error), sep = ": "))
  })
}
if (length(parse_failures)) stop(paste(parse_failures, collapse = "\n"))

packages <- c("Seurat", "SeuratObject", "CellChat", "ggplot2", "patchwork", "ggrepel", "future", "ComplexHeatmap", "circlize", "igraph", "ragg", "jsonlite", "digest")
available <- vapply(packages, requireNamespace, logical(1), quietly = TRUE)
if (!all(available)) stop("Missing packages: ", paste(names(available)[!available], collapse = ", "))
versions <- vapply(packages, function(package) as.character(packageVersion(package)), character(1))
utils::data("CellChatDB.human", package = "CellChat", envir = environment())
cellchat_db <- get("CellChatDB.human", envir = environment(), inherits = FALSE)
if (!is.list(cellchat_db) || !length(cellchat_db)) stop("CellChatDB.human is unavailable.")
write_json(
  list(
    R = as.character(getRversion()),
    library_paths = as.list(.libPaths()),
    packages = as.list(versions),
    parsed_project_scripts = length(project_scripts),
    parsed_skill_recipe_scripts = length(skill_scripts),
    cellchat_database = "CellChatDB.human available",
    trusted_rds_only = TRUE
  ),
  project_path("results", "preflight.json")
)
message("Preflight passed: ", length(project_scripts), " project scripts, ", length(skill_scripts), " Skill Recipe scripts.")
complete_stage("00_preflight")
