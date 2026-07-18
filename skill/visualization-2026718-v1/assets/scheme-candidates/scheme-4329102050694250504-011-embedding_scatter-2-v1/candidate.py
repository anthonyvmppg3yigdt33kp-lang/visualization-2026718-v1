"""Import-safe candidate distilled from a traceable plotting chain."""

CANDIDATE_SOURCE = "# source block: article-4329102050694250504-011-b005\nfig, ax = plt.subplots(figsize=(10, 7))\nax.scatter(\n    u_df[\"umap_1\"], u_df[\"umap_2\"],\n    c=[colorDict[cat] for cat in u_df[f\"graph_localization_annotation\"]],\n    s=120, alpha=0.6, label=\"uninfected\", marker=\".\", linewidths=0, edgecolor=None,\n)\n\n# create legend elements from colorDict\nlegend_elements = [\n    mpatches.Patch(facecolor=colorDict[cat], label=cat)\n    for cat in u_df[f\"graph_localization_annotation\"].unique()\n]\n\n# add legend to the plot\nax.legend(handles=legend_elements, title=\"Clusters\", bbox_to_anchor=(1.05, 1), loc='upper right',\n          prop={'size': 9})\n"

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
    preferred = ['prop', 'legend_elements', 's', 'c']
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
