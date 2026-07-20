"""Normalize (ICE balancing) — writes to workspace copy only."""

from __future__ import annotations

import streamlit as st

from porec_dashboard.cooler_io import (
    balance_cooler,
    chromsizes_table,
    has_weights,
    list_resolutions,
    open_cooler,
)
from porec_dashboard.help_text import NORMALIZE
from porec_dashboard.organism_guidance import show_organism_guidance
from porec_dashboard.profiles import normalize_resolution_defaults
from porec_dashboard.ui_common import get_active_profile, nav_back_hub, require_mcool, scroll_to_top, show_help_block
from porec_dashboard.workspace import ensure_working_mcool, is_under_normalized

st.set_page_config(page_title="Normalize", layout="wide")
scroll_to_top()
nav_back_hub(key="norm_top")

show_help_block(NORMALIZE)
show_organism_guidance("normalize")

mcool_src, _exclude = require_mcool()
st.info(
    "ICE weights are written only to a **working copy** under "
    "`workspace/normalized/`. Your original `.mcool` is never modified."
)

resolutions = list_resolutions(mcool_src)
profile = get_active_profile()
default_res = 25000 if 25000 in resolutions else resolutions[len(resolutions) // 2]
resolution = st.selectbox(
    "Primary resolution to inspect",
    options=resolutions,
    index=resolutions.index(default_res),
)
clr = open_cooler(mcool_src, resolution)

c1, c2 = st.columns(2)
with c1:
    st.metric("Current resolution", f"{resolution:,} bp")
    st.metric("Already balanced?", "Yes" if has_weights(clr) else "No")
    if is_under_normalized(mcool_src):
        st.caption(f"Active file is already a working copy: `{mcool_src}`")
with c2:
    st.dataframe(chromsizes_table(clr), hide_index=True, height=240)

multi = st.multiselect(
    "Resolutions to balance",
    options=resolutions,
    default=normalize_resolution_defaults(resolutions, profile),
    help="Common choices: 1, 5, 10, and 25 kb (depends on mcool contents).",
)

if st.button("Run ICE balancing", type="primary"):
    with st.spinner("Creating / locating working copy (original untouched)…"):
        work = ensure_working_mcool(mcool_src)
    st.session_state["mcool_path"] = str(work)
    st.success(f"Working file: `{work}`")

    targets = sorted(set(multi) | {resolution})
    progress = st.progress(0.0)
    for i, res in enumerate(targets):
        c = open_cooler(str(work), res)
        if has_weights(c):
            st.write(f"{res} bp — already has weights, skipping")
        else:
            with st.spinner(f"Balancing {res} bp on working copy…"):
                balance_cooler(c, store=True)
            st.success(f"{res} bp — balanced")
        progress.progress((i + 1) / len(targets))
    st.success(
        "Done. Other analysis pages will use this working copy. "
        "Original input file was not modified."
    )

nav_back_hub(key="norm_bottom")
