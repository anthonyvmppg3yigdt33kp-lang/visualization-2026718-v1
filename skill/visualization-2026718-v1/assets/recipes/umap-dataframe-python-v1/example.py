from pathlib import Path
import pandas as pd
from recipe import plot_umap_groups

fixture = Path(__file__).parents[2] / "fixtures" / "umap_points.csv"
data = pd.read_csv(fixture)
figure, axes = plot_umap_groups(data, label_groups=True)
