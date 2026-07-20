"""Section 2 hub — six boxed, centered analysis cards with examples."""

from __future__ import annotations

import streamlit as st

from porec_dashboard.help_text import SECTION2_CARDS
from porec_dashboard.organism_guidance import COMPARISON_TABLE, active_row_hint
from porec_dashboard.paths import example_image_path
from porec_dashboard.ui_common import analysis_card_html, get_active_profile, render_data_sidebar, scroll_to_top

st.set_page_config(page_title="Section 2 — Analyze", layout="wide")
scroll_to_top()

st.title("Section 2 — Analyze")
st.caption(
    "Import a processed `.mcool`, then pick an analysis. "
    "Each card shows what the analysis does biologically and an example figure."
)

render_data_sidebar()

profile = get_active_profile()
st.markdown(active_row_hint(profile))
with st.expander("Cross-organism settings guide (yeast vs human vs mouse)", expanded=False):
    st.markdown(COMPARISON_TABLE)
    st.caption(
        "Each analysis page also has a page-specific table. "
        "Select a demo dataset or reference genome in the sidebar to apply defaults."
    )

if st.button("← Back to Home"):
    st.switch_page("app.py")

st.markdown("---")

ROUTES = {
    "Normalize (ICE balancing)": "pages/2_Normalize.py",
    "Balanced normalization preview": "pages/3_Normalization_QC.py",
    "Genome-wide contact map": "pages/4_Genome_wide_map.py",
    "Chromosome / region contact map": "pages/5_Chromosome_map.py",
    "Eigenvectors / compartments": "pages/6_Eigenvectors.py",
    "TADs / insulation": "pages/7_TADs_insulation.py",
}

# Six cards in two rows of three — equal card widths, centered buttons.
for row_cards in (SECTION2_CARDS[:3], SECTION2_CARDS[3:]):
    cols = st.columns(3, gap="medium")
    for col, meta in zip(cols, row_cards):
        with col:
            try:
                card = st.container(border=True)
            except TypeError:
                card = st.container()
            with card:
                st.markdown(
                    analysis_card_html(
                        meta["title"], meta["blurb"], meta["example_caption"]
                    ),
                    unsafe_allow_html=True,
                )
                path = example_image_path(meta["example_stem"])
                if path is not None:
                    img_l, img_m, img_r = st.columns([0.08, 0.84, 0.08])
                    with img_m:
                        st.image(str(path))
                else:
                    # Placeholder keeps card heights similar when example PNGs are absent.
                    st.markdown(
                        "<div style='min-height:4.5rem;'></div>",
                        unsafe_allow_html=True,
                    )
                route = ROUTES.get(meta["title"])
                btn_l, btn_m, btn_r = st.columns([0.12, 0.76, 0.12])
                with btn_m:
                    if route and st.button(
                        f"Open: {meta['title']}",
                        key=f"open_{meta['example_stem']}",
                        use_container_width=True,
                    ):
                        st.switch_page(route)
