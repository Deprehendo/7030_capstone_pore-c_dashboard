# Pore-C Dashboard

Streamlit app to streamline Pore-C analysis.

## Project progress

Development began from a personal yeast Pore-C analysis workflow and grew into a multipage Streamlit application for scientists without software engineering backgrounds.

**Section 2 — Analyze is complete** for capstone milestone 1 (Jul 17–20, 2026):

- ICE normalization, balanced preview, genome-wide and chromosome contact maps, GC-phased eigenvectors, TAD/insulation calling
- **TAD page:** compute once → chromosome scrubber → bookmark regions → export ZIP (PNGs + CSVs)
- **Dual-panel insulation plot:** viewport detail + full-chromosome overview strip
- **Public demo data:** [GSE149117](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149117) human Pore-C downloadable from the sidebar (~360 MB starter sample)
- **Reference catalog:** hg38, hg19, mm10, mm39, sacCer3 (UCSC chromosome naming; download from sidebar)
- **Cross-organism support:** YAML profiles with resolution defaults, chromosome filtering, and in-app guidance tables
- **UX polish:** 6-card analysis hub, biology help text, batch ZIP exports, safe normalize (original mcool never overwritten)
- **Validated:** End-to-end on GSE149117 HCC1954 + hg38 UCSC (Session 12)

**Planned:** Section 1 — Nextflow wrapper for [wf-pore-c](https://github.com/epi2me-labs/wf-pore-c) (FASTQ/BAM → mcool).

Full milestone timeline, architecture notes, and suggested Git commit chunks: **[`PROGRESS.md`](PROGRESS.md)**. Session-level decisions: [`CONVERSATION_LOG.md`](CONVERSATION_LOG.md).

## Sections

1. **Process** (coming soon) — FASTQ/BAM → `wf-pore-c` → `.mcool`
2. **Analyze** (available) — import `.mcool` → balance, preview, maps, eigenvectors, TADs

## Quick start (Section 2)

Use port **2001** (not Jupyter’s typical **2000**):

```bash
conda activate 7030_capstone_project
pip install -r requirements.txt
streamlit run app.py --server.port 2001 --server.address 0.0.0.0
```

### Try public demo data (no local files needed)

1. Open **Section 2** → use the sidebar **Demo mcool** section
2. Select **Human Pore-C — HCC1954 (GSE149117)** → **Download** (~360 MB)
3. Select **hg38** reference → **Download** (large; cached once)
4. Run **Normalize** → **Balanced normalization preview** → other analyses

Or paste paths to your own `.mcool` / FASTA.

## Important behaviors

- **Normalize is safe:** ICE weights go to `workspace/normalized/*.balanced.mcool` — original untouched
- **Balanced preview:** One-chromosome log1p contact map after balancing (notebook-style QC)
- **Reference catalog:** hg38, hg19, mm10, mm39, sacCer3 in `profiles/reference_genomes.yaml`
- **Batch downloads:** All-chromosome ZIP for maps, eigenvectors, TADs
- **TADs:** Window 1 = strong boundaries; Window 2 = weak; scrub/bookmark regions; dual-panel insulation plot

## Layout

| Path | Role |
|------|------|
| `app.py` | Home |
| `pages/` | Section 2 hub (6 cards) + analysis pages |
| `porec_dashboard/` | Analysis + catalog download helpers |
| `profiles/` | Demo datasets, reference genomes, organism defaults |
| `workspace/` | demo/, references/, normalized/ caches |
| `PROGRESS.md` | Milestone timeline for instructors / GitHub review |
| `CONVERSATION_LOG.md` | Detailed session notes |

## Notes

- GC eigenvectors need **pysam** and a matching reference FASTA
- GSE149117 mcool is **GRCh38** — use **hg38** for GC phasing
