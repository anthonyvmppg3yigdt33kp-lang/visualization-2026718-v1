from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from recipe import plot_sample_composition, summarize_sample_composition


fixture = Path(__file__).parents[2] / "fixtures" / "sample_composition_cells.csv"
aggregated = pd.read_csv(fixture)

# Aggregated long-table input.
summary = summarize_sample_composition(aggregated, count="count")
assert summary.groupby("sample_id")["proportion"].sum().round(12).eq(1.0).all()
figure, axes = plot_sample_composition(aggregated, count="count")
figure.canvas.draw()

# AnnData-compatible cell-level input; .obs is read but never modified.
cell_rows = aggregated.loc[aggregated.index.repeat(aggregated["count"])].drop(columns="count").reset_index(drop=True)
mock_anndata = SimpleNamespace(obs=cell_rows)
summary_from_anndata = summarize_sample_composition(mock_anndata)
assert summary_from_anndata["count"].sum() == aggregated["count"].sum()
