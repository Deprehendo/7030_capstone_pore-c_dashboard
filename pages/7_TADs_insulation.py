"""TADs / insulation — scrub, bookmark, export; W1 strong / W2 weak."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from porec_dashboard.analysis_cache import get_cached, set_cached
from porec_dashboard.batch_export import zip_bytes_with_extra
from porec_dashboard.cooler_io import (
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.help_text import TADS
from porec_dashboard.insulation import (
    TAD_METHOD_NOTES,
    boundary_table,
    compute_insulation,
    default_view_span_bp,
    plot_triangle_with_insulation,
    region_contact_stats,
    suggest_triangle_region_start,
    suggest_triangle_vmax,
)
from porec_dashboard.organism_guidance import show_organism_guidance
from porec_dashboard.ui_common import (
    fig_to_png_bytes,
    filtered_chromosomes,
    nav_back_hub,
    preferred_view_resolution,
    require_mcool,
    scroll_to_top,
    show_help_block,
    show_view_resolution_tip,
)

st.set_page_config(page_title="TADs / insulation", layout="wide")
scroll_to_top()
nav_back_hub(key="tad_top")

show_help_block(TADS)
show_organism_guidance("tads")

with st.expander("Other TAD methods (reference)", expanded=False):
    st.markdown(TAD_METHOD_NOTES)

if "tad_bookmarks" not in st.session_state:
    st.session_state["tad_bookmarks"] = []


def _bookmark_png_name(bm: dict) -> str:
    s_mb = bm["region_start"] / 1_000_000
    e_mb = bm["region_end"] / 1_000_000
    label = bm.get("label", "").strip()
    suffix = f"_{label}" if label else ""
    return (
        f"bookmarked_figures/{bm['chrom']}_{s_mb:.1f}-{e_mb:.1f}Mb"
        f"_insulation_{bm['resolution']}bp{suffix}.png"
    )


def _render_tad_figure(
    clr,
    ins: pd.DataFrame,
    chrom: str,
    *,
    w1: int,
    w2: int,
    region_start: int,
    view_span_bp: int,
    plot_vmax: float | None,
    balanced: bool,
) -> plt.Figure:
    region_end = min(region_start + view_span_bp, int(clr.chromsizes[chrom]))
    return plot_triangle_with_insulation(
        clr,
        ins,
        chrom,
        primary_window=w1,
        secondary_window=w2,
        balance=balanced,
        vmax=plot_vmax,
        region_start=region_start,
        region_end=region_end,
    )


mcool, exclude = require_mcool()
resolutions = list_resolutions(mcool)
show_view_resolution_tip()
tad_default = preferred_view_resolution(resolutions)
tad_res = st.selectbox(
    "Resolution for insulation",
    options=resolutions,
    index=resolutions.index(tad_default),
    help="~10 kb is a common resolution for insulation when depth allows.",
)
clr_tad = open_cooler(mcool, tad_res)
balanced = has_weights(clr_tad)

st.markdown("#### Insulation windows")
st.info(
    f"**Window 1** (default {10 * tad_res:,} bp) → **strong** boundaries. "
    f"**Window 2** (default {25 * tad_res:,} bp) → **weak** boundaries. "
    "Scrub along each chromosome, bookmark regions for figures. "
    "CSV tables cover the full genome for quantitative work."
)

w1 = int(
    st.number_input(
        "Window 1 (bp) — strong boundaries",
        value=10 * tad_res,
        step=tad_res,
        help="Often 100000 at 10 kb resolution.",
    )
)
w2 = int(
    st.number_input(
        "Window 2 (bp) — weak boundaries",
        value=25 * tad_res,
        step=tad_res,
        help="Often 250000 at 10 kb resolution.",
    )
)

tad_chroms = filtered_chromosomes(clr_tad, exclude, purpose="general")

if not balanced:
    st.warning("Balancing this resolution first is strongly recommended (Normalize page).")

if st.button("Compute insulation / boundaries", type="primary"):
    if not balanced:
        st.error(
            "cooltools.insulation requires ICE balancing weights. Run **Normalize** first "
            "(or select the `.balanced.mcool` working copy in the sidebar)."
        )
        st.stop()
    try:
        cache_parts = (mcool, tad_res, w1, w2, tuple(tad_chroms))
        ins = get_cached("insulation", *cache_parts)
        if ins is None:
            with st.spinner("Running cooltools.insulation…"):
                ins = compute_insulation(
                    clr_tad,
                    windows=[w1, w2],
                    chromosomes=tad_chroms,
                    verbose=False,
                )
            set_cached("insulation", ins, *cache_parts)
        else:
            st.info("Using cached insulation result for this mcool, resolution, and windows.")
        st.session_state["insulation_table"] = ins
        bounds = boundary_table(ins, strong_window=w1, weak_window=w2)
        st.session_state["tad_bounds"] = bounds
        st.session_state["tad_plot_params"] = {
            "mcool": mcool,
            "resolution": tad_res,
            "w1": w1,
            "w2": w2,
        }
        n_strong = int((bounds["strength_class"] == "strong").sum()) if len(bounds) else 0
        n_weak = int((bounds["strength_class"] == "weak").sum()) if len(bounds) else 0
        st.success(
            f"**{n_strong} strong** (window {w1:,} bp), "
            f"**{n_weak} weak** (window {w2:,} bp). Scrub and bookmark below."
        )
    except Exception as exc:  # noqa: BLE001
        st.exception(exc)

if "insulation_table" in st.session_state:
    ins = st.session_state["insulation_table"]
    bounds = st.session_state.get("tad_bounds", pd.DataFrame())

    st.download_button(
        "Download insulation table (CSV)",
        ins.to_csv(index=False).encode(),
        "insulation_table.csv",
        "text/csv",
    )
    st.download_button(
        "Download strong/weak boundaries (CSV)",
        bounds.to_csv(index=False).encode(),
        "tad_boundaries_strong_weak.csv",
        "text/csv",
    )

    st.markdown("#### Explore & bookmark")
    st.caption(
        "The insulation track shows the **full chromosome**. "
        "Scrub the triangle viewport along the chrom, then bookmark regions for export."
    )

    explore_chrom = st.selectbox("Chromosome", tad_chroms, key="tad_explore_chrom")
    chrom_len = int(clr_tad.chromsizes[explore_chrom])
    default_span_bp = default_view_span_bp(w1)
    default_span_mb = default_span_bp / 1_000_000
    max_span_mb = min(5.0, chrom_len / 1_000_000)

    view_span_mb = st.slider(
        "Triangle view span (Mb)",
        min_value=0.1,
        max_value=max(0.2, max_span_mb),
        value=float(min(default_span_mb, max_span_mb)),
        step=0.05,
        help=f"Width of the triangle contact map. Default ≈ 4× Window 1 ({default_span_mb:.2f} Mb).",
        key=f"tad_view_span_{explore_chrom}",
    )
    view_span_bp = max(int(view_span_mb * 1_000_000), tad_res)
    max_start = max(0, chrom_len - view_span_bp)

    scrub_store_key = f"tad_scrub_pos_{explore_chrom}_{view_span_bp}"
    if scrub_store_key not in st.session_state:
        auto_start, auto_frac = suggest_triangle_region_start(
            clr_tad, explore_chrom, view_span_bp, balance=balanced
        )
        st.session_state[scrub_store_key] = min(auto_start, max_start)
        if auto_frac < 0.01:
            st.session_state[f"{scrub_store_key}_warn"] = True

    region_start = st.slider(
        "Scrub position along chromosome (bp)",
        min_value=0,
        max_value=max_start,
        value=min(int(st.session_state[scrub_store_key]), max_start),
        step=tad_res,
        help="Pans the triangle contact map. Insulation track stays full-chromosome.",
        key=f"tad_scrub_slider_{explore_chrom}_{view_span_bp}",
    )
    st.session_state[scrub_store_key] = region_start
    region_end = min(region_start + view_span_bp, chrom_len)
    st.caption(
        f"Triangle viewport: **{explore_chrom}:{region_start:,}–{region_end:,}** "
        f"({(region_end - region_start) / 1e6:.2f} Mb)"
    )

    auto_vmax = st.checkbox("Auto-scale triangle color (recommended)", value=True, key="tad_auto_vmax")
    plot_vmax: float | None = None
    if not auto_vmax:
        plot_vmax = st.number_input(
            "vmax (triangle color scale)",
            value=0.1,
            min_value=1e-5,
            format="%.5f",
            key="tad_manual_vmax",
        )
    else:
        sug, p95, _ = suggest_triangle_vmax(
            clr_tad,
            explore_chrom,
            region_start=region_start,
            region_end=region_end,
            balance=balanced,
        )
        plot_vmax = None
        st.caption(f"Auto vmax ≈ **{sug:.5f}** (p95 ≈ {p95:.5f} in this viewport).")

    contact_frac, _ = region_contact_stats(
        clr_tad, explore_chrom, region_start, region_end, balance=balanced
    )
    if contact_frac < 0.01:
        st.warning(
            "Very few contacts in this viewport — scrub to a different position "
            "or widen the view span."
        )

    fig = _render_tad_figure(
        clr_tad,
        ins,
        explore_chrom,
        w1=w1,
        w2=w2,
        region_start=region_start,
        view_span_bp=view_span_bp,
        plot_vmax=plot_vmax,
        balanced=balanced,
    )
    st.pyplot(fig)

    bm_col1, bm_col2, bm_col3 = st.columns([1, 1, 2])
    with bm_col1:
        bookmark_label = st.text_input(
            "Label (optional)",
            value="",
            key="tad_bookmark_label",
            placeholder="e.g. chr21 TAD cluster",
        )
        if st.button("Bookmark this view", type="secondary"):
            entry = {
                "chrom": explore_chrom,
                "region_start": region_start,
                "region_end": region_end,
                "view_span_bp": view_span_bp,
                "vmax": plot_vmax,
                "w1": w1,
                "w2": w2,
                "resolution": tad_res,
                "label": bookmark_label.strip(),
            }
            st.session_state["tad_bookmarks"].append(entry)
            st.success(f"Bookmarked {explore_chrom}:{region_start:,}–{region_end:,}")
    with bm_col2:
        st.download_button(
            "Download current view (PNG)",
            data=fig_to_png_bytes(fig),
            file_name=f"{explore_chrom}_{region_start}_{region_end}_insulation_{tad_res}bp.png",
            mime="image/png",
        )
    plt.close(fig)

    bookmarks: list[dict] = st.session_state["tad_bookmarks"]
    if bookmarks:
        st.markdown("#### Saved regions")
        bm_df = pd.DataFrame(
            [
                {
                    "#": i + 1,
                    "chrom": b["chrom"],
                    "start_Mb": round(b["region_start"] / 1e6, 2),
                    "end_Mb": round(b["region_end"] / 1e6, 2),
                    "span_Mb": round(b["view_span_bp"] / 1e6, 2),
                    "label": b.get("label") or "",
                }
                for i, b in enumerate(bookmarks)
            ]
        )
        st.dataframe(bm_df, hide_index=True, use_container_width=True)

        remove_idx = st.number_input(
            "Remove bookmark # (0 = none)",
            min_value=0,
            max_value=len(bookmarks),
            value=0,
            step=1,
            key="tad_remove_idx",
        )
        if st.button("Remove selected bookmark") and remove_idx > 0:
            st.session_state["tad_bookmarks"].pop(int(remove_idx) - 1)
            st.rerun()

        if st.button("Export bookmarked figures (ZIP)", type="primary"):
            named_pngs: list[tuple[str, bytes]] = []
            progress = st.progress(0.0)
            for i, bm in enumerate(bookmarks):
                fig_bm = _render_tad_figure(
                    clr_tad,
                    ins,
                    bm["chrom"],
                    w1=bm["w1"],
                    w2=bm["w2"],
                    region_start=bm["region_start"],
                    view_span_bp=bm["view_span_bp"],
                    plot_vmax=bm.get("vmax"),
                    balanced=balanced,
                )
                named_pngs.append((_bookmark_png_name(bm), fig_to_png_bytes(fig_bm)))
                plt.close(fig_bm)
                progress.progress((i + 1) / len(bookmarks))
            progress.empty()

            manifest = pd.DataFrame(bookmarks)
            extras = [
                ("insulation_table.csv", ins.to_csv(index=False).encode()),
                ("tad_boundaries_strong_weak.csv", bounds.to_csv(index=False).encode()),
                ("bookmarks_manifest.csv", manifest.to_csv(index=False).encode()),
            ]
            st.session_state["tad_bookmark_zip"] = zip_bytes_with_extra(named_pngs, extras)
            st.session_state["tad_bookmark_zip_name"] = f"tads_bookmarked_{tad_res}bp.zip"
            st.success(f"ZIP ready — {len(named_pngs)} bookmarked PNG(s) + tables.")

    with st.expander("Quick overview — one PNG per chromosome (optional)", expanded=False):
        st.caption(
            "Fast pass: one auto-viewport PNG per chromosome at the best-contact region. "
            "For curated figures, use bookmarks above."
        )
        if st.button("Generate overview ZIP for all chromosomes"):
            named = []
            progress = st.progress(0.0)
            for i, chrom in enumerate(tad_chroms):
                span = default_view_span_bp(w1)
                start, _ = suggest_triangle_region_start(clr_tad, chrom, span, balance=balanced)
                fig_o = _render_tad_figure(
                    clr_tad,
                    ins,
                    chrom,
                    w1=w1,
                    w2=w2,
                    region_start=start,
                    view_span_bp=span,
                    plot_vmax=None,
                    balanced=balanced,
                )
                named.append(
                    (f"overview/{chrom}_insulation_{tad_res}bp.png", fig_to_png_bytes(fig_o))
                )
                plt.close(fig_o)
                progress.progress((i + 1) / len(tad_chroms))
            progress.empty()
            extras = [
                ("insulation_table.csv", ins.to_csv(index=False).encode()),
                ("tad_boundaries_strong_weak.csv", bounds.to_csv(index=False).encode()),
            ]
            st.session_state["tad_overview_zip"] = zip_bytes_with_extra(named, extras)
            st.session_state["tad_overview_zip_name"] = f"tads_overview_{tad_res}bp.zip"
            st.success(f"{len(tad_chroms)} overview PNGs ready.")

if st.session_state.get("tad_bookmark_zip"):
    st.download_button(
        "Download bookmarked figures (ZIP)",
        data=st.session_state["tad_bookmark_zip"],
        file_name=st.session_state["tad_bookmark_zip_name"],
        mime="application/zip",
    )

if st.session_state.get("tad_overview_zip"):
    st.download_button(
        "Download overview all-chromosomes (ZIP)",
        data=st.session_state["tad_overview_zip"],
        file_name=st.session_state["tad_overview_zip_name"],
        mime="application/zip",
    )

nav_back_hub(key="tad_bottom")
