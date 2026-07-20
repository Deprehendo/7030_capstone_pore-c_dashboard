# Capstone Project — Conversation Log

Running log of project discussions. Newest entries at the top.

---

## 2026-07-20 — Session 12: Clean workspace + fresh E2E restart

**User:** File issues with cached data; requested clean slate before E2E validation.

**Action:**
- Wiped **`workspace/`** only (~5.6 GB): demo mcool, normalized balanced copies (GSE149117 + yeast `combined_pass.balanced.mcool`), all reference FASTAs (UCSC hg38 + stale RefSeq `.gz`).
- **Kept:** project-root `sacCer3.fa`, `pairs/`, `workspace/normalized/README.md`.

**Next (user):**
1. Restart Streamlit (clear stale session paths).
2. Sidebar: re-download **GSE149117 HCC1954** demo mcool (~360 MB) → **hg38** UCSC reference (~950 MB gz).
3. Run full Section 2 E2E from **Normalize** (ICE from scratch) through TADs.

**Docs:** Added [`PROGRESS.md`](PROGRESS.md) + README progress section for instructor / GitHub milestone review.

**Bug fixes (E2E):**
- **Eigenvectors chrEBV:** GC phasing uses profile-filtered chromosomes; categorical chrom cast to strings before `frac_gc`.
- **TAD UX overhaul:** Scrub + bookmark workflow; dual-panel insulation (viewport detail + full-chrom overview strip); PuOr triangle.

**Completed:**
- User approved TAD dual-panel plot ("looks good").
- Full E2E on GSE149117 + hg38 UCSC validated across all 6 analysis pages.
- Git init: public repo **`7030_capstone_pore-c_dashboard`**, branch **`ai-coding`**. Excluded from repo: `Pore_C_wt_analysis.ipynb`, `sacCer3.fa`, `note`, `pairs/`, `workspace/`.

---

## 2026-07-20 — Session 11: GSE149117 QA fixes (catalog, EBV, preview scale, TADs)

**User:** Implement QA plan — expand refs, fix balanced preview visibility, exclude chrEBV, fix TADs IndexError.

**Implemented:**
- Reference catalog: **hg38, hg19, mm10, mm39** (UCSC) + sacCer3; parenthetical `display_name`; profiles for hg19/mm39.
- **chrEBV** / `*EBV*` excluded from all analyses (default + human/mouse profiles).
- Balanced preview: **auto-vmax** from log1p percentiles; slider min 0.001; resolution guidance for 100/250 kb.
- TADs: `compute_insulation(..., chromosomes=...)` with min-length filter + `view_df`; no IndexError on GSE149117.

**Validated on HCC1954 balanced mcool:** EBV absent from compartment list; insulation runs at 10 kb.

---

## 2026-07-20 — Session 10: GSE149117 HCC1954 errors — FASTA naming + balancing

**User errors on GSE149117 HCC1954:**
1. Eigenvectors: `chrom from intervals not in fasta_records`
2. Balanced preview: `No column 'bins/weight'`
3. TADs: `cooler is not balanced`

**Root causes (verified on cached files):**
| Issue | Cause |
|-------|--------|
| Eigenvectors / GC | mcool uses **UCSC** names (`chr1`, …); cached hg38 FASTA was **NCBI RefSeq** (`NC_000001.11`, …) |
| Balanced preview / TADs | Demo mcool has **no ICE weights**; sidebar was resetting to unbalanced `workspace/demo/` file even after Normalize created `workspace/normalized/*.balanced.mcool` |

**Fixes implemented:**
- Reference catalog → **UCSC** hg38/mm10/sacCer3 FASTA URLs (`hg38.ucsc.fa`, etc.)
- `genome_harmonize.py` — detect naming mismatch; sidebar error when RefSeq FASTA + UCSC mcool
- `prefer_balanced_mcool()` — auto-use `.balanced.mcool` when it exists
- Clear errors on balanced preview / TADs when weights missing
- Help text: GSE149117 ships without pre-computed weights

**User action required:**
1. Delete old `workspace/references/hg38.primary_assembly.fa*` and re-download **hg38** from sidebar (~950 MB UCSC)
2. Confirm sidebar shows **balanced working copy** after Normalize
3. Re-run eigenvectors @ 100 kb, balanced preview @ 25 kb, TADs @ 10 kb

---

## 2026-07-20 — Session 9: Plan 2 — cross-organism scientific fixes + guidance tables

**User:** Execute Scientific Code Review plan (Plan 2); add helpful organism-aware guidance tables throughout Section 2.

**Implemented:**
- **Chromosome filtering:** profile-driven excludes in `cooler_io.py` (mito, alt/random patterns, chrY for compartment calling on mammals).
- **Resolution split:** `preferred_compartment_resolution()` — human/mouse **100 kb** eigs default; yeast **25 kb**; chromosome/TAD viewing stays **10 kb**.
- **bioframe.make_viewframe** for `eigs_cis` view frames.
- **Genome-wide guardrails:** min resolution + bin-count warnings on genome-wide page.
- **Session cache** for eigenvectors and insulation results (`analysis_cache.py`).
- **Organism guidance:** `organism_guidance.py` with cross-organism comparison table + per-page settings tables; shown on all Section 2 detail pages.
- **Phasing guidance table** on Eigenvectors page (GC for yeast; RNA-seq/H3K27ac for mammals).
- **Profile YAML updates:** explicit `call_resolution_bp`, `exclude_patterns`, `genome_wide_min_resolution_bp`, phasing notes.

**User to validate:**
- GSE149117 flow with hg38 profile: eigs @ 100 kb, insulation @ 10 kb, genome-wide @ 100 kb.
- Confirm filtered chromosome list matches mcool contig names.

**Deferred:** ENCODE bigWig auto-fetch; plant profiles.

---

## 2026-07-20 — Session 8: Plan executed — balanced preview, GSE149117 sidebar, reference catalog

**User:** Execute Section 2 polish plan; update conversation log.

**Corrections applied:**
- 6th hub card is **Balanced normalization preview** (notebook cell 5: log1p + fall + vmax 2), **not** P(s) curves.
- Removed `normalization_qc.py`; added `balanced_preview.py`.

**Implemented:**
- Sidebar **Demo mcool** download (GSE149117 entries from `profiles/demo_datasets.yaml` → `workspace/demo/`).
- Sidebar **Reference catalog** download (**hg38**, **sacCer3**, **mm10** → `workspace/references/`).
- `porec_dashboard/catalogs.py`, `profiles.py`; `profiles/mouse_mm10.yaml`.
- Organism-aware defaults/tips via session profile (human_hg38, yeast_sacCer3, mouse_mm10).
- Organism-neutral help text across pages; README + AGENT_PLAN updated.

**User to validate:**
- Download GSE149117 HCC1954 mcool + hg38 on laptop/HPC.
- Full flow: Normalize → Balanced preview → genome-wide → chr map → eigenvectors → TADs.

**Deferred:** Hub example PNGs.

---

## 2026-07-20 — Session 7: Section 2 polish plan — 6 cards, GSE149117, reference catalog

**User goals:**
- Fix hub layout (Eigenvectors / TADs buttons not centered with card boundaries).
- Add **6th hub card**: normalization QC plot from `Pore_C_wt_analysis.ipynb` — balanced P(s) vs distance; place **between Normalize and Genome-wide**.
- Move demo toward **public human Pore-C** ([GSE149117](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149117)), not private yeast mcool.
- Reference genomes: explicit catalog — **hg38**, **sacCer3**, **mm10** (common mouse); download when needed.
- Keep UX/copy **broad** for any user (sacCer3 was dev example only).
- Hub example images: **blank for now**; add later.
- Keep decisions in conversation files.

**User decisions (confirmed):**
1. Demo mcool series: **GSE149117** (GRCh38; e.g. GSM4490690 HCC1954 ~360 MB as starter).
2. Reference FASTA catalog: hg38, sacCer3, mm10 — named explicitly in UI when built.
3. Yeast stays as optional catalog entry; default narrative is organism-neutral + public human data.
4. Example PNGs deferred.

**Implemented this session:**
- **6-card hub** in fixed **2×3 grid**; `use_container_width` on Open buttons; min-height placeholder when no example PNG.
- New **`Normalization QC (P(s) curves)`** page (`pages/3_Normalization_QC.py`) — ports notebook `cooltools.expected_cis` + `balanced.avg.smoothed` log-log plot (`porec_dashboard/normalization_qc.py`).
- Renumbered detail pages: genome-wide → `4_`, chromosome → `5_`, eigenvectors → `6_`, TADs → `7_`.
- Catalog YAML: `profiles/reference_genomes.yaml`, `profiles/demo_datasets.yaml`, `profiles/human_hg38.yaml`.
- Removed sacCer3-as-default in sidebar FASTA picker; generic resolution tip in `ui_common.py`.
- Updated `AGENT_PLAN.md` with full continuity (6 cards, GSE149117, catalog, next steps).

**Next when ready:**
- Sidebar: explicit “Download demo mcool (GSE149117)” + reference genome dropdown with on-demand fetch to `workspace/references/`.
- Test full Section 2 flow on GSE149117 + hg38.
- Add hub example PNGs (including normalization QC) when user provides figures.

---

## 2026-07-17 — Session 6: Hub full cards, 10kb tips, simplified TAD boundaries

**User:** Box should wrap image+Open; eigenvector “30 vs 70” was resolution mistake; prefer 10kb tip/default on chrom/eigs/TAD; simplify TAD to W1=strong, W2=weak.

**Implemented:** `st.container(border=True)` hub cards; `preferred_view_resolution` + tip on pages 4–6; insulation plot/CSV/help use W1 strong / W2 weak only.

**End of day:** User confirmed Section 2 is complete for today's goals. Next when ready: Section 1 processing.

---

## 2026-07-17 — Session 5: UX polish + batch + safe normalize implemented

**User asks:** boxed/centered hub cards; bottom back buttons; scroll-to-top; batch all chroms + ZIP with progress/preview; shared vmax; fix pysam; TAD legend; strong/weak boundaries both windows; never overwrite original mcool on normalize.

**Implemented:** hub CSS cards; nav helpers; `workspace.py` safe copy; pysam in requirements; TAD dual-window strong/weak + external legend; batch ZIP on chrom/eigs/TADs; docs updated.

---

## 2026-07-17 — Session 4: Section 2 UX redesign implemented

**User feedback (from testing):** Port conflict with Jupyter (use 2001); FASTA path failed for `sacCer3.fa`; liked Normalize explanations; wants hub with two section boxes then 4–5 explained cards with examples; vmax education; TAD dual-window clarity + figure legends.

**Implemented:**
- Multipage: `app.py` Home (Section 1 coming soon + Section 2), `pages/1_Section_2_Analyze.py` gallery, detail pages 2–6.
- `porec_dashboard/help_text.py`, `paths.py`, `ui_common.py`
- Path auto-detect for project FASTA/mcool + resolve vs project root
- TAD plot legends; Window 1 = primary boundaries, Window 2 = comparison
- Example schematics in `assets/examples/`
- Docs/port default **2001**

---

## 2026-07-17 — Session 3: AGENT_PLAN + Section 2 MVP started

**User:** Liked the plan; asked for a short agent reference file (save usage if chat cuts off) and to begin Section 2. Agent does most development.

**Done:**
- Created `AGENT_PLAN.md` (compact continuity doc).
- Scaffolded Section 2 Streamlit app:
  - `app.py` — UI tabs: Normalize, Genome-wide, Chromosome, Eigenvectors, TADs
  - `porec_dashboard/` — cooler_io, plots, eigenvectors, insulation, colormap
  - `profiles/yeast_sacCer3.yaml`
  - Updated `requirements.txt`, `environment.yml`, `README.md`
- Ported notebook logic: fall cmap, genome matrix, ICE balance, GC eigs, insulation/boundaries, PNG/CSV export.
- Not yet run against real mcool on this machine (needs user data path + conda install).

**Next:** Install deps, test with user's mcool; then Section 1 Nextflow wrapper.

---

## 2026-07-17 — Session 2: Answers, notebook review, refined plan

**User provided:**
- Answers in `note`
- Analysis notebook `Pore_C_wt_analysis.ipynb` (yeast WT Pore-C / cooltools)

**Answers summary:**
1. **Deployment:** Prefer open-access feel; primary use = personal laptop/desktop OR HPC (user will test HPC). Not pure public SaaS for heavy compute.
2. **Data scale:** No multiplexed barcodes — Pore-C does not support barcoding in their workflow.
3. **Section scope:** Keep separate — Section 1 = FASTQ→mcool; Section 2 = mcool-import→visualization.
4. **Must-have plots:** Normalization, genome-wide + individual contact maps, eigenvectors, TADs.
5. **Eigenvectors:** Used GC for yeast; unsure if best; interested in gene expression / RNA-Seq as alternative.
6. **Enzyme:** Default consistent (user used NlaIII) but user-selectable.
7. **TADs:** Used insulation score only; wants highlights of other methods by organism/model.
8. **OS:** Expect Mac/Linux primarily; Windows possible later.
9. **Timeline:** Limited time now (couple of weeks); hopes to accomplish a lot when available. Agent will do most software development (user has no SE experience).
10. **EPI2ME:** Used command line; EPI2ME Desktop too heavy for Mac.

**Notebook findings (MVP mapping):**
- Stack: cooler, cooltools, bioframe, matplotlib, numpy, pandas.
- Resolutions used: 1kb, 5kb, 10kb, 25kb; balancing via `cooler.balance_cooler`.
- Custom "fall" colormap for contact maps.
- Genome-wide contact map (block-diagonal cis matrices, exclude chrM).
- Per-chromosome contact maps + E1 track (GC-phased via `cooltools.eigs_cis` + `bioframe.frac_gc`); 25kb preferred for compartments; 10kb also explored.
- Insulation / TAD: `cooltools.insulation` at 10kb preferred; 25kb marked "not great for TADs".
- Triangle (45°) contact map + insulation track underlay (cooltools-style).
- Trans enrichment matrix between chromosomes.
- Explicitly unreliable / deprioritize for sparse yeast data: P(s), O/E genome-wide, saddle plots (low contact depth).
- Chromunity parquet multi-contact exploration (stretch / later).
- Hardcoded local Mac paths; needs to become path-agnostic in app.

**Decisions this session:**
- UI choice for non-developers: **Streamlit** (Python web UI; run locally or on HPC; no frontend expertise needed from user).
- Agent owns most implementation; user validates biology, parameters, and demo data.
- Phased MVP: yeast end-to-end first (import mcool → maps/eigs/TADs), then Section 1 Nextflow wrapper, then organism profiles + RNA-Seq expected track.

---

## 2026-07-17 — Session 1: Project kickoff & planning

**User goals:**
1. Maintain this conversation log going forward.
2. Plan a Pore-C data analysis dashboard to streamline nanopore raw data → processed outputs (mcool, heatmaps, etc.).

**Context shared:**
- Prior experience: Pore-C analysis in *Saccharomyces cerevisiae* (yeast); raw nanopore FASTQ → processed heatmap datasets is currently difficult and manual.
- Reference pipeline: [epi2me-labs/wf-pore-c](https://github.com/epi2me-labs/wf-pore-c) — target for Section 1 (raw FASTQ → mcool and related artifacts).
- Proposed dashboard structure:
  - **Section 1 — Processing:** Raw FASTQ → analyzed data types (mcool, etc.), mirroring wf-pore-c.
  - **Section 2 — Visualization & analysis:** Flexible outputs including genome-wide contact maps, chromosome-specific maps, eigenvector overlays, TAD boundary detection. User will share a `.ipynb` notebook later with example outputs.
- **Cross-organism requirement:** Must work dynamically for yeast, human, mammalian, and plant inputs.
- **Eigenvector / compartment calling:** Method depends on cell/organism type (e.g., RNA-Seq vs. GC coverage).
- **Audience:** Specialized scientists who may not be strong in data science; UX should be user-friendly.
- **Open decision:** Online (web) vs. desktop application.

**Agent response:** Created this log; delivered project plan with key questions, considerations, and phased architecture (see session notes in chat).

---
