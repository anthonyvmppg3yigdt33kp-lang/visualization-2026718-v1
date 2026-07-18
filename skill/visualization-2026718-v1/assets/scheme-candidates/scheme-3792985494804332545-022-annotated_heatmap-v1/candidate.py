"""Reference-only, import-safe candidate source fragment."""

CANDIDATE_SOURCE = "# source block: article-3792985494804332545-022-b004\nlibrary(pheatmap)\npheatmap(data,scale = \"none\",treeheight_row = 0,treeheight_col = 0,show_colnames = F,\n         annotation_col = anno[,1,drop=F],annotation_names_col=F,\n         cluster_cols = F,cluster_rows = F,  annotation_colors = ann_colors,\n         col = colorRampPalette(c(\"#ceb0ff\",\"white\",\"#ff4628\"))(100),\n         fontsize_row=8\n         )\n"

def get_candidate_source() -> str:
    """Return sanitized source for explicit adaptation; never executes it."""
    return CANDIDATE_SOURCE
