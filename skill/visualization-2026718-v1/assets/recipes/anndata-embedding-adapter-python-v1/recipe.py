"""Adapt an AnnData-like object to the pandas embedding recipe contract."""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def anndata_embedding_frame(
    adata,
    basis: str = "X_umap",
    group: str = "leiden",
    dimensions: Sequence[int] = (0, 1),
    x_name: str = "umap_1",
    y_name: str = "umap_2",
    group_name: str = "cluster",
) -> pd.DataFrame:
    """Return an aligned copy; never compute an embedding or modify ``adata``."""
    if not hasattr(adata, "obsm") or not hasattr(adata, "obs"):
        raise TypeError("adata must expose AnnData-compatible 'obsm' and 'obs' attributes")
    if basis not in adata.obsm:
        raise KeyError(f"Embedding not found in adata.obsm: {basis}")
    if group not in adata.obs.columns:
        raise KeyError(f"Metadata column not found in adata.obs: {group}")
    if len(dimensions) != 2 or any(not isinstance(index, (int, np.integer)) or index < 0 for index in dimensions):
        raise ValueError("dimensions must contain two non-negative integer indices")
    coordinates = np.asarray(adata.obsm[basis])
    if coordinates.ndim != 2 or max(dimensions) >= coordinates.shape[1]:
        raise ValueError("Requested dimensions exceed the embedding shape")
    if coordinates.shape[0] != adata.obs.shape[0]:
        raise ValueError("Embedding rows and adata.obs rows are not aligned")
    if not np.isfinite(coordinates[:, list(dimensions)]).all():
        raise ValueError("Selected embedding coordinates must all be finite")
    return pd.DataFrame(
        {
            "observation_id": adata.obs.index.astype(str),
            x_name: coordinates[:, dimensions[0]],
            y_name: coordinates[:, dimensions[1]],
            group_name: adata.obs[group].to_numpy(copy=True),
        },
        index=adata.obs.index.copy(),
    )
