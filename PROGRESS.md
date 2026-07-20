# Project Progress — Pore-C Dashboard

Chronological record of capstone work from the original yeast analysis notebook through the current Streamlit application. Intended for instructors reviewing GitHub activity and milestone delivery.

**Last updated:** 2026-07-20 (Session 12)

---

## Project summary

**Goal:** Build a scientist-friendly dashboard that streamlines Pore-C (long-read Hi-C) analysis — from raw nanopore reads to contact maps, compartment eigenvectors, and TAD boundaries — without requiring software engineering expertise.

**Starting point:** Personal yeast (*Saccharomyces cerevisiae*) Pore-C workflow (local notebook; not in this repo) using cooler, cooltools, and bioframe.

**Current state:** **Section 2 (Analyze) is complete** for capstone milestone 1 — a working multipage Streamlit app with six analysis modules, public demo data (GSE149117 human Pore-C), reference genome downloads, and organism-aware defaults for human, mouse, and yeast. End-to-end validated on GSE149117 + hg38 (Session 12). **Section 1 (Process)** — a Nextflow wrapper for [wf-pore-c](https://github.com/epi2me-labs/wf-pore-c) — is planned but not yet implemented.

**Target users:** Specialized biologists running analyses on a laptop, desktop, or HPC cluster (port **2001**, separate from Jupyter **2000**).

---

## Milestone timeline

| Date | Session | Milestone | Status |
|------|---------|-----------|--------|
| 2026-07-17 | 1 | Project kickoff; requirements gathering; two-section architecture (Process + Analyze) | Done |
| 2026-07-17 | 2 | Reviewed yeast notebook; chose Streamlit; mapped notebook cells → app features | Done |
| 2026-07-17 | 3 | Section 2 MVP scaffold (`app.py`, `porec_dashboard/`, yeast profile, conda env) | Done |
| 2026-07-17 | 4 | Multipage UX redesign (hub + detail pages); biology help text; port 2001 | Done |
| 2026-07-17 | 5 | Safe ICE normalize (never overwrite original); batch ZIP exports; TAD dual-window plots | Done |
| 2026-07-17 | 6 | Hub card polish; 10 kb viewing defaults; simplified TAD strong/weak labeling | Done |
| 2026-07-20 | 7–8 | Public human demo (GSE149117); reference catalog; 6-card hub; balanced preview page | Done |
| 2026-07-20 | 9 | Cross-organism scientific review: chromosome filters, resolution defaults, guidance tables | Done |
| 2026-07-20 | 10 | Bug fixes: UCSC vs RefSeq FASTA naming; auto-select balanced mcool copy | Done |
| 2026-07-20 | 11 | QA pass: expanded ref catalog (hg19/mm39), chrEBV exclusion, auto-vmax preview, TAD IndexError fix | Done |
| 2026-07-20 | 12 | Clean workspace restart; GSE149117 E2E; eigenvectors chrEBV fix; TAD scrub/bookmark + dual-panel insulation | Done |
| TBD | — | Section 1: Nextflow wf-pore-c wrapper (FASTQ/BAM → mcool) | Planned |

---

## What we built (from notebook → software)

### 1. From the example notebook

The personal yeast notebook established the scientific workflow we ported into reusable Python modules (notebook kept local, not in this repo):

| Notebook analysis | Dashboard module / page |
|-------------------|-------------------------|
| ICE balancing (`cooler.balance_cooler`) | [`pages/2_Normalize.py`](pages/2_Normalize.py) + [`porec_dashboard/workspace.py`](porec_dashboard/workspace.py) |
| Log1p contact map QC (cell 5, fall colormap) | [`pages/3_Normalization_QC.py`](pages/3_Normalization_QC.py) + [`porec_dashboard/balanced_preview.py`](porec_dashboard/balanced_preview.py) |
| Genome-wide block-diagonal map | [`pages/4_Genome_wide_map.py`](pages/4_Genome_wide_map.py) + [`porec_dashboard/plots.py`](porec_dashboard/plots.py) |
| Per-chromosome triangle map | [`pages/5_Chromosome_map.py`](pages/5_Chromosome_map.py) |
| GC-phased eigenvectors (`cooltools.eigs_cis`) | [`pages/6_Eigenvectors.py`](pages/6_Eigenvectors.py) + [`porec_dashboard/eigenvectors.py`](porec_dashboard/eigenvectors.py) |
| Insulation / TAD boundaries | [`pages/7_TADs_insulation.py`](pages/7_TADs_insulation.py) + [`porec_dashboard/insulation.py`](porec_dashboard/insulation.py) |
| Custom "fall" colormap | [`porec_dashboard/colormap.py`](porec_dashboard/colormap.py) |

Notebook logic that was **intentionally deprioritized** (sparse yeast data): P(s) curves, genome-wide O/E, saddle plots — documented in planning notes, not exposed in the UI.

### 2. Application architecture

```
app.py                          # Home — Section 1 (coming soon) + Section 2 entry
pages/
  1_Section_2_Analyze.py        # Hub — 6 analysis cards (2×3 grid)
  2_Normalize.py … 7_TADs_insulation.py
porec_dashboard/                # Core library (no Streamlit in analysis logic)
  cooler_io.py                  # Open mcool, ICE balance, chromosome filtering
  catalogs.py                   # Download demo mcool + reference FASTA
  organism_guidance.py          # Per-organism settings tables for scientists
  ui_common.py                  # Sidebar, paths, navigation helpers
profiles/
  demo_datasets.yaml            # GSE149117 public Pore-C samples
  reference_genomes.yaml        # hg38, hg19, mm10, mm39, sacCer3 (UCSC naming)
  human_hg38.yaml, …            # Organism-specific resolution + exclude rules
workspace/                      # Runtime cache (gitignored): demo/, references/, normalized/
# Local-only (gitignored): personal notebook, sacCer3.fa, pairs/, planning note
```

**Tech stack:** Python 3.10, Streamlit, cooler, cooltools, bioframe, pysam, matplotlib, PyYAML.

### 3. Key design decisions

- **Two sections kept separate:** raw processing (Section 1) vs. mcool analysis (Section 2).
- **Non-destructive normalize:** ICE weights written only to `workspace/normalized/*.balanced.mcool`; original files never modified.
- **Cross-organism support:** YAML profiles drive resolution defaults, chromosome exclusions (mito, alt contigs, chrEBV, chrY for mammal compartments), and in-app guidance tables.
- **Public demo data:** [GSE149117](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149117) human Pore-C (HCC1954, ~360 MB) downloadable from the sidebar — no private data required to test.
- **Reference harmonization:** UCSC-style FASTA (`chr1`, …) required to match typical mcool naming; mismatch detection prevents silent GC phasing failures.

### 4. UX features for non-developers

- Biology-focused help blocks on every analysis page ([`porec_dashboard/help_text.py`](porec_dashboard/help_text.py))
- Organism comparison and per-page settings tables ([`porec_dashboard/organism_guidance.py`](porec_dashboard/organism_guidance.py))
- Hub cards with descriptions before entering each analysis
- Batch export: all-chromosome ZIP with progress bar for maps, eigenvectors, and TADs
- Scroll-to-top and back-to-hub navigation on detail pages

---

## Testing and validation

| Test | Result |
|------|--------|
| Yeast mcool (sacCer3, project dev data) | Used during early Section 2 development |
| GSE149117 HCC1954 + hg38 UCSC | Primary validation target; bugs found and fixed in Sessions 10–11 |
| Agent programmatic checks (Session 11) | EBV excluded; insulation at 10 kb; auto-vmax ~0.01–0.02 @ 25 kb |
| User E2E clean-slate rerun (Session 12) | Done — all 6 pages on GSE149117 + hg38; TAD plot approved |

---

## Not yet done

- **Section 1 — Process:** Nextflow wrapper for wf-pore-c (FASTQ/BAM → mcool)
- **Hub example PNGs:** Placeholder cards until user-provided figures are added
- **RNA-seq / H3K27ac phasing upload** for mammalian eigenvectors (guidance shown; upload not built)
- **Plant organism profiles**
- **ENCODE bigWig auto-fetch**

---

## Suggested Git commit milestones

If retroactively organizing GitHub pushes for instructor review, these logical chunks map to development sessions:

1. `Initial scaffold: Streamlit app, porec_dashboard package, yeast profile, requirements`
2. `Multipage UX: hub, help text, navigation, port 2001`
3. `Safe normalize + batch ZIP exports + TAD dual-window plots`
4. `Public demo catalog (GSE149117) + reference genome downloads`
5. `Organism profiles + guidance tables + scientific chromosome/resolution fixes`
6. `GSE149117 bug fixes: UCSC FASTA, balanced mcool auto-select, chrEBV exclude`
7. `QA: expanded ref catalog, auto-vmax preview, TAD view_df fix`
8. `Docs: PROGRESS.md, README progress section, conversation log updates`

> **Note:** Initial Git push (Session 12): public repo `7030_capstone_pore-c_dashboard` on branch `ai-coding`. Personal notebook, local yeast FASTA, and planning notes are gitignored.

---

## Related documentation

- [`README.md`](README.md) — Quick start and layout
- [`CONVERSATION_LOG.md`](CONVERSATION_LOG.md) — Detailed session-by-session decisions
- [`AGENT_PLAN.md`](AGENT_PLAN.md) — Compact agent recovery reference
