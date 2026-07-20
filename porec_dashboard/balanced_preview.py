"""Balanced normalization preview — notebook cell 5 (25 kb contact map)."""

from __future__ import annotations

import numpy as np
import cooler
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .colormap import get_fall_cmap


def suggest_vmax(
    clr: cooler.Cooler,
    chrom: str,
    *,
    balance: bool = True,
    percentile: float = 98.0,
    floor: float = 0.001,
) -> tuple[float, float, float]:
    """
    Suggest display vmax from log1p(balanced) matrix percentiles.

    Returns (suggested_vmax, p95, p98).
    """
    mat = clr.matrix(balance=balance).fetch(chrom)
    mat = np.nan_to_num(mat, nan=0.0)
    positive = mat[mat > 0]
    if positive.size == 0:
        return floor, 0.0, 0.0
    log_vals = np.log1p(positive)
    p95 = float(np.percentile(log_vals, 95))
    p98 = float(np.percentile(log_vals, percentile))
    suggested = max(p98, floor)
    return suggested, p95, p98


def plot_balanced_normalization_preview(
    clr: cooler.Cooler,
    chrom: str,
    *,
    vmax: float = 2.0,
    figsize: tuple[float, float] = (8, 8),
    balance: bool = True,
) -> Figure:
    """
    Single-chromosome balanced contact map using log1p(contacts).

    Matches Pore_C_wt_analysis.ipynb: fall colormap, vmax=2, log1p scale.
    """
    mat = clr.matrix(balance=balance).fetch(chrom)
    mat = np.nan_to_num(mat, nan=0.0)

    res_kb = clr.binsize // 1000
    balance_label = "balanced" if balance else "raw"
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(
        np.log1p(mat),
        cmap=get_fall_cmap(),
        vmax=vmax,
        interpolation="none",
    )
    plt.colorbar(im, ax=ax, label="log1p(contacts)")
    ax.set_title(f"{chrom} — {res_kb} kb {balance_label} normalization")
    fig.tight_layout()
    return fig
