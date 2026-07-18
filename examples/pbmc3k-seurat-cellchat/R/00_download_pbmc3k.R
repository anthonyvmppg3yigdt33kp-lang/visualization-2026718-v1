source("R/helpers.R")

url <- "https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz"
expected_sha256 <- "847d6ebd9a1ec9a768f2be7e40ca42cbfe75ebeb6d76a4c24167041699dc28b5"
archive <- project_path("data", "raw", "pbmc3k_filtered_gene_bc_matrices.tar.gz")
extract_root <- project_path("data", "raw", "extracted")
matrix_dir <- file.path(extract_root, "filtered_gene_bc_matrices", "hg19")

ensure_parent(archive)
dir.create(extract_root, recursive = TRUE, showWarnings = FALSE)
if (!file.exists(archive)) {
  message("Downloading official 10x Genomics PBMC3K archive ...")
  utils::download.file(url, archive, mode = "wb", quiet = FALSE)
}

actual_sha256 <- sha256_file(archive)
if (!identical(tolower(actual_sha256), expected_sha256)) {
  stop("PBMC3K archive SHA256 mismatch. Expected ", expected_sha256, "; observed ", actual_sha256)
}

required <- c("barcodes.tsv", "genes.tsv", "matrix.mtx")
if (!all(file.exists(file.path(matrix_dir, required)))) {
  utils::untar(archive, exdir = extract_root)
}
if (!all(file.exists(file.path(matrix_dir, required)))) {
  stop("Archive extracted but the expected hg19 matrix files are missing: ", matrix_dir)
}

message("PBMC3K input ready: ", matrix_dir)
message("SHA256: ", actual_sha256)
complete_stage("00_download_pbmc3k")
