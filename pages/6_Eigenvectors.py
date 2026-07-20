"""Eigenvectors / compartments — single or all-chromosome ZIP."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from porec_dashboard.analysis_cache import get_cached, set_cached
from porec_dashboard.batch_export import png_zip_bytes
from porec_dashboard.cooler_io import (
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.eigenvectors import (
    compute_cis_eigenvectors,
    gc_track_from_fasta,
    make_view_df,
    plot_map_with_eigenvector,
)
from porec_dashboard.help_text import EIGENVECTORS
from porec_dashboard.organism_guidance import show_organism_guidance, show_phasing_guidance
from porec_dashboard.profiles import (
    compartment_resolution_tip,
    phasing_recommendation,
    preferred_compartment_resolution,
)
from porec_dashboard.ui_common import (
    fig_to_png_bytes,
    filtered_chromosomes,
    get_active_profile,
    get_fasta_or_warn,
    nav_back_hub,
    require_mcool,
    scroll_to_top,
    show_help_block,
)

st.set_page_config(page_title="Eigenvectors", layout="wide")
scroll_to_top()
nav_back_hub(key="eig_top")

show_help_block(EIGENVECTORS)
show_organism_guidance("eigenvectors")

mcool, exclude = require_mcool()
profile = get_active_profile()
fasta = get_fasta_or_warn()
resolutions = list_resolutions(mcool)

st.info(compartment_resolution_tip(profile))
show_phasing_guidance()
st.caption(phasing_recommendation(profile))

default_res = preferred_compartment_resolution(resolutions, profile)
resolution = st.selectbox(
    "Compartment calling resolution (bp)",
    resolutions,
    index=resolutions.index(default_res),
    help="Resolution passed to cooltools.eigs_cis — coarser than chromosome map viewing.",
)
clr = open_cooler(mcool, resolution)
chroms = filtered_chromosomes(clr, exclude, purpose="compartment")

method = st.radio(
    "Phasing / expected signal",
    options=["GC from FASTA", "Upload track (chrom, start, end, value)"],
    horizontal=True,
)
uploaded = None
if method.startswith("Upload"):
    uploaded = st.file_uploader("Track file (TSV/CSV)", type=["tsv", "csv", "txt", "bed"])
else:
    if fasta:
        st.success(f"Using FASTA: `{fasta}`")
    else:
        st.warning("Select a reference genome in the sidebar (hg38, sacCer3, mm10, or local FASTA) for GC phasing.")

mode = st.radio(
    "Output",
    options=["One chromosome", "All chromosomes (ZIP)"],
    horizontal=True,
    key="eig_mode",
)
eig_chrom = st.selectbox("Chromosome to display / preview", chroms)
st.caption(f"Compartment analysis uses **{len(chroms)}** chromosomes (profile-filtered).")

if not has_weights(clr):
    st.warning("This resolution is not balanced yet. Open **Normalize** first for best results.")


def _load_track():
    if method.startswith("GC"):
        if not fasta:
            st.error("Provide a valid reference FASTA in the sidebar.")
            st.stop()
        track_key = ("gc", fasta, resolution, tuple(chroms))
        cached = get_cached("eig_track", mcool, track_key)
        if cached is not None:
            return cached
        with st.spinner("Computing GC track…"):
            track = gc_track_from_fasta(clr, fasta, chromosomes=chroms)
        set_cached("eig_track", track, mcool, track_key)
        return track
    if uploaded is None:
        st.error("Upload a track file first.")
        st.stop()
    raw = pd.read_csv(uploaded, sep=None, engine="python")
    raw.columns = [c.lower() for c in raw.columns]
    if "gc" in raw.columns:
        raw = raw.rename(columns={"gc": "GC"})
    elif "value" in raw.columns:
        raw = raw.rename(columns={"value": "GC"})
    elif "score" in raw.columns:
        raw = raw.rename(columns={"score": "GC"})
    else:
        st.error("Track needs a GC, value, or score column.")
        st.stop()
    return raw


if st.button("Compute eigenvectors", type="primary"):
    try:
        track = _load_track()
        view = make_view_df(clr, chroms)
        cache_parts = (mcool, resolution, tuple(chroms), method, uploaded.name if uploaded else "gc")
        eig_df = get_cached("eig_df", *cache_parts)
        if eig_df is None:
            with st.spinner("Running cooltools.eigs_cis…"):
                _, eig_df = compute_cis_eigenvectors(clr, track, view_df=view, n_eigs=3)
            set_cached("eig_df", eig_df, *cache_parts)
        else:
            st.info("Using cached eigenvector result for this mcool, resolution, and phasing track.")
        st.session_state["eig_df"] = eig_df
        st.success("Eigenvectors computed.")
        st.download_button(
            "Download eigenvector table (CSV)",
            eig_df.to_csv(index=False).encode(),
            "eigenvectors.csv",
            "text/csv",
        )

        if mode.startswith("One"):
            fig = plot_map_with_eigenvector(clr, eig_df, eig_chrom, balance=has_weights(clr))
            st.pyplot(fig)
            st.download_button(
                "Download map+E1 PNG",
                data=fig_to_png_bytes(fig),
                file_name=f"{eig_chrom}_E1_{resolution}bp.png",
                mime="image/png",
            )
            plt.close(fig)
        else:
            named = []
            preview_fig = None
            progress = st.progress(0.0)
            status = st.empty()
            for i, chrom in enumerate(chroms):
                status.write(f"Plotting {chrom} ({i + 1}/{len(chroms)})…")
                fig = plot_map_with_eigenvector(
                    clr, eig_df, chrom, balance=has_weights(clr)
                )
                named.append((f"{chrom}_E1_{resolution}bp.png", fig_to_png_bytes(fig)))
                if preview_fig is None:
                    preview_fig = fig
                else:
                    plt.close(fig)
                progress.progress((i + 1) / len(chroms))
            status.empty()
            progress.empty()
            st.session_state["eig_zip"] = png_zip_bytes(named)
            st.session_state["eig_zip_name"] = f"eigenvectors_{resolution}bp.zip"
            st.session_state["eig_preview"] = preview_fig
            st.session_state["eig_count"] = len(named)
            st.success(f"{len(named)} figures ready.")
    except Exception as exc:  # noqa: BLE001
        st.exception(exc)

if st.session_state.get("eig_zip"):
    st.markdown("#### Preview (first chromosome)")
    st.pyplot(st.session_state["eig_preview"])
    st.caption(f"{st.session_state['eig_count']} PNGs in ZIP.")
    st.download_button(
        "Download all map+E1 (ZIP)",
        data=st.session_state["eig_zip"],
        file_name=st.session_state["eig_zip_name"],
        mime="application/zip",
    )

if "eig_df" in st.session_state:
    st.dataframe(st.session_state["eig_df"].head(50), hide_index=True)

nav_back_hub(key="eig_bottom")
