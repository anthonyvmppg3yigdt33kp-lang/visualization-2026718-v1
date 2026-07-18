"""Import-safe candidate distilled from a traceable plotting chain."""

CANDIDATE_SOURCE = "# source block: article-4329102050694250504-001-b010\nplt.figure(figsize=(10, 4), dpi=300)\nax4 = plt.gca()\n\n# Specify the IF channels that you want to plot\nif_channels = [2, 1]\n\nmapped_ims = []\nfor g in range(len(if_channels)):\n    # Grab the current IF channel\n    image = IF_image[min_x:max_x, min_y:max_y, if_channels[g]]\n    min_val = np.min(image)\n    max_val = np.max(image)\n\n    normalized_image = (image - min_val) / (max_val - min_val)\n\n    # If the channel is CD8A, perform a top hat and black hat transform\n    if if_channels[g] == 2:\n        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))\n        # Top Hat Transform\n        topHat = cv2.morphologyEx(normalized_image, cv2.MORPH_TOPHAT, kernel)\n        # Black Hat Transform\n        blackHat = cv2.morphologyEx(normalized_image, cv2.MORPH_BLACKHAT, kernel)\n\n        normalized_image = normalized_image + topHat - blackHat\n\n        normalized_image = normalized_image * 2\n\n    mapped_ims.append(normalized_image)\n\n# Add a last blank channel\nmapped_ims.append(\n    np.zeros(np.shape(IF_image[min_x:max_x, min_y:max_y, if_channels[g]]))\n)\n\nfull_im = np.dstack(mapped_ims)\nax4.imshow(full_im)\n\n# Add a black rectangle\nrectangle2 = Rectangle(\n    (second_min_y, second_min_x),\n    second_max_y - second_min_y,\n    second_max_x - second_min_x,\n    linewidth=4,\n    edgecolor=\"white\",\n    facecolor=\"none\",\n)\n\nax4.add_patch(rectangle2)\nax4.axis(\"off\")\nplt.show()\n"

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
    preferred = ['facecolor', 'edgecolor', 'linewidth', 'rectangle2', 'full_im', 'blackHat', 'topHat', 'kernel', 'normalized_image', 'max_val', 'min_val', 'image', 'mapped_ims', 'if_channels', 'ax4']
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
