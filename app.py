"""Pore-C Dashboard — Home (two section cards)."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Pore-C Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Pore-C Dashboard")
st.caption(
    "A guided workspace for Pore-C: process raw reads into contact matrices, "
    "then explore maps, compartments, and TAD boundaries — built for scientists, "
    "not software engineers."
)

st.markdown("### Choose a section")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(
        """
        <div style="border:2px solid #bbb; border-radius:12px; padding:1.4rem 1.2rem;
                    min-height:280px; background:linear-gradient(160deg,#f7f7f7,#ebebeb);">
          <h2 style="margin-top:0;">Section 1 — Process</h2>
          <p><b>FASTQ / BAM → .mcool</b></p>
          <p>Run the Pore-C processing pipeline (wf-pore-c style): digest, align,
          and build multi-resolution contact matrices for downstream analysis.</p>
          <p style="color:#666;"><i>Coming soon — not available in this build.</i></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("Open Section 1", disabled=True, use_container_width=True)

with col2:
    st.markdown(
        """
        <div style="border:2px solid #2c6e49; border-radius:12px; padding:1.4rem 1.2rem;
                    min-height:280px; background:linear-gradient(160deg,#f0faf4,#d8eee0);">
          <h2 style="margin-top:0;">Section 2 — Analyze</h2>
          <p><b>Import .mcool → maps, eigenvectors, TADs</b></p>
          <p>Normalize contacts, plot genome-wide and chromosome maps, call compartment
          eigenvectors, and find insulation / TAD boundaries — with biology-focused help
          on every page.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Section 2", type="primary", use_container_width=True):
        st.switch_page("pages/1_Section_2_Analyze.py")

st.divider()
st.markdown(
    """
    **How to run this app** (use a port that is **not** your Jupyter port):

    ```bash
    streamlit run app.py --server.port 2001 --server.address 0.0.0.0
    ```

    Tip: use a public demo mcool from [GSE149117](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149117) (GRCh38)
    or place your own `.mcool` in the project folder — Analyze pages auto-detect local files.
    Reference genomes (hg38, sacCer3, mm10) are cataloged in `profiles/reference_genomes.yaml`.
    """
)
