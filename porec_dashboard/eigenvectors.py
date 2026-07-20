"""Compartment / eigenvector calling."""

from __future__ import annotations

from pathlib import Path

import bioframe
import cooler
import cooltools
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .colormap import get_fall_cmap
from .plots import fetch_matrix


def make_view_df(clr: cooler.Cooler, chromosomes: list[str] | None = None) -> pd.DataFrame:
    """View frame for cooltools (bioframe.make_viewframe)."""
    chroms = chromosomes or list(clr.chromnames)
    sizes = pd.Series({c: int(clr.chromsizes[c]) for c in chroms})
    return bioframe.make_viewframe(sizes)


def gc_track_from_fasta(
    clr: cooler.Cooler,
    fasta_path: str | Path,
    chromosomes: list[str] | None = None,
) -> pd.DataFrame:
    """Bin-level GC fraction from a reference FASTA (notebook default)."""
    from .genome_harmonize import load_fasta_for_cooler

    bins = clr.bins()[:]
    if chromosomes is not None:
        chrom_set = set(chromosomes)
        bins = bins[bins["chrom"].isin(chrom_set)].copy()
        if bins.empty:
            raise ValueError("No bins remain after chromosome filter for GC phasing.")
    check_chroms = chromosomes if chromosomes is not None else sorted(bins["chrom"].unique())
    try:
        fasta = load_fasta_for_cooler(clr, fasta_path, chromosomes=check_chroms)
    except ImportError as exc:
        raise ImportError(
            "Reading FASTA for GC phasing requires pysam. "
            "Install it in your conda env, e.g. "
            "`conda install -c bioconda pysam` or `pip install pysam`, "
            "then restart the Streamlit app."
        ) from exc
    track_bins = bins[["chrom", "start", "end"]].copy()
    # Cooler uses categorical chrom names; pandas groupby may iterate unused
    # categories (e.g. chrEBV) unless we cast to plain strings.
    track_bins["chrom"] = track_bins["chrom"].astype(str)
    return bioframe.frac_gc(track_bins, fasta)


def compute_cis_eigenvectors(
    clr: cooler.Cooler,
    phasing_track: pd.DataFrame,
    *,
    view_df: pd.DataFrame | None = None,
    n_eigs: int = 3,
) -> tuple:
    """
    Run cooltools.eigs_cis.

    Returns (eigvals, eigvecs_dataframe).
    """
    view = view_df if view_df is not None else make_view_df(clr)
    track = phasing_track.copy()
    if "GC" not in track.columns:
        for alt in ("score", "value", "gc"):
            if alt in track.columns:
                track = track.rename(columns={alt: "GC"})
                break
    result = cooltools.eigs_cis(clr, track, view_df=view, n_eigs=n_eigs)
    if isinstance(result, tuple) and len(result) == 2:
        return result[0], result[1]
    return result, result


def plot_map_with_eigenvector(
    clr: cooler.Cooler,
    eig_df: pd.DataFrame,
    chrom: str,
    *,
    balance: bool = True,
    vmax: float = 0.1,
    figsize: tuple[float, float] = (12, 8),
) -> Figure:
    """Contact map with E1 track underneath (notebook style)."""
    start, end = 0, int(clr.chromsizes[chrom])
    mat = fetch_matrix(clr, (chrom, start, end), balance=balance)
    eig_chrom = eig_df[eig_df["chrom"] == chrom].copy()
    if "E1" not in eig_chrom.columns:
        raise ValueError("Eigenvector table missing E1 column.")

    fig, ax = plt.subplots(figsize=figsize)
    norm = LogNorm(vmin=1e-4, vmax=vmax)
    im = ax.matshow(mat, cmap=get_fall_cmap(), norm=norm, interpolation="none")
    ax.xaxis.set_ticks_position("bottom")
    ax.set_title(f"{chrom} — contact map + E1 ({clr.binsize} bp)")

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)
    fig.colorbar(im, cax=cax, label="corrected frequencies")

    eig_ax = divider.append_axes("bottom", size="18%", pad=0.35, sharex=ax)
    x = ((eig_chrom["start"] + eig_chrom["end"]) / 2).to_numpy()
    binsize = clr.binsize
    x_bins = x / binsize
    y = eig_chrom["E1"].to_numpy()
    eig_ax.fill_between(x_bins, 0, y, where=y >= 0, color="#d62728", alpha=0.7, linewidth=0)
    eig_ax.fill_between(x_bins, 0, y, where=y < 0, color="#1f77b4", alpha=0.7, linewidth=0)
    eig_ax.axhline(0, color="black", linewidth=0.5)
    eig_ax.set_ylabel("E1")
    eig_ax.set_xlabel("bin")
    fig.tight_layout()
    return fig
