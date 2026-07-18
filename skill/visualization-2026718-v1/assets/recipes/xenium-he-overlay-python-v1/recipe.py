"""Minimal Xenium/H&E image overlay that never reads or writes files implicitly."""
from __future__ import annotations

from typing import Mapping, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_xenium_he_overlay(
    image: np.ndarray,
    cells: Optional[pd.DataFrame] = None,
    x: str = "x",
    y: str = "y",
    group: str = "cell_type",
    palette: Optional[Mapping[str, str]] = None,
    point_size: float = 10.0,
    alpha: float = 0.65,
    origin: str = "upper",
    ax=None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Display an RGB/grayscale tissue image with optional registered cell coordinates."""
    image = np.asarray(image)
    if image.ndim not in (2, 3):
        raise ValueError("image must be a 2D grayscale or 3D RGB/RGBA array")
    if ax is None:
        figure, ax = plt.subplots(figsize=(7.0, 7.0), constrained_layout=True)
    else:
        figure = ax.figure
    ax.imshow(image, origin=origin)
    if cells is not None:
        missing = [column for column in (x, y, group) if column not in cells.columns]
        if missing:
            raise ValueError(f"Missing cell columns: {', '.join(missing)}")
        categories = list(pd.unique(cells[group]))
        defaults = plt.get_cmap("tab20").colors
        colors = {category: (palette or {}).get(category, defaults[i % len(defaults)]) for i, category in enumerate(categories)}
        for category in categories:
            subset = cells.loc[cells[group] == category]
            ax.scatter(subset[x], subset[y], s=point_size, color=colors[category], alpha=alpha, linewidths=0, label=str(category))
        ax.legend(title=group, frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.set_axis_off()
    return figure, ax
