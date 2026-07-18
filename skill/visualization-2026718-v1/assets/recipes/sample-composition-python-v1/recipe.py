"""Sample/donor-level composition summary and Matplotlib recipe.

The functions never treat cells as independent biological replicates: rows are
first aggregated within each sample, and every plotted bar remains one sample.
"""
from __future__ import annotations

import math
from typing import Mapping, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import pandas as pd


def _observation_frame(data) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy(deep=True)
    if hasattr(data, "obs") and isinstance(data.obs, pd.DataFrame):
        return data.obs.copy(deep=True)
    raise TypeError("data must be a pandas DataFrame or expose an AnnData-compatible .obs DataFrame")


def _checked_order(values: Sequence[str], observed: list[str], name: str) -> list[str]:
    order = [str(value) for value in values]
    if len(order) != len(set(order)):
        raise ValueError(f"{name} must not contain duplicates")
    missing = [value for value in observed if value not in order]
    if missing:
        raise ValueError(f"{name} omits observed values: {', '.join(missing)}")
    return order


def summarize_sample_composition(
    data,
    sample: str = "sample_id",
    group: str = "condition",
    cell_type: str = "cell_type",
    count: Optional[str] = None,
    group_order: Optional[Sequence[str]] = None,
    cell_type_order: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Return a complete sample-by-cell-type composition table.

    ``data`` may be a cell-level long DataFrame, an AnnData-like object (its
    ``.obs`` is copied), or an already aggregated long table when ``count`` is
    supplied.  A sample must belong to exactly one biological group.  Missing
    sample/cell-type combinations are completed with zero counts; no group mean
    replaces the individual sample values.
    """
    semantic_columns = [sample, group, cell_type]
    if len(set(semantic_columns)) != len(semantic_columns):
        raise ValueError("sample, group and cell_type must name distinct columns")
    if count is not None and count in semantic_columns:
        raise ValueError("count must be distinct from sample, group and cell_type")
    frame = _observation_frame(data)
    required = [sample, group, cell_type, *( [count] if count is not None else [] )]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("data must contain at least one observation")
    if frame[required].isna().any().any():
        raise ValueError("Sample, group, cell-type and count fields must not contain missing values")

    tidy = frame.loc[:, required].copy()
    tidy[sample] = tidy[sample].astype(str)
    tidy[group] = tidy[group].astype(str)
    tidy[cell_type] = tidy[cell_type].astype(str)
    if (tidy[[sample, group, cell_type]] == "").any().any():
        raise ValueError("Sample, group and cell-type labels must be non-empty")

    sample_group_counts = tidy.groupby(sample, sort=False, observed=True)[group].nunique()
    ambiguous = sample_group_counts[sample_group_counts != 1].index.tolist()
    if ambiguous:
        raise ValueError("Each sample must map to one group; ambiguous samples: " + ", ".join(ambiguous))

    if count is None:
        tidy[".count"] = 1.0
    else:
        tidy[".count"] = pd.to_numeric(tidy[count], errors="coerce")
        if tidy[".count"].isna().any() or not tidy[".count"].map(math.isfinite).all() or (tidy[".count"] < 0).any():
            raise ValueError("count values must be finite, numeric and non-negative")

    observed_groups = list(pd.unique(tidy[group]))
    groups = _checked_order(group_order, observed_groups, "group_order") if group_order is not None else observed_groups
    observed_types = list(pd.unique(tidy[cell_type]))
    cell_types = (
        _checked_order(cell_type_order, observed_types, "cell_type_order")
        if cell_type_order is not None else observed_types
    )

    sample_meta = tidy[[sample, group]].drop_duplicates().copy()
    sample_meta[".group_order"] = sample_meta[group].map({value: index for index, value in enumerate(groups)})
    sample_meta[".input_order"] = range(len(sample_meta))
    sample_meta = sample_meta.sort_values([".group_order", ".input_order"], kind="stable")

    counts = (
        tidy.groupby([sample, group, cell_type], sort=False, observed=True)[".count"]
        .sum()
        .reset_index()
    )
    grid = sample_meta[[sample, group]].assign(_key=1).merge(
        pd.DataFrame({cell_type: cell_types, "_key": 1}), on="_key", how="inner"
    ).drop(columns="_key")
    summary = grid.merge(counts, on=[sample, group, cell_type], how="left")
    summary[".count"] = summary[".count"].fillna(0.0)
    totals = summary.groupby(sample, sort=False, observed=True)[".count"].transform("sum")
    if (totals <= 0).any():
        bad = summary.loc[totals <= 0, sample].drop_duplicates().tolist()
        raise ValueError("Every sample needs a positive denominator; empty samples: " + ", ".join(bad))
    summary["proportion"] = summary[".count"] / totals
    summary = summary.rename(columns={sample: "sample_id", group: "group", cell_type: "cell_type", ".count": "count"})
    return summary[["sample_id", "group", "cell_type", "count", "proportion"]].reset_index(drop=True)


def plot_sample_composition(
    data,
    sample: str = "sample_id",
    group: str = "condition",
    cell_type: str = "cell_type",
    count: Optional[str] = None,
    group_order: Optional[Sequence[str]] = None,
    cell_type_order: Optional[Sequence[str]] = None,
    palette: Optional[Mapping[str, str]] = None,
    ax=None,
    legend_ncol: int = 1,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot one stacked proportion bar per biological sample and return Figure/Axes."""
    summary = summarize_sample_composition(
        data, sample=sample, group=group, cell_type=cell_type, count=count,
        group_order=group_order, cell_type_order=cell_type_order,
    )
    samples = list(pd.unique(summary["sample_id"]))
    cell_types = list(pd.unique(summary["cell_type"]))
    if ax is None:
        width = max(6.0, 0.58 * len(samples) + 2.5)
        figure, ax = plt.subplots(figsize=(width, 4.6), constrained_layout=True)
    else:
        figure = ax.figure

    pivot = summary.pivot(index="sample_id", columns="cell_type", values="proportion").reindex(samples)
    default_colors = plt.get_cmap("tab20").colors
    bottom = pd.Series(0.0, index=samples)
    x_positions = list(range(len(samples)))
    for index, category in enumerate(cell_types):
        values = pivot[category].fillna(0.0)
        color = (palette or {}).get(category, default_colors[index % len(default_colors)])
        ax.bar(x_positions, values.to_numpy(), bottom=bottom.to_numpy(), width=0.78,
               color=color, edgecolor="white", linewidth=0.35, label=str(category))
        bottom = bottom + values

    sample_groups = summary[["sample_id", "group"]].drop_duplicates().set_index("sample_id").loc[samples, "group"]
    labels = [f"{sample_id}\n{sample_groups.loc[sample_id]}" for sample_id in samples]
    ax.set_xticks(x_positions, labels, rotation=45, ha="right")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Within-sample proportion")
    ax.set_xlabel("Biological sample")
    ax.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
    for name in ("top", "right"):
        ax.spines[name].set_visible(False)
    ax.grid(axis="y", color="0.9", linewidth=0.6)
    ax.set_axisbelow(True)

    previous = sample_groups.iloc[0]
    for index, current in enumerate(sample_groups.iloc[1:], start=1):
        if current != previous:
            ax.axvline(index - 0.5, color="0.55", linewidth=0.7, linestyle=":")
        previous = current
    ax.legend(title=cell_type, frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left", ncol=legend_ncol)
    return figure, ax
