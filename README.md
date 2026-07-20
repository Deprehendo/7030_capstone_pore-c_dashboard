# Pore-C Dashboard

**Pore-C Dashboard** is a Streamlit app for analyzing Pore-C (long-read Hi-C) contact data. Import a `.mcool` file, balance contacts, visualize genome-wide and chromosome maps, call A/B compartments from GC-phased eigenvectors, and identify TAD boundaries — all from a browser UI, no Python notebook required.

Built for specialized biologists on a laptop, desktop, or HPC cluster (Streamlit port **2001**, separate from Jupyter **2000**).

**Section 2 (Analyze) is working today.** Section 1 (raw FASTQ/BAM → mcool via [wf-pore-c](https://github.com/epi2me-labs/wf-pore-c)) is planned.

Repo: [github.com/Deprehendo/7030_capstone_pore-c_dashboard](https://github.com/Deprehendo/7030_capstone_pore-c_dashboard)

## Sections

1. **Process** (coming soon) — FASTQ/BAM → `wf-pore-c` → `.mcool`
2. **Analyze** (available) — import `.mcool` → balance, preview, maps, eigenvectors, TADs

## What you can do today

Open **Section 2** from the home page. The analysis hub has six modules:

| Module | What you do | What you get |
|--------|-------------|--------------|
| **Normalize** | Run ICE balancing on a `.mcool` | Balanced copy in `workspace/normalized/`; original never modified |
| **Balanced preview** | QC one chromosome at chosen resolution | Log1p contact map (fall colormap, auto-vmax) |
| **Genome-wide map** | Block-diagonal cis contact map | PNG + optional all-chromosome ZIP |
| **Chromosome map** | Triangle contact map for one chrom/region | PNG export |
| **Eigenvectors** | GC-phased A/B compartment calling | E1 tracks, CSV/PNG; batch ZIP |
| **TADs / insulation** | Dual-window boundary calling | Scrub chromosomes, bookmark regions, export ZIP (PNGs + CSVs + manifest); dual-panel insulation plot |

**Typical workflow:** download demo data → Normalize → Balanced preview → Genome-wide map → Chromosome map → Eigenvectors → TADs.

Each page includes biology-focused help text and organism-specific guidance tables.

## Download and run

```bash
git clone https://github.com/Deprehendo/7030_capstone_pore-c_dashboard.git
cd 7030_capstone_pore-c_dashboard

# Create / activate environment (conda recommended)
conda env create -f environment.yml   # first time only
conda activate 7030_capstone_project

# If the env already exists:
# conda activate 7030_capstone_project

pip install -r requirements.txt

# Launch the dashboard (port 2001 — not Jupyter's typical 2000)
streamlit run app.py --server.port 2001 --server.address 0.0.0.0
```

On HPC, run Streamlit on a compute node and SSH-tunnel to port **2001** to view the UI in your browser.

## Quick start (Section 2)

If you already have the repo cloned and the environment active:

```bash
conda activate 7030_capstone_project
pip install -r requirements.txt
streamlit run app.py --server.port 2001 --server.address 0.0.0.0
```

### Try public demo data (no local files needed)

1. Open **Section 2** → use the sidebar **Demo mcool** section
2. Select **Human Pore-C — HCC1954 (GSE149117)** → **Download** (~360 MB)
3. Select **hg38** reference → **Download** (large; cached once in `workspace/references/`)
4. Run **Normalize** → **Balanced normalization preview** → other analyses

Or paste paths to your own `.mcool` / FASTA in the sidebar.

## Supported data and organisms

- **Input:** `.mcool` (multi-resolution cooler); reference FASTA required for GC-phased eigenvectors
- **Demo data:** [GSE149117](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149117) HCC1954 (~360 MB) — downloadable from the sidebar
- **Reference genomes (sidebar download):** hg38, hg19, mm10, mm39, sacCer3 (UCSC chromosome naming)
- **Organism profiles:** YAML-driven resolution defaults, chromosome filtering (mito, alt contigs, chrEBV, etc.), and in-app guidance tables in `profiles/`
- **Tech stack:** Python 3.10, Streamlit, cooler, cooltools, bioframe, pysam, matplotlib, PyYAML

## Important behaviors

- **Normalize is safe:** ICE weights go to `workspace/normalized/*.balanced.mcool` — original untouched
- **Balanced preview:** One-chromosome log1p contact map after balancing (notebook-style QC)
- **Reference catalog:** hg38, hg19, mm10, mm39, sacCer3 in `profiles/reference_genomes.yaml`
- **Batch downloads:** All-chromosome ZIP for maps, eigenvectors, TADs
- **TADs:** Window 1 = strong boundaries; Window 2 = weak; scrub/bookmark regions; dual-panel insulation plot
- **Reference harmonization:** UCSC-style FASTA (`chr1`, …) must match mcool chromosome names for GC phasing

## Project status

**Done (Jul 2026):** Section 2 complete — six analysis modules, public GSE149117 demo, reference catalog, cross-organism profiles, batch exports. End-to-end validated on GSE149117 HCC1954 + hg38 UCSC.

**Planned:**
- Section 1 — Nextflow wrapper for [wf-pore-c](https://github.com/epi2me-labs/wf-pore-c) (FASTQ/BAM → mcool)
- RNA-seq / H3K27ac phasing upload for mammalian eigenvectors
- Plant organism profiles; ENCODE bigWig auto-fetch

Full milestone timeline and architecture notes: **[`PROGRESS.md`](PROGRESS.md)**. Session-level decisions: [`CONVERSATION_LOG.md`](CONVERSATION_LOG.md).

## Layout

| Path | Role |
|------|------|
| `app.py` | Home |
| `pages/` | Section 2 hub (6 cards) + analysis pages |
| `porec_dashboard/` | Analysis + catalog download helpers |
| `profiles/` | Demo datasets, reference genomes, organism defaults |
| `workspace/` | Runtime cache (gitignored): demo/, references/, normalized/ |
| `PROGRESS.md` | Milestone timeline for instructors / GitHub review |
| `CONVERSATION_LOG.md` | Detailed session notes |

## Notes

- GC eigenvectors need **pysam** and a matching reference FASTA
- GSE149117 mcool is **GRCh38** — use **hg38** for GC phasing
