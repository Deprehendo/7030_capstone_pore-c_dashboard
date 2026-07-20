"""Insulation score / TAD boundary helpers."""

from __future__ import annotations

import cooler
import cooltools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from .eigenvectors import make_view_df
from .plots import fetch_matrix, format_ticks, pcolormesh_45deg


def suggest_triangle_vmax(
    clr: cooler.Cooler,
    chrom: str,
    *,
    region_start: int = 0,
    region_end: int | None = None,
    balance: bool = True,
    percentile: float = 98.0,
    floor: float = 1e-4,
) -> tuple[float, float, float]:
    """Suggest LogNorm vmax from balanced contact percentiles in a viewed region."""
    chrom_len = int(clr.chromsizes[chrom])
    end = chrom_len if region_end is None else min(int(region_end), chrom_len)
    mat = fetch_matrix(clr, (chrom, region_start, end), balance=balance)
    positive = mat[mat > 0]
    if positive.size == 0:
        return floor, 0.0, 0.0
    p95 = float(np.percentile(positive, 95))
    p98 = float(np.percentile(positive, percentile))
    return max(p98, floor), p95, p98


def default_view_span_bp(primary_window: int) -> int:
    """Genomic span for triangle zoom — ~4× strong insulation window."""
    return int(4 * primary_window)


def region_contact_stats(
    clr: cooler.Cooler,
    chrom: str,
    region_start: int,
    region_end: int,
    *,
    balance: bool = True,
) -> tuple[float, float]:
    """Return (fraction of pixels with finite contacts, max value) in a viewport."""
    mat = fetch_matrix(clr, (chrom, region_start, region_end), balance=balance)
    valid = np.isfinite(mat) & (mat > 0)
    n = mat.size
    frac = float(valid.sum()) / n if n else 0.0
    max_val = float(np.max(mat[valid])) if valid.any() else 0.0
    return frac, max_val


def suggest_triangle_region_start(
    clr: cooler.Cooler,
    chrom: str,
    span_bp: int,
    *,
    balance: bool = True,
    min_fraction: float = 0.05,
) -> tuple[int, float]:
    """Pick a viewport start with enough contacts for triangle display."""
    chrom_len = int(clr.chromsizes[chrom])
    span = min(int(span_bp), chrom_len)
    if span <= 0:
        return 0, 0.0
    resolution = int(clr.binsize)
    step = max(resolution * 25, span // 4, resolution)
    best_start = 0
    best_frac = 0.0
    for start in range(0, max(1, chrom_len - span + 1), step):
        frac, _ = region_contact_stats(clr, chrom, start, start + span, balance=balance)
        if frac >= min_fraction:
            return start, frac
        if frac > best_frac:
            best_frac = frac
            best_start = start
    return best_start, best_frac


def chromosomes_for_insulation(
    clr: cooler.Cooler,
    chromosomes: list[str],
    windows: list[int],
) -> list[str]:
    """Keep chromosomes long enough for the largest insulation window."""
    min_len = max(windows)
    return [c for c in chromosomes if int(clr.chromsizes[c]) >= min_len]


def compute_insulation(
    clr: cooler.Cooler,
    windows: list[int] | None = None,
    *,
    view_df: pd.DataFrame | None = None,
    chromosomes: list[str] | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Run cooltools.insulation.

    Default windows: 10× and 25× binsize (matches notebook 10 kb practice).
    Pass ``chromosomes`` or ``view_df`` to restrict regions (recommended for human mcools).
    """
    resolution = int(clr.binsize)
    if windows is None:
        windows = [10 * resolution, 25 * resolution]
    if view_df is None and chromosomes is not None:
        usable = chromosomes_for_insulation(clr, chromosomes, windows)
        if not usable:
            raise ValueError(
                f"No chromosomes are at least {max(windows):,} bp long for the selected "
                "insulation windows. Try smaller windows or exclude short contigs."
            )
        view_df = make_view_df(clr, usable)
    return cooltools.insulation(clr, windows, view_df=view_df, verbose=verbose)


def boundary_table(
    insulation_table: pd.DataFrame,
    *,
    strong_window: int,
    weak_window: int,
) -> pd.DataFrame:
    """
    Simplified biology mapping:
    - strong_window (e.g. 100 kb): is_boundary → strong
    - weak_window (e.g. 250 kb): is_boundary → weak
    """
    rows: list[dict] = []
    for window, label in ((strong_window, "strong"), (weak_window, "weak")):
        boundary_col = f"is_boundary_{window}"
        strength_col = f"boundary_strength_{window}"
        if boundary_col not in insulation_table.columns:
            continue
        sub = insulation_table.loc[insulation_table[boundary_col] == True].copy()  # noqa: E712
        for _, r in sub.iterrows():
            strength = (
                float(r[strength_col])
                if strength_col in insulation_table.columns and pd.notna(r.get(strength_col))
                else float("nan")
            )
            rows.append(
                {
                    "chrom": r["chrom"],
                    "start": int(r["start"]),
                    "end": int(r["end"]),
                    "window_bp": int(window),
                    "strength_class": label,
                    "boundary_strength": strength,
                }
            )
    return pd.DataFrame(rows)


def _score_columns(insulation_table: pd.DataFrame) -> list[tuple[int, str]]:
    cols = []
    for c in insulation_table.columns:
        if c.startswith("log2_insulation_score_"):
            try:
                w = int(c.split("_")[-1])
            except ValueError:
                continue
            cols.append((w, c))
    return sorted(cols, key=lambda x: x[0])


def _insulation_ylim(
    insul_df: pd.DataFrame,
    score_cols: list[str],
    *,
    pad_fraction: float = 0.12,
) -> tuple[float, float]:
    """Robust y-limits from score percentiles (avoids outlier compression)."""
    if not score_cols or insul_df.empty:
        return -1.0, 1.0
    vals = insul_df[score_cols].to_numpy().astype(float, copy=False).ravel()
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return -1.0, 1.0
    lo, hi = np.percentile(vals, [3, 97])
    if lo == hi:
        lo -= 0.1
        hi += 0.1
    margin = (hi - lo) * pad_fraction
    return float(lo - margin), float(hi + margin)


def _insul_in_viewport(insul_df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    return insul_df[(insul_df["end"] > start) & (insul_df["start"] < end)].copy()


def _plot_insulation_curves(
    ax,
    insul_df: pd.DataFrame,
    windows: list[int],
    *,
    primary_window: int,
    secondary_window: int | None,
    linewidth_scale: float = 1.0,
) -> list[Line2D]:
    """Draw log2 insulation score curves; return line handles for legend."""
    if insul_df.empty:
        return []
    x = insul_df[["start", "end"]].mean(axis=1)
    styles = {
        primary_window: {"color": "steelblue", "linewidth": 2.2 * linewidth_scale, "alpha": 1.0},
        secondary_window: {"color": "darkorange", "linewidth": 1.8 * linewidth_scale, "alpha": 0.85},
    }
    handles: list[Line2D] = []
    for w in windows:
        col = f"log2_insulation_score_{w}"
        if col not in insul_df.columns:
            continue
        style = styles.get(w, {"color": "gray", "linewidth": 1.5 * linewidth_scale, "alpha": 0.8})
        (line,) = ax.plot(
            x,
            insul_df[col],
            label=f"Insulation {w:,} bp",
            **{k: v for k, v in style.items() if k in ("color", "linewidth", "alpha")},
        )
        handles.append(line)
    return handles


def _plot_boundary_vlines(
    ax,
    insul_df: pd.DataFrame,
    boundary_specs: list[tuple[int, str, dict]],
    y_min: float,
    y_max: float,
) -> list[Line2D]:
    """Draw boundary markers in viewport; return legend handles."""
    handles: list[Line2D] = []
    for w, label, style in boundary_specs:
        boundary_col = f"is_boundary_{w}"
        if boundary_col not in insul_df.columns:
            continue
        called = insul_df[insul_df[boundary_col] == True]  # noqa: E712
        if called.empty:
            continue
        mids = called[["start", "end"]].mean(axis=1)
        ax.vlines(mids, ymin=y_min, ymax=y_max, **style)
        handles.append(
            Line2D(
                [0],
                [0],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=style["linewidth"],
                alpha=style["alpha"],
                label=f"{label.capitalize()} boundary ({w:,} bp)",
            )
        )
    return handles


def plot_triangle_with_insulation(
    clr: cooler.Cooler,
    insulation_table: pd.DataFrame,
    chrom: str,
    *,
    primary_window: int | None = None,
    secondary_window: int | None = None,
    window: int | None = None,
    balance: bool = True,
    vmax: float | None = None,
    vmin: float = 1e-4,
    region_start: int = 0,
    region_end: int | None = None,
    view_span_bp: int | None = None,
    ylim_bp: int | None = None,
    figsize: tuple[float, float] = (14, 8.5),
) -> Figure:
    """
    Triangle contact map (viewport) + detail insulation (viewport) + genome overview strip.

    Detail panel: scores and boundaries aligned with the triangle window.
    Overview strip: full-chromosome curves only (no boundary vlines), viewport shaded.
    """
    if primary_window is None:
        primary_window = window

    score_cols = _score_columns(insulation_table)
    if not score_cols:
        raise ValueError("Insulation table has no log2_insulation_score_* columns.")

    resolution = int(clr.binsize)
    chrom_len = int(clr.chromsizes[chrom])
    region_start = max(0, int(region_start))

    if primary_window is None:
        primary_window = score_cols[0][0]
    if secondary_window is None and len(score_cols) > 1:
        for w, _ in score_cols:
            if w != primary_window:
                secondary_window = w
                break

    if view_span_bp is None and region_end is None:
        view_span_bp = default_view_span_bp(int(primary_window))

    if region_end is None:
        if view_span_bp is not None:
            region_end = min(region_start + int(view_span_bp), chrom_len)
        else:
            region_end = chrom_len
    else:
        region_end = min(int(region_end), chrom_len)

    view_span = region_end - region_start
    data = fetch_matrix(clr, (chrom, region_start, region_end), balance=balance)

    if vmax is None:
        suggested, _, _ = suggest_triangle_vmax(
            clr,
            chrom,
            region_start=region_start,
            region_end=region_end,
            balance=balance,
        )
        vmax = suggested

    windows = [w for w in (primary_window, secondary_window) if w is not None]
    insul_full = insulation_table[insulation_table["chrom"] == chrom].copy()
    insul_viewport = _insul_in_viewport(insul_full, region_start, region_end)
    score_col_names = [f"log2_insulation_score_{w}" for w in windows]
    score_cols_present = [c for c in score_col_names if c in insul_full.columns]
    y_detail_min, y_detail_max = _insulation_ylim(insul_viewport, score_cols_present)
    ylim = ylim_bp if ylim_bp is not None else view_span

    boundary_specs: list[tuple[int, str, dict]] = [
        (
            int(primary_window),
            "strong",
            {"color": "#1f4e79", "linestyle": "-", "linewidth": 1.5, "alpha": 0.9},
        ),
    ]
    if secondary_window is not None:
        boundary_specs.append(
            (
                int(secondary_window),
                "weak",
                {"color": "#c0392b", "linestyle": "--", "linewidth": 1.1, "alpha": 0.65},
            )
        )

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(
        4,
        2,
        height_ratios=[3.2, 1.6, 0.55, 0.35],
        width_ratios=[40, 1],
        hspace=0.28,
        wspace=0.02,
    )
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])
    ins_detail = fig.add_subplot(gs[1, 0])
    ins_overview = fig.add_subplot(gs[2, 0])
    leg_ax = fig.add_subplot(gs[3, :])
    leg_ax.axis("off")

    norm = LogNorm(vmax=vmax, vmin=vmin)
    im = pcolormesh_45deg(
        ax,
        data,
        start=region_start,
        resolution=resolution,
        norm=norm,
        cmap="PuOr",
    )
    ax.set_ylim(0, ylim)
    ax.set_xlim(region_start, region_end)
    ax.xaxis.set_visible(False)
    span_mb = view_span / 1_000_000
    ax.set_title(
        f"{chrom}:{region_start:,}–{region_end:,} ({span_mb:.2f} Mb triangle) — "
        f"{resolution // 1000} kb bins; strong={primary_window:,} bp, weak={secondary_window:,} bp"
        if secondary_window
        else f"{chrom}:{region_start:,}–{region_end:,} ({span_mb:.2f} Mb triangle) — "
        f"{resolution // 1000} kb bins; strong={primary_window:,} bp"
    )
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Corrected contacts")

    legend_handles: list[Line2D] = []
    legend_handles.extend(
        _plot_insulation_curves(
            ins_detail,
            insul_viewport,
            windows,
            primary_window=int(primary_window),
            secondary_window=secondary_window,
        )
    )
    legend_handles.extend(
        _plot_boundary_vlines(ins_detail, insul_viewport, boundary_specs, y_detail_min, y_detail_max)
    )
    ins_detail.axhline(0, color="black", linewidth=0.5)
    ins_detail.set_ylim(y_detail_min, y_detail_max)
    ins_detail.set_xlim(region_start, region_end)
    ins_detail.set_ylabel("log2 insulation\n(this view)")
    format_ticks(ins_detail, y=False, rotate=False)

    _plot_insulation_curves(
        ins_overview,
        insul_full,
        windows,
        primary_window=int(primary_window),
        secondary_window=secondary_window,
        linewidth_scale=0.65,
    )
    ins_overview.axvspan(region_start, region_end, color="gray", alpha=0.2, zorder=0)
    ins_overview.set_xlim(0, chrom_len)
    ins_overview.set_ylim(y_detail_min, y_detail_max)
    ins_overview.axhline(0, color="black", linewidth=0.4, alpha=0.5)
    ins_overview.set_ylabel("overview", fontsize=8)
    ins_overview.set_xlabel(f"Genomic position on {chrom} (shaded = triangle viewport)")
    format_ticks(ins_overview, y=False, rotate=False)

    seen: set[str] = set()
    unique_handles = []
    for h in legend_handles:
        lab = h.get_label()
        if lab in seen or lab.startswith("_"):
            continue
        seen.add(lab)
        unique_handles.append(h)
    if unique_handles:
        leg_ax.legend(
            handles=unique_handles,
            loc="center",
            ncol=min(4, len(unique_handles)),
            fontsize=9,
            frameon=False,
        )

    fig.tight_layout()
    return fig


TAD_METHOD_NOTES = """
**Insulation score (default)** — Best starting point for moderate-depth Pore-C across organisms.
Looks for dips in contacts across a sliding window. Window size matters (often ~10× bin size).

**Directionality index (DI)** — Classic mammalian TAD caller (Dixon). Needs clearer domains
and usually deeper coverage; more common for human Hi-C.

**Arrowhead (Juicer)** — Corner-enrichment domains; strong for large mammalian genomes;
heavier dependency stack.

**Plants** — Domains can be weaker or structured differently; start with insulation and
conservative resolutions; polyploidy needs care.
"""
