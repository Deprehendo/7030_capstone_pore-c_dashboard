"""Organism-aware parameter tables and guidance copy for Section 2."""

from __future__ import annotations

import streamlit as st

# Cross-organism reference (shown when no profile or in expander)
COMPARISON_TABLE = """
| Analysis step | Yeast (sacCer3) | Human / mouse (hg38, mm10) | Why it differs |
|---------------|-----------------|----------------------------|----------------|
| **ICE balancing** | 1–25 kb typical | 1–25 kb typical | Same method; depth sets usable resolutions |
| **Balanced preview** | 25 kb, e.g. chrVII | 25 kb, e.g. chr21 | Visual QC only — log1p map, not literature metric |
| **Genome-wide map** | 25 kb OK (small genome) | **≥ 50–100 kb** recommended | Bin count scales with genome size; dense matrices get slow |
| **Chromosome map** | ~10 kb when depth allows | ~10 kb when depth allows | Finer bins for local structure |
| **Compartment calling (eigs)** | **25 kb** common | **100 kb** common (25–100 kb range) | A/B signal is coarse; mammalian papers use 100 kb–1 Mb |
| **TAD / insulation** | 10 kb bins; 100 / 250 kb windows | 10 kb bins; 100 / 250 kb windows | Same cooltools windows; depth matters more in yeast |
| **Phasing track** | **GC** from FASTA works well | Prefer **RNA-seq**, H3K27ac, or DNase; GC is fallback | GC–compartment link is weaker in mammals |
| **Chromosomes used** | All nuclear contigs | Autosomes (+ chrX); drop alt/random, chrM, **chrEBV** | GSE149117 EBV spike-in excluded |
"""

PAGE_TABLES: dict[str, str] = {
    "normalize": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| Resolutions to balance | 1, 5, 10, 25 kb | 1, 5, 10, 25 kb (100 kb optional) |
| When to skip | Weights already in file | GSE149117 may ship pre-balanced — safe to skip |
""",
    "balanced_preview": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| Default resolution | 25 kb | 25 kb |
| Default chromosome | chrVII, chrIV | chr21, chr22, chr1 |
| Color scale | log1p(contacts), vmax=2 | Same — **not** the same scale as other pages |
| Note | Other pages use log **balanced frequencies** | Do not compare vmax directly across pages |
""",
    "genome_wide": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| Recommended resolution | 25 kb | **100 kb** (min ~50 kb) |
| Chromosomes | Nuclear only | Autosomes; alt/random/unplaced excluded |
| Risk if too fine | Moderate memory | Very slow / may fail — millions of bins |
""",
    "chromosome": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| View resolution | ~10 kb when available | ~10 kb when available |
| vmax starting point | 0.05–0.2 (try 0.1) | 0.02–0.1 (human often lower) |
| Batch mode | One shared vmax | One shared vmax |
""",
    "eigenvectors": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| **Calling resolution (eigs_cis)** | **25 kb** | **100 kb** (literature: 100 kb–1 Mb) |
| Map viewing | Same resolution as calling on this page | Same — use **Chromosome map** for finer bins |
| Phasing track | GC from FASTA | Upload RNA-seq / H3K27ac preferred; GC fallback |
| Chromosomes in view | All nuclear | Autosomes (+ chrX); chrY often excluded |
""",
    "tads": """
| Setting | Yeast | Human / mouse |
|---------|-------|---------------|
| Insulation resolution | 10 kb | 10 kb |
| Window 1 (strong) | 10× binsize (100 kb) | 10× binsize (100 kb) |
| Window 2 (weak) | 25× binsize (250 kb) | 25× binsize (250 kb) |
| Boundary labels | UI simplification — both are standard cooltools calls | Same |
""",
}

PHASING_TABLE = """
| Organism | Recommended phasing | GC from FASTA | Notes |
|----------|---------------------|---------------|-------|
| **Yeast (sacCer3)** | GC | Good default | Matches project notebook; weak but usable axis |
| **Human (hg38)** | RNA-seq, H3K27ac, DNase | Fallback only | ENCODE / literature favor functional tracks |
| **Mouse (mm10)** | RNA-seq, H3K27ac | Fallback only | Same as human mammalian practice |
"""


def profile_label(profile: dict | None) -> str:
    if not profile:
        return "Generic (no reference selected)"
    return profile.get("display_name") or profile.get("organism", "Unknown")


def active_row_hint(profile: dict | None) -> str:
    """One-line summary for the active profile."""
    if not profile:
        return "Select a reference genome or demo dataset in the sidebar for organism-specific defaults."
    org = profile.get("organism", "")
    comp = profile.get("compartment", {})
    call = comp.get("call_resolution_bp") or comp.get("preferred_resolution_bp")
    view = comp.get("view_resolution_bp", 10_000)
    tad = profile.get("tad", {}).get("preferred_resolution_bp", 10_000)
    gw_min = profile.get("ui", {}).get("genome_wide_min_resolution_bp")
    gw_part = f"genome-wide ≥ {gw_min // 1000} kb" if gw_min else "genome-wide per profile"
    return (
        f"**{profile_label(profile)}** — compartment calling **{call // 1000 if call else '?'} kb**, "
        f"chromosome/TAD view **{view // 1000} kb**, {gw_part}."
    )


def show_organism_guidance(page_key: str, *, profile: dict | None = None) -> None:
    """Show active-organism summary and page-specific parameter table."""
    if profile is None:
        from porec_dashboard.ui_common import get_active_profile

        profile = get_active_profile()

    st.markdown(active_row_hint(profile))
    page_table = PAGE_TABLES.get(page_key, "")
    if page_table:
        with st.expander("Recommended settings by organism", expanded=False):
            st.markdown(page_table)
            st.caption("Rows reflect common Pore-C / Hi-C practice (Open2C, Rao 2014, GSE149117).")
    with st.expander("Full cross-organism comparison", expanded=False):
        st.markdown(COMPARISON_TABLE)


def show_phasing_guidance() -> None:
    st.markdown("#### Phasing track guidance")
    st.markdown(PHASING_TABLE)
