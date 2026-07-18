"""Backend-pure Matplotlib recipe for precomputed UMAP-like coordinates."""
from __future__ import annotations

from typing import Mapping, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd


def plot_umap_groups(
    data: pd.DataFrame,
    x: str = "umap_1",
    y: str = "umap_2",
    group: str = "cluster",
    palette: Optional[Mapping[str, str]] = None,
    point_size: float = 12.0,
    alpha: float = 0.75,
    legend_fontsize: float = 7.0,
    legend_title_fontsize: float = 7.0,
    ax=None,
    label_groups: bool = False,
) -> Tuple[plt.Figure, plt.Axes]:
    """Return ``(figure, axes)`` without saving or changing input data."""
    missing = [column for column in (x, y, group) if column not in data.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    if ax is None:
        figure, ax = plt.subplots(figsize=(6.0, 5.0), constrained_layout=True)
    else:
        figure = ax.figure
    categories = list(pd.unique(data[group]))
    default_colors = plt.get_cmap("tab20").colors
    colors = {category: (palette or {}).get(category, default_colors[i % len(default_colors)]) for i, category in enumerate(categories)}
    for category in categories:
        subset = data.loc[data[group] == category]
        ax.scatter(subset[x], subset[y], s=point_size, alpha=alpha, linewidths=0, color=colors[category], label=str(category), rasterized=True)
        if label_groups and len(subset):
            ax.text(subset[x].median(), subset[y].median(), str(category), ha="center", va="center", weight="bold")
    ax.set(xlabel=x, ylabel=y)
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(
        title=group,
        frameon=False,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=legend_fontsize,
        title_fontsize=legend_title_fontsize,
    )
    # Expose an explicit, copied label-anchor contract for compatible
    # modifiers.  This keeps composition callable without asking a JSON
    # runtime request to serialize a DataFrame, and never mutates caller data.
    label_data = (
        data.loc[:, [x, y, group]]
        .groupby(group, sort=False, observed=True)[[x, y]]
        .median()
        .reset_index()
    )
    ax._plot_code_retriever_label_contract = {
        "data": label_data,
        "x": x,
        "y": y,
        "label": group,
    }
    return figure, ax
