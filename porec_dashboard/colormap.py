"""Shared colormaps for contact maps."""

from __future__ import annotations

from matplotlib.colors import LinearSegmentedColormap
import matplotlib as mpl

FALL_COLORS = [
    (1.0, 1.0, 1.0),
    (1.0, 0.9, 0.7),
    (0.99, 0.6, 0.2),
    (0.7, 0.1, 0.1),
    (0.1, 0.0, 0.0),
]


def get_fall_cmap() -> LinearSegmentedColormap:
    """Return the notebook 'fall' colormap, registering it if needed."""
    name = "fall"
    try:
        return mpl.colormaps[name]
    except KeyError:
        cmap = LinearSegmentedColormap.from_list(name, FALL_COLORS, N=256)
        mpl.colormaps.register(cmap, name=name, force=True)
        return cmap
