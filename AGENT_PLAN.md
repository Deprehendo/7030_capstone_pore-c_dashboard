# Pore-C Dashboard — Agent Reference Plan

Short recovery doc. Prefer this over re-reading the full chat.

## Goal
User-friendly Pore-C dashboard for specialized scientists (not software engineers).
Agent does most development. User validates biology + tests on laptop/HPC.

## Two sections (keep separate)
1. **Process:** FASTQ/BAM → Nextflow `wf-pore-c` → `.mcool` (no barcoding)
2. **Analyze:** import `.mcool` → maps / eigenvectors / TADs

## UI
Streamlit multipage: Home → Section 2 hub (**6** boxed centered cards, **2×3 grid**) → detail pages.
Streamlit port **2001** (never collide with Jupyter **2000**).

### Section 2 hub cards (order)
1. Normalize (ICE balancing)
2. **Balanced normalization preview** — log1p contact map (notebook cell 5; NOT P(s) curves)
3. Genome-wide contact map
4. Chromosome / region contact map
5. Eigenvectors / compartments
6. TADs / insulation

Example PNGs under `assets/examples/` — **deferred**.

## Critical behaviors
- **Normalize:** copy to `workspace/normalized/*.balanced.mcool`; never overwrite original
- **Balanced preview:** single-chromosome `log1p` map, fall colormap, vmax=2, default 25 kb
- **Demo data:** sidebar download from `profiles/demo_datasets.yaml` → `workspace/demo/`
- **References:** hg38 / hg19 / mm10 / mm39 / sacCer3 from `profiles/reference_genomes.yaml` → `workspace/references/` (UCSC chr naming)
- **Organism profiles:** `profiles/human_hg38.yaml`, `yeast_sacCer3.yaml`, `mouse_mm10.yaml` drive resolution defaults, chromosome filtering, and guidance tables
- **Compartment calling:** human/mouse default **100 kb** eigs; yeast **25 kb**; chromosome/TAD viewing **10 kb**
- **Chromosome filter:** profile-driven excludes (mito, alt/random contigs, **chrEBV**, chrY for compartments on mammals)
- **Genome-wide guardrails:** warn/block below organism min resolution; show bin count
- **Batch:** all chromosomes → progress → preview → ZIP
- **TADs:** W1 strong / W2 weak; external legend; compute once → chromosome scrubber → bookmark regions → export ZIP
- **TAD insulation plot:** dual-panel — viewport detail (scores + boundaries) + full-chromosome overview strip with shaded viewport band; PuOr triangle with auto-vmax
- **GC eigs:** pysam + matching reference FASTA; mammals guided toward RNA-seq / H3K27ac upload

## Public demo (GSE149117)
- Default: **GSM4490690** HCC1954 (~360 MB), GRCh38
- Catalog: [profiles/demo_datasets.yaml](profiles/demo_datasets.yaml)
- Pair with **hg38** reference from sidebar

## Page paths
| Page | File |
|------|------|
| Hub | `pages/1_Section_2_Analyze.py` |
| Normalize | `pages/2_Normalize.py` |
| Balanced preview | `pages/3_Normalization_QC.py` |
| Genome-wide | `pages/4_Genome_wide_map.py` |
| Chromosome | `pages/5_Chromosome_map.py` |
| Eigenvectors | `pages/6_Eigenvectors.py` |
| TADs | `pages/7_TADs_insulation.py` |

## How to run
```bash
conda activate 7030_capstone_project
pip install -r requirements.txt
streamlit run app.py --server.port 2001 --server.address 0.0.0.0
```

## Stack
cooler, cooltools, bioframe, pysam, matplotlib, streamlit, pyyaml

## Next
- **Section 2 milestone complete (Session 12).** GSE149117 + hg38 E2E validated; TAD scrub/bookmark + dual-panel insulation approved.
- Hub example PNGs when user provides figures
- Section 1 Nextflow wrapper (FASTQ/BAM → mcool)
