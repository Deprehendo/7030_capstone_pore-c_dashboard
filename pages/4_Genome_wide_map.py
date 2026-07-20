"""Genome-wide contact map page."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from porec_dashboard.cooler_io import (
    estimate_genome_bins,
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.help_text import GENOME_WIDE
from porec_dashboard.organism_guidance import show_organism_guidance
from porec_dashboard.plots import plot_genome_wide
from porec_dashboard.profiles import (
    genome_wide_max_bins,
    genome_wide_min_resolution,
    genome_wide_resolution_default,
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

st.set_page_config(page_title="Genome-wide map", layout="wide")
scroll_to_top()
nav_back_hub(key="gw_top")

show_help_block(GENOME_WIDE)
show_organism_guidance("genome_wide")

mcool, exclude = require_mcool()
profile = get_active_profile()
resolutions = list_resolutions(mcool)
default_res = genome_wide_resolution_default(resolutions, profile)
resolution = st.selectbox("Resolution (bp)", resolutions, index=resolutions.index(default_res))
clr = open_cooler(mcool, resolution)
chroms = filtered_chromosomes(clr, exclude, purpose="genome_wide")
n_bins = estimate_genome_bins(clr, chroms)
max_bins = genome_wide_max_bins(profile)
min_res = genome_wide_min_resolution(profile)

st.caption(f"**{len(chroms)}** chromosomes · **~{n_bins:,}** bins at this resolution")

if min_res and resolution < min_res:
    st.error(
        f"Resolution **{resolution:,} bp** is below the recommended minimum "
        f"**{min_res:,} bp** for {profile.get('display_name', 'this organism')}. "
        "Choose a coarser resolution or use the Chromosome map page for fine detail."
    )
elif n_bins > max_bins:
    st.warning(
        f"**~{n_bins:,} bins** exceeds the recommended limit (~{max_bins:,}) for a genome-wide "
        "dense matrix. Consider **100 kb** or coarser, or plot individual chromosomes instead."
    )

if not has_weights(clr):
    st.warning("This resolution is not balanced yet. Open **Normalize** first for best results.")

if st.button("Generate genome-wide map", type="primary", disabled=bool(min_res and resolution < min_res)):
    with st.spinner("Building genome matrix…"):
        fig = plot_genome_wide(clr, chromosomes=chroms, balance=has_weights(clr))
    st.pyplot(fig)
    st.download_button(
        "Download PNG",
        data=fig_to_png_bytes(fig),
        file_name=f"genome_wide_{resolution}bp.png",
        mime="image/png",
    )
    plt.close(fig)

nav_back_hub(key="gw_bottom")
