"""Chromosome / region contact map page — single or all-chromosome ZIP."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from porec_dashboard.batch_export import png_zip_bytes
from porec_dashboard.cooler_io import (
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.help_text import CHROMOSOME
from porec_dashboard.organism_guidance import show_organism_guidance
from porec_dashboard.plots import plot_chromosome_map
from porec_dashboard.profiles import vmax_hint
from porec_dashboard.ui_common import (
    fig_to_png_bytes,
    filtered_chromosomes,
    get_active_profile,
    nav_back_hub,
    preferred_view_resolution,
    require_mcool,
    scroll_to_top,
    show_help_block,
    show_view_resolution_tip,
)

st.set_page_config(page_title="Chromosome map", layout="wide")
scroll_to_top()
nav_back_hub(key="chr_top")

show_help_block(CHROMOSOME)
show_organism_guidance("chromosome")

mcool, exclude = require_mcool()
resolutions = list_resolutions(mcool)
show_view_resolution_tip()
default_res = preferred_view_resolution(resolutions)
resolution = st.selectbox("Resolution (bp)", resolutions, index=resolutions.index(default_res))
clr = open_cooler(mcool, resolution)
chroms = filtered_chromosomes(clr, exclude, purpose="general")

mode = st.radio(
    "Generate",
    options=["One chromosome", "All chromosomes"],
    horizontal=True,
)

st.markdown("#### Color scale (`vmax`)")
st.info(
    "**vmax** is the upper color limit on the log heatmap — it only changes display, not data. "
    f"{vmax_hint(get_active_profile())} "
    "For **All chromosomes**, one shared vmax is used so maps are comparable."
)
vmax = st.number_input(
    "vmax (shared for batch)",
    value=0.1,
    min_value=0.0001,
    format="%.4f",
    help="Same vmax applied to every chromosome in batch mode.",
)

if not has_weights(clr):
    st.warning("This resolution is not balanced yet. Open **Normalize** first for best results.")

if mode == "One chromosome":
    chrom = st.selectbox("Chromosome", chroms)
    use_region = st.checkbox("Limit to a genomic region", value=False)
    start, end = None, None
    if use_region:
        c1, c2 = st.columns(2)
        start = c1.number_input("Start", min_value=0, value=0, step=1000)
        end = c2.number_input(
            "End",
            min_value=1,
            value=min(int(clr.chromsizes[chrom]), 500_000),
            step=1000,
        )
    if st.button("Generate chromosome map", type="primary"):
        with st.spinner("Plotting…"):
            fig = plot_chromosome_map(
                clr,
                chrom,
                start=start,
                end=end,
                balance=has_weights(clr),
                vmax=float(vmax),
            )
        st.pyplot(fig)
        st.download_button(
            "Download PNG",
            data=fig_to_png_bytes(fig),
            file_name=f"{chrom}_{resolution}bp.png",
            mime="image/png",
        )
        plt.close(fig)
else:
    st.caption(f"Will generate **{len(chroms)}** maps with vmax={vmax}.")
    if st.button("Generate all chromosome maps", type="primary"):
        named = []
        preview_fig = None
        progress = st.progress(0.0)
        status = st.empty()
        for i, chrom in enumerate(chroms):
            status.write(f"Plotting {chrom} ({i + 1}/{len(chroms)})…")
            fig = plot_chromosome_map(
                clr,
                chrom,
                balance=has_weights(clr),
                vmax=float(vmax),
            )
            named.append((f"{chrom}_{resolution}bp.png", fig_to_png_bytes(fig)))
            if preview_fig is None:
                preview_fig = fig
            else:
                plt.close(fig)
            progress.progress((i + 1) / len(chroms))
        status.empty()
        progress.empty()
        st.session_state["chr_zip"] = png_zip_bytes(named)
        st.session_state["chr_zip_name"] = f"chr_maps_{resolution}bp.zip"
        st.session_state["chr_preview"] = preview_fig
        st.session_state["chr_count"] = len(named)
        st.success(f"{len(named)} figures ready.")

    if st.session_state.get("chr_zip"):
        st.markdown("#### Preview (first chromosome)")
        st.pyplot(st.session_state["chr_preview"])
        st.caption(f"{st.session_state['chr_count']} PNGs in ZIP (shared vmax={vmax}).")
        st.download_button(
            "Download all (ZIP)",
            data=st.session_state["chr_zip"],
            file_name=st.session_state["chr_zip_name"],
            mime="application/zip",
        )

nav_back_hub(key="chr_bottom")
