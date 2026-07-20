"""Balanced normalization preview — single-chromosome log1p contact map."""

from __future__ import annotations

import streamlit as st

from porec_dashboard.balanced_preview import (
    plot_balanced_normalization_preview,
    suggest_vmax,
)
from porec_dashboard.cooler_io import (
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.help_text import BALANCED_PREVIEW
from porec_dashboard.organism_guidance import show_organism_guidance
from porec_dashboard.profiles import (
    preview_chromosome_default,
    preview_resolution_default,
)
from porec_dashboard.ui_common import (
    fig_to_png_bytes,
    filtered_chromosomes,
    get_active_profile,
    nav_back_hub,
    require_mcool,
    scroll_to_top,
    show_help_block,
)

st.set_page_config(page_title="Balanced normalization preview", layout="wide")
scroll_to_top()
nav_back_hub(key="bprev_top")

show_help_block(BALANCED_PREVIEW)
show_organism_guidance("balanced_preview")

mcool, exclude = require_mcool()
profile = get_active_profile()
resolutions = list_resolutions(mcool)
default_res = preview_resolution_default(resolutions, profile)
resolution = st.selectbox(
    "Resolution (bp)",
    resolutions,
    index=resolutions.index(default_res),
    help="Notebook default: 25 kb. Coarse bins (100–250 kb) need auto-scaling — structure is harder to see.",
)
if resolution >= 100_000:
    st.info(
        "At **100 kb+**, balanced contact values are very small on a log1p scale. "
        "Enable **Auto-scale color** below (recommended). For visual QC, **25 kb** works best."
    )

clr = open_cooler(mcool, resolution)
chroms = filtered_chromosomes(clr, exclude, purpose="general")
default_chrom = preview_chromosome_default(chroms, profile)
chrom = st.selectbox(
    "Chromosome",
    chroms,
    index=chroms.index(default_chrom) if default_chrom in chroms else 0,
)

use_balance = has_weights(clr)
if use_balance:
    suggested, p95, p98 = suggest_vmax(clr, chrom, balance=True)
    st.caption(
        f"Suggested vmax from data: **{suggested:.4f}** "
        f"(log1p p95={p95:.4f}, p98={p98:.4f} on non-zero bins)."
    )
else:
    suggested = 2.0
    p95, p98 = 0.0, 0.0

auto_scale = st.checkbox("Auto-scale color (recommended)", value=True)
if auto_scale and use_balance:
    vmax = suggested
    st.caption(f"Using auto vmax = **{vmax:.4f}**")
else:
    vmax = st.slider(
        "log1p color scale max (vmax)",
        min_value=0.001,
        max_value=2.0,
        value=float(min(suggested, 2.0)) if use_balance else 2.0,
        step=0.001,
        format="%.3f",
    )

if not has_weights(clr):
    st.warning(
        "This resolution is not balanced yet. Run **Normalize (ICE balancing)** first, "
        "then return here to preview the balanced contact map."
    )

if st.button("Generate balanced normalization preview", type="primary"):
    if not use_balance:
        st.error(
            "This resolution has no ICE weights. Open **Normalize**, run balancing, "
            "then return here. The app will automatically use the `.balanced.mcool` "
            "working copy under workspace/normalized/."
        )
        st.stop()
    plot_vmax = suggest_vmax(clr, chrom, balance=True)[0] if auto_scale else vmax
    fig = plot_balanced_normalization_preview(clr, chrom, vmax=plot_vmax, balance=True)
    st.pyplot(fig, clear_figure=True)
    st.download_button(
        "Download PNG",
        data=fig_to_png_bytes(fig),
        file_name=f"balanced_preview_{chrom}_{resolution}bp.png",
        mime="image/png",
    )

nav_back_hub(key="bprev_bottom")
