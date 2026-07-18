"""Matplotlib borderless-axis modifier."""


def remove_axes_frame(ax, keep_labels: bool = False):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)
    ax.tick_params(left=False, bottom=False, labelleft=keep_labels, labelbottom=keep_labels)
    if not keep_labels:
        ax.set_xlabel("")
        ax.set_ylabel("")
    return ax
