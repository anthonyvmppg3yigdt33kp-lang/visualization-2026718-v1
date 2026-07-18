"""Import-safe candidate distilled from a traceable plotting chain."""

CANDIDATE_SOURCE = "# source block: article-4329102050694250504-001-b011\nplt.figure(figsize=(10, 4), dpi=300)\nax1 = plt.gca()\n\n# Color cells by leiden\nsegmentation_face_color = \"leiden\"\ninside_alpha = 0.34\noutside_alpha = 0.34\n\n# Add the key of facecolor of the cells to each transcript row\ncelltypes = []\nids = np.array([i.split(\"_\")[-1] for i in finalized_adata.obs.index.values]).astype(int)\nid_df = pd.DataFrame(\n    zip(ids, finalized_adata.obs[segmentation_face_color].values),\n    columns=[\"id\", segmentation_face_color],\n)\ntranscripts_with_obs = transcripts_df.merge(\n    id_df, left_on=\"split_cell\", right_on=\"id\", how=\"left\"\n)\ntranscripts_with_obs = transcripts_with_obs.dropna(axis=0)\n\n# Group transcripts by their Baysor assignment\nprint(\"Making Shapes\")\ngby = transcripts_with_obs[\n    (transcripts_with_obs.split_cell != 0) & (transcripts_with_obs.split_cell != -1)\n].groupby(\"split_cell\")\n\n# Create a cell segmentation boundary for each set of transcripts, and get the color of the mask\nshapes = []\nfor group in tqdm(gby):\n    shapes.append(make_alphashape(group[1][[\"x\", \"y\"]].values, alpha=0.05))\n    ctype = group[1][segmentation_face_color].values[0]\n    cell_location = np.where(\n        finalized_adata.obs[segmentation_face_color].cat.categories == ctype\n    )[0]\n    try:\n        celltypes.append(\n            finalized_adata.uns[f\"{segmentation_face_color}_colors\"][cell_location][0]\n        )\n    except:\n        celltypes.append(\n            finalized_adata.uns[f\"{segmentation_face_color}_colors\"][cell_location[0]]\n        )\nshapes = gpd.GeoSeries(shapes)\ncolors = celltypes\n\n# Display the Xenium DAPI image\nimg_cropped = xenium_dapi[\n    min_x:max_x, min_y:max_y\n]  # [second_min_x:second_max_x, second_min_y:second_max_y]\nax1.imshow(img_cropped, vmax=np.percentile(img_cropped, 99.9), cmap=\"Greys_r\")\n\n# Create an empty GeoDataFrame to store adjusted polygons\nadjusted_shapes = []\n\n# Iterate through the shapes DataFrame and adjust each polygon\nfor original_polygon in shapes:\n    scaled_polygon = sa.translate(original_polygon, -min_y, -min_x)\n    adjusted_shapes.append(scaled_polygon)\n\nadjusted_shapes = gpd.GeoSeries(adjusted_shapes)\n\nfor geometry, color in zip(adjusted_shapes, colors):\n    if geometry.geom_type == \"Polygon\":\n        patch = plt.Polygon(\n            list(zip(*geometry.exterior.xy)),\n            facecolor=color,\n            edgecolor=\"none\",\n            alpha=inside_alpha,\n            zorder=1,\n        )\n        ax1.add_patch(patch)\n    elif geometry.geom_type == \"MultiPolygon\":\n        for poly in geometry:\n            patch = plt.Polygon(\n                list(zip(*poly.exterior.xy)),\n                facecolor=color,\n                edgecolor=\"none\",\n                alpha=inside_alpha,\n                zorder=1,\n            )\n            ax1.add_patch(patch)\n\n# Plot polygon edges with edgecolor based on data values\nfor geometry, color in zip(adjusted_shapes, colors):\n    if geometry.geom_type == \"Polygon\":\n        ax1.plot(*geometry.exterior.xy, color=color, alpha=outside_alpha)\n    elif geometry.geom_type == \"MultiPolygon\":\n        for poly in geometry:\n            ax1.plot(*poly.exterior.xy, color=color, alpha=outside_alpha)\n\n\nrectangle2 = Rectangle(\n    (second_min_y, second_min_x),\n    second_max_y - second_min_y,\n    second_max_x - second_min_x,\n    linewidth=4,\n    edgecolor=\"white\",\n    facecolor=\"none\",\n    zorder=2,\n)\nax1.add_patch(rectangle2)\nax1.set_xlim(0, max_y - min_y)\nax1.set_ylim(0, max_x - min_x)\nax1.invert_yaxis()\n# ax1.axis('equal')\nax1.axis(\"off\")\nplt.show()\n"

def get_candidate_source() -> str:
    """Return the sanitized source without executing it."""
    return CANDIDATE_SOURCE

def build_candidate_plot(bindings: dict | None = None):
    """Execute explicitly with caller-supplied bindings and return Figure/Axes.

    This candidate is reference-only until its dependencies, input contract,
    statistics, and native render have been validated.
    """
    namespace = dict(bindings or {})
    exec(compile(CANDIDATE_SOURCE, '<visualization-2026718-v1-candidate>', 'exec'), namespace, namespace)
    preferred = ['linewidth', 'rectangle2', 'zorder', 'alpha', 'edgecolor', 'facecolor', 'patch', 'scaled_polygon', 'adjusted_shapes', 'img_cropped', 'colors', 'cell_location', 'ctype', 'shapes', 'gby', 'transcripts_with_obs', 'columns', 'id_df', 'ids', 'celltypes', 'outside_alpha', 'inside_alpha', 'segmentation_face_color', 'ax1']
    try:
        from matplotlib.axes import Axes
        from matplotlib.figure import Figure
        accepted = (Figure, Axes)
    except Exception:
        accepted = ()
    for name in preferred:
        value = namespace.get(name)
        if accepted and isinstance(value, accepted):
            return value
        if hasattr(value, 'get_figure') or hasattr(value, 'savefig'):
            return value
    pyplot = namespace.get('plt')
    if pyplot is not None and hasattr(pyplot, 'gcf'):
        return pyplot.gcf()
    raise RuntimeError('Candidate did not expose a Figure/Axes; supply the declared bindings and dependencies.')
