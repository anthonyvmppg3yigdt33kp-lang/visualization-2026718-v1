project_path <- function(...) {
  root <- Sys.getenv("PBMC3K_PROJECT", unset = getwd())
  file.path(normalizePath(root, winslash = "/", mustWork = TRUE), ...)
}

ensure_parent <- function(path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  invisible(path)
}

write_json <- function(value, path) {
  ensure_parent(path)
  jsonlite::write_json(value, path, auto_unbox = TRUE, pretty = TRUE, null = "null", digits = NA)
}

sha256_file <- function(path) {
  unname(digest::digest(file = path, algo = "sha256", serialize = FALSE))
}

save_ggplot_pair <- function(plot, stem, original_mm = c(180, 140),
                             final_mm = c(180, 140), original_dpi = 150,
                             final_dpi = 300, background = "white") {
  original <- project_path("results", "figures", "original", paste0(stem, ".png"))
  final <- project_path("results", "figures", "final", paste0(stem, ".png"))
  ensure_parent(original)
  ensure_parent(final)
  ggplot2::ggsave(original, plot = plot, width = original_mm[1], height = original_mm[2],
                  units = "mm", dpi = original_dpi, bg = background, device = ragg::agg_png)
  ggplot2::ggsave(final, plot = plot, width = final_mm[1], height = final_mm[2],
                  units = "mm", dpi = final_dpi, bg = background, device = ragg::agg_png)
  list(original = original, final = final, original_mm = original_mm,
       final_mm = final_mm, original_dpi = original_dpi, final_dpi = final_dpi)
}

save_base_pair <- function(draw, stem, original_mm = c(170, 170),
                           final_mm = c(170, 170), original_dpi = 150,
                           final_dpi = 300, background = "white") {
  original <- project_path("results", "figures", "original", paste0(stem, ".png"))
  final <- project_path("results", "figures", "final", paste0(stem, ".png"))
  ensure_parent(original)
  ensure_parent(final)
  render <- function(path, size, dpi) {
    ragg::agg_png(path, width = size[1], height = size[2], units = "mm", res = dpi, background = background)
    device <- grDevices::dev.cur()
    on.exit(if (device %in% grDevices::dev.list()) grDevices::dev.off(device), add = TRUE)
    draw()
    grDevices::dev.off()
  }
  render(original, original_mm, original_dpi)
  render(final, final_mm, final_dpi)
  list(original = original, final = final, original_mm = original_mm,
       final_mm = final_mm, original_dpi = original_dpi, final_dpi = final_dpi)
}

save_heatmap_pair <- function(heatmap, stem, original_mm = c(150, 130),
                              final_mm = c(150, 130), original_dpi = 150,
                              final_dpi = 300, background = "white") {
  save_base_pair(
    function() {
      grid::grid.newpage()
      ComplexHeatmap::draw(heatmap, heatmap_legend_side = "right")
    },
    stem = stem, original_mm = original_mm, final_mm = final_mm,
    original_dpi = original_dpi, final_dpi = final_dpi,
    background = background
  )
}

source_recipe <- function(skill_root, recipe_id) {
  path <- file.path(skill_root, "assets", "recipes", recipe_id, "recipe.R")
  if (!file.exists(path)) stop("Skill Recipe is missing: ", path)
  sys.source(path, envir = .GlobalEnv, keep.source = TRUE)
  invisible(path)
}

capture_session_info <- function(path) {
  ensure_parent(path)
  writeLines(capture.output(sessionInfo()), path, useBytes = TRUE)
  invisible(path)
}

complete_stage <- function(stage) {
  marker <- project_path("results", "logs", paste0(stage, ".complete.json"))
  write_json(
    list(stage = stage, completed_at = format(Sys.time(), tz = "UTC", usetz = TRUE), pid = Sys.getpid()),
    marker
  )
  flush.console()
  if (identical(Sys.getenv("PBMC3K_WINDOWS_EXIT_WORKAROUND"), "1")) {
    helper <- project_path("runtime", "hard_exit.dll")
    if (!file.exists(helper)) stop("Windows exit workaround requested but helper DLL is missing: ", helper)
    dyn.load(helper)
    .Call("pbmc3k_terminate_process", 0L)
  }
  invisible(marker)
}
