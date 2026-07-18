from pathlib import Path
import numpy as np
import pandas as pd
from recipe import plot_xenium_he_overlay

y, x = np.mgrid[0:320, 0:360]
image = np.stack([0.96 - 0.15 * np.sin(x / 24), 0.88 - 0.25 * np.cos(y / 31), 0.93 - 0.12 * np.sin((x + y) / 29)], axis=-1)
image = np.clip(image, 0, 1)
fixture = Path(__file__).parents[2] / "fixtures" / "xenium_cells.csv"
cells = pd.read_csv(fixture)
figure, axes = plot_xenium_he_overlay(image, cells)
