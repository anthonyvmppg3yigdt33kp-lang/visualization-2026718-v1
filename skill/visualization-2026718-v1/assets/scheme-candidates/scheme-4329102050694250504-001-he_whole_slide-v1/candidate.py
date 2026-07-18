"""Import-safe candidate distilled from a traceable plotting chain."""

CANDIDATE_SOURCE = "# source block: article-4329102050694250504-001-b008\n# Downsize by 4 to speed up plotting with minimal resolution loss\nplot_down = 4\n\n# Load in the H&E image\nthumbnail = cv2.resize(\n    h_an_e, (np.shape(h_an_e)[0] // plot_down, np.shape(h_an_e)[1] // plot_down)\n)\n# Define the RGB value for black\nblack_color = [0, 0, 0]\n\n# Create a mask for black pixels\nblack_pixels = np.all(thumbnail[:, :, :3] == black_color, axis=-1)\n\n# Replace black pixels with white\nthumbnail[black_pixels] = [255, 255, 255]\n\n# Plot the large H&E staining\nplt.figure(figsize=(10, 10))\nax0 = plt.gca()\n# 'thumbnail' is the image data\nax0.imshow(thumbnail)\nax0.set_xlim(300, np.shape(thumbnail)[1])\nax0.set_ylim(np.shape(thumbnail)[0], 400)\n\n# Add a black rectangle\nrectangle = Rectangle(\n    (min_y // plot_down, min_x // plot_down),\n    max_y // plot_down - min_y // plot_down,\n    max_x // plot_down - min_x // plot_down,\n    linewidth=2,\n    edgecolor=\"black\",\n    facecolor=\"none\",\n)\nax0.add_patch(rectangle)\nax0.axis(\"off\")\nplt.show()\n"

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
    preferred = ['facecolor', 'edgecolor', 'linewidth', 'rectangle', 'ax0', 'black_pixels', 'black_color', 'thumbnail', 'plot_down']
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
