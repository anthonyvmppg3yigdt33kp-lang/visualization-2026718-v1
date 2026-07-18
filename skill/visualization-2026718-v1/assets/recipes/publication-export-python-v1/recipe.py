"""Explicit Matplotlib publication export."""
from pathlib import Path


def export_publication_figure(figure, path, width: float, height: float, dpi: int = 600, transparent: bool = False):
    destination = Path(path)
    if destination.suffix.lower() not in {".pdf", ".svg", ".png", ".tif", ".tiff"}:
        raise ValueError("Supported formats: PDF, SVG, PNG, TIF, TIFF")
    if width <= 0 or height <= 0 or dpi <= 0:
        raise ValueError("width, height and dpi must be positive")
    figure.set_size_inches(width, height, forward=True)
    figure.savefig(destination, dpi=dpi, bbox_inches="tight", transparent=transparent)
    return destination
