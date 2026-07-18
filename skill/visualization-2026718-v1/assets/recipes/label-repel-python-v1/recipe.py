"""Collision-aware Matplotlib labels with a dependency-free fallback."""
from __future__ import annotations

import math
from typing import Iterator, Tuple


def _offset_candidates(step_points: float, max_steps: int) -> Iterator[Tuple[float, float]]:
    yield 0.0, 0.0
    directions = ((0, 1), (1, 0), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))
    for ring in range(1, max_steps + 1):
        distance = step_points * ring
        for dx, dy in directions:
            yield dx * distance, dy * distance


def _deterministic_labels(
    ax,
    label_data,
    x: str,
    y: str,
    label: str,
    arrowprops,
    step_points: float,
    max_steps: int,
    padding_points: float,
    point_padding_factor: float,
    max_point_overlap: int,
    fontsize: float,
):
    figure = ax.figure
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    axes_box = ax.get_window_extent(renderer)
    dpi_scale = figure.dpi / 72.0
    padding_pixels = padding_points * dpi_scale
    placed = []
    plotted_points = []
    for collection in list(ax.collections):
        try:
            offsets = collection.get_offsets()
            # ``PathCollection.get_offsets()`` are the original data-space
            # scatter coordinates.  Use the axes data transform explicitly;
            # collection offset transforms can include backend-specific affine
            # state that is not the final display coordinate system.
            transformed = ax.transData.transform(offsets)
            plotted_points.extend(
                (float(px), float(py))
                for px, py in transformed
                if math.isfinite(float(px)) and math.isfinite(float(py))
            )
        except (AttributeError, TypeError, ValueError):
            # Non-scatter collections do not participate in point avoidance.
            continue
    # Respect labels already attached to the axes (for example cluster names).
    for existing in list(ax.texts):
        if existing.get_visible() and existing.get_text():
            placed.append(existing.get_window_extent(renderer).expanded(1.03, 1.08))

    for _, row in label_data.iterrows():
        accepted = None
        best_offset = None
        best_score = None
        for offset_x, offset_y in _offset_candidates(step_points, max_steps):
            annotation = ax.annotate(
                str(row[label]),
                xy=(row[x], row[y]),
                xytext=(offset_x, offset_y),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=fontsize,
                # Measure the text glyph box without the leader line.  An
                # Annotation bbox that includes its arrow necessarily contains
                # the anchor point and would make every displaced candidate
                # look like a point collision.
                arrowprops=None,
                annotation_clip=True,
            )
            figure.canvas.draw()
            renderer = figure.canvas.get_renderer()
            box = annotation.get_window_extent(renderer).expanded(1.03, 1.08)
            inside = (
                box.x0 >= axes_box.x0 + padding_pixels
                and box.x1 <= axes_box.x1 - padding_pixels
                and box.y0 >= axes_box.y0 + padding_pixels
                and box.y1 <= axes_box.y1 - padding_pixels
            )
            collision = any(box.overlaps(other) for other in placed)
            point_box = box.expanded(point_padding_factor, point_padding_factor)
            point_overlap = sum(point_box.contains(px, py) for px, py in plotted_points)
            if inside and not collision and point_overlap <= max_point_overlap:
                if arrowprops and (offset_x or offset_y):
                    annotation.remove()
                    annotation = ax.annotate(
                        str(row[label]),
                        xy=(row[x], row[y]),
                        xytext=(offset_x, offset_y),
                        textcoords="offset points",
                        ha="center",
                        va="center",
                        fontsize=fontsize,
                        arrowprops=arrowprops,
                        annotation_clip=True,
                    )
                accepted = annotation
                placed.append(box)
                break
            if inside:
                score = (
                    1 if collision else 0,
                    point_overlap,
                    abs(offset_x) + abs(offset_y),
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best_offset = (offset_x, offset_y)
            annotation.remove()
        if accepted is None:
            # Dense labels may exhaust the zero-overlap search. Retain the
            # deterministic in-bounds position with the fewest covered points.
            offset_x, offset_y = best_offset or (0.0, 0.0)
            accepted = ax.annotate(
                str(row[label]), xy=(row[x], row[y]), xytext=(offset_x, offset_y),
                textcoords="offset points", ha="center", va="center",
                fontsize=fontsize,
                arrowprops=(arrowprops if (offset_x or offset_y) else None), annotation_clip=True,
            )
            figure.canvas.draw()
            placed.append(accepted.get_window_extent(figure.canvas.get_renderer()).expanded(1.03, 1.08))
    return ax


def add_repel_labels(
    ax,
    label_data=None,
    x: str | None = None,
    y: str | None = None,
    label: str | None = None,
    arrowprops=None,
    method: str = "auto",
    fallback_step_points: float = 8.0,
    fallback_max_steps: int = 12,
    fallback_padding_points: float = 1.5,
    fallback_point_padding_factor: float = 1.5,
    fallback_max_point_overlap: int = 0,
    fontsize: float = 7.0,
):
    """Add labels and return ``ax`` without requiring ``adjustText``.

    ``method='auto'`` uses adjustText when installed and otherwise uses a
    deterministic display-coordinate search.  ``method='deterministic'`` forces
    the dependency-free path, while ``method='adjusttext'`` requires the optional
    package explicitly.
    """
    if label_data is None:
        contract = getattr(ax, "_plot_code_retriever_label_contract", None)
        if not isinstance(contract, dict) or contract.get("data") is None:
            raise ValueError(
                "label_data is required unless the base Recipe exposes a label-anchor contract"
            )
        label_data = contract["data"].copy(deep=True)
        x = x or contract.get("x")
        y = y or contract.get("y")
        label = label or contract.get("label")
    if not x or not y or not label:
        raise ValueError("x, y and label are required for label placement")
    missing = [column for column in (x, y, label) if column not in label_data.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    if method not in {"auto", "adjusttext", "deterministic"}:
        raise ValueError("method must be 'auto', 'adjusttext', or 'deterministic'")
    if (
        fallback_step_points <= 0
        or fallback_max_steps < 1
        or fallback_padding_points < 0
        or fallback_point_padding_factor < 1
        or fallback_max_point_overlap < 0
        or fontsize <= 0
    ):
        raise ValueError(
            "Fallback step/max_steps/padding/point padding/max overlap values are invalid"
        )
    arrows = arrowprops or {"arrowstyle": "-", "color": "0.4", "lw": 0.5}

    adjust_text = None
    if method in {"auto", "adjusttext"}:
        try:
            from adjustText import adjust_text as imported_adjust_text
            adjust_text = imported_adjust_text
        except ImportError:
            if method == "adjusttext":
                raise ImportError("method='adjusttext' requires the optional package 'adjustText'")

    if adjust_text is not None:
        texts = [ax.text(row[x], row[y], str(row[label])) for _, row in label_data.iterrows()]
        adjust_text(texts, ax=ax, arrowprops=arrows)
        ax._plot_code_retriever_label_engine = "adjustText"
        return ax

    result = _deterministic_labels(
        ax, label_data, x, y, label, arrows,
        step_points=float(fallback_step_points),
        max_steps=int(fallback_max_steps),
        padding_points=float(fallback_padding_points),
        point_padding_factor=float(fallback_point_padding_factor),
        max_point_overlap=int(fallback_max_point_overlap),
        fontsize=float(fontsize),
    )
    ax._plot_code_retriever_label_engine = "deterministic_matplotlib"
    return result
