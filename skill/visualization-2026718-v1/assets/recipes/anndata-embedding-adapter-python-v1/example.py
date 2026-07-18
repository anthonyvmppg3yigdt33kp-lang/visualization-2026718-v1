from types import SimpleNamespace
import numpy as np
import pandas as pd
from recipe import anndata_embedding_frame

mock = SimpleNamespace(
    obsm={"X_umap": np.array([[-1.0, 0.2], [-0.8, 0.4], [1.1, -0.3]])},
    obs=pd.DataFrame({"leiden": ["0", "0", "1"]}, index=["cell_a", "cell_b", "cell_c"]),
)
frame = anndata_embedding_frame(mock)
assert list(frame.columns) == ["observation_id", "umap_1", "umap_2", "cluster"]
