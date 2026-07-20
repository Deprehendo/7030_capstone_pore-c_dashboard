"""Contact-map matrix helpers and matplotlib figures."""

from __future__ import annotations

import itertools
from typing import Sequence

import cooler
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from matplotlib.ticker import EngFormatter
from scipy.linalg import block_diag

from .colormap import get_fall_cmap
from .cooler_io import analysis_chromosomes


def fetch_matrix(
    clr: cooler.Cooler,
    region: str | tuple,
    *,
    balance: bool = True,
) -> np.ndarray:
    """Fetch a (balanced) contact matrix; NaNs → 0."""
    mat = clr.matrix(balance=balance).fetch(region)
    return np.nan_to_num(np.asarray(mat, dtype=float), nan=0.0)


def build_genome_matrix(
    clr: cooler.Cooler,
    chromosomes: Sequence[str] | None = None,
    *,
    balance: bool = True,
) -> tuple[np.ndarray, list[str], list[int]]:
    """
    Build a full genome contact matrix (cis blocks + filled trans).

    Returns (matrix, chromosomes, bin_counts_per_chrom).
    """
    chroms = list(chromosomes) if chromosomes is not None else analysis_chromosomes(clr)
    matrices = []
    bin_counts: list[int] = []
    for chrom in chroms:
        m = fetch_matrix(clr, chrom, balance=balance)
        matrices.append(m)
        bin_counts.append(m.shape[0])

    genome = block_diag(*matrices)
    offsets = np.concatenate([[0], np.cumsum(bin_counts)])

    for i, chrom_i in enumerate(chroms):
        for j, chrom_j in enumerate(chroms):
            if i >= j:
                continue
            trans = np.nan_to_num(
                np.asarray(clr.matrix(balance=balance).fetch(chrom_i, chrom_j), dtype=float),
                nan=0.0,
            )
            r0, r1 = offsets[i], offsets[i + 1]
            c0, c1 = offsets[j], offsets[j + 1]
            genome[r0:r1, c0:c1] = trans
            genome[c0:c1, r0:r1] = trans.T

    return genome, chroms, bin_counts


def plot_genome_wide(
    clr: cooler.Cooler,
    *,
    chromosomes: Sequence[str] | None = None,
    balance: bool = True,
    vmax_percentile: float = 97,
    figsize: tuple[float, float] = (10, 10),
    title: str | None = None,
) -> Figure:
    """Whole-genome contact heatmap (notebook style)."""
    genome, chroms, bin_counts = build_genome_matrix(
        clr, chromosomes=chromosomes, balance=balance
    )
    plot_matrix = genome.copy()
    plot_matrix[plot_matrix == 0] = np.nan
    nonzero = plot_matrix[np.isfinite(plot_matrix) & (plot_matrix > 0)]
    if nonzero.size == 0:
        raise ValueError("No positive contacts to plot. Check balancing / resolution.")

    vmin = float(np.percentile(nonzero, 0))
    vmax = float(np.percentile(nonzero, vmax_percentile))
    if vmin <= 0:
        vmin = float(nonzero.min())

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(
        plot_matrix,
        cmap=get_fall_cmap(),
        norm=LogNorm(vmin=max(vmin, np.finfo(float).tiny), vmax=vmax),
        interpolation="none",
    )
    boundaries = np.cumsum(bin_counts)[:-1]
    for b in boundaries:
        ax.axhline(b, color="black", linewidth=0.4, alpha=0.6)
        ax.axvline(b, color="black", linewidth=0.4, alpha=0.6)

    centers = []
    start = 0
    for count in bin_counts:
        centers.append(start + count / 2)
        start += count
    ax.set_xticks(centers)
    ax.set_xticklabels(list(chroms), rotation=90, fontsize=9)
    ax.set_yticks(centers)
    ax.set_yticklabels(list(chroms), fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("corrected frequencies")
    res = clr.binsize
    ax.set_title(title or f"Whole-genome contact matrix ({res // 1000} kb)")
    fig.tight_layout()
    return fig


def plot_chromosome_map(
    clr: cooler.Cooler,
    chrom: str,
    *,
    start: int | None = None,
    end: int | None = None,
    balance: bool = True,
    vmax: float | None = 0.1,
    figsize: tuple[float, float] = (8, 8),
    title: str | None = None,
) -> Figure:
    """Square contact map for one chromosome or region."""
    chrom_len = int(clr.chromsizes[chrom])
    s = 0 if start is None else int(start)
    e = chrom_len if end is None else int(end)
    region = (chrom, s, e)
    mat = fetch_matrix(clr, region, balance=balance)

    fig, ax = plt.subplots(figsize=figsize)
    if vmax is not None:
        norm = LogNorm(vmin=1e-4, vmax=vmax)
        im = ax.matshow(mat, cmap=get_fall_cmap(), norm=norm, interpolation="none")
    else:
        nonzero = mat[mat > 0]
        vmax_auto = float(np.percentile(nonzero, 97)) if nonzero.size else 1.0
        im = ax.matshow(
            np.where(mat > 0, mat, np.nan),
            cmap=get_fall_cmap(),
            norm=LogNorm(vmin=max(nonzero.min(), 1e-6) if nonzero.size else 1e-6, vmax=vmax_auto),
            interpolation="none",
        )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="corrected frequencies")
    ax.set_title(title or f"{chrom}:{s}-{e} ({clr.binsize} bp)")
    ax.xaxis.set_ticks_position("bottom")
    fig.tight_layout()
    return fig


def pcolormesh_45deg(ax, matrix_c, start: int = 0, resolution: int = 1, *args, **kwargs):
    """Triangle / 45-degree contact map (cooltools tutorial style)."""
    start_pos_vector = [start + resolution * i for i in range(len(matrix_c) + 1)]
    n = matrix_c.shape[0]
    t = np.array([[1, 0.5], [-1, 0.5]])
    matrix_a = np.dot(
        np.array(
            [(i[1], i[0]) for i in itertools.product(start_pos_vector[::-1], start_pos_vector)]
        ),
        t,
    )
    x = matrix_a[:, 1].reshape(n + 1, n + 1)
    y = matrix_a[:, 0].reshape(n + 1, n + 1)
    im = ax.pcolormesh(x, y, np.flipud(matrix_c), *args, **kwargs)
    im.set_rasterized(True)
    return im


def format_ticks(ax, x: bool = True, y: bool = True, rotate: bool = True) -> None:
    bp_formatter = EngFormatter("b")
    if y:
        ax.yaxis.set_major_formatter(bp_formatter)
    if x:
        ax.xaxis.set_major_formatter(bp_formatter)
        ax.xaxis.tick_bottom()
    if rotate:
        ax.tick_params(axis="x", rotation=45)
