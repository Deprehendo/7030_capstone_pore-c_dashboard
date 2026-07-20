"""Biology and parameter help copy for Section 2 pages."""

from __future__ import annotations

NORMALIZE = {
    "title": "Normalize (ICE balancing)",
    "blurb": (
        "Raw contact counts are biased by sequencing depth and how often each genomic "
        "bin is observed. ICE balancing estimates those biases and stores correction "
        "weights so contact frequencies are comparable across the genome."
    ),
    "how": """
### What this does
Iterative Correction and Eigenvector decomposition (ICE) balancing adjusts each bin
so maps reflect interaction preference rather than coverage artifacts.

### Why it matters
Unbalanced maps can invent or hide structure. **Run this before** genome-wide maps,
chromosome maps, eigenvectors, or TAD calling.

### Safe storage (your original file is not modified)
Balancing writes weights into a **working copy** under `workspace/normalized/`
(for example `sample.balanced.mcool`). The original `.mcool` stays unchanged.
Downstream analyses should use that working file (the app switches to it after Normalize).

### How to use
1. Choose resolutions to balance (common choices: 1, 5, 10, and 25 kb).
2. Run balancing once per resolution on the working copy.
3. If a resolution already has weights, it is skipped.
""",
    "example_caption": (
        "Example: after balancing, contact maps use corrected frequencies "
        "instead of raw counts — structure becomes clearer and more comparable."
    ),
    "example_stem": "normalize",
}

NORMALIZATION_QC = {
    "title": "Balanced normalization preview",
    "blurb": (
        "After ICE balancing, preview one chromosome’s contact map on a log1p scale. "
        "A clear diagonal and visible domain structure are a quick visual check that "
        "normalization worked before genome-wide or compartment analyses."
    ),
    "how": """
### What this shows
A single-chromosome **balanced** contact heatmap — the same style as the first map
in the project notebook (`log1p(contacts)`, fall colormap, default vmax 2).

### How to read it
| Pattern | Likely meaning |
|---------|----------------|
| Strong diagonal; domain-like blocks | Balancing looks reasonable — good to proceed |
| Mostly empty / flat | Too sparse at this resolution, or balancing not run yet |
| One arm looks very different | Coverage bias or mapping issue on that region |

### Defaults (from notebook)
- **Resolution:** 25 kb (adjust if your mcool uses other bins)
- **Colormap:** fall; **scale:** log1p(contacts); **vmax:** auto from data (typically ~0.001–0.01 on human balanced data)
- **Requires ICE weights** — run **Normalize** first. GSE149117 demo files ship **without** pre-computed weights.
- At **100 kb / 250 kb**, values are much smaller — use **Auto-scale color** or prefer 25 kb for this visual QC.

Run **Normalize** first, then open this page before genome-wide maps.
""",
    "example_caption": (
        "Example: one chromosome at 25 kb after ICE balancing — "
        "log1p contact map with fall colormap."
    ),
    "example_stem": "balanced_preview",
}

# Alias for imports
BALANCED_PREVIEW = NORMALIZATION_QC

GENOME_WIDE = {
    "title": "Genome-wide contact map",
    "blurb": (
        "A whole-genome heatmap shows how often every pair of loci contacts. "
        "Diagonal blocks are within-chromosome (cis) contacts; off-diagonal blocks "
        "are between chromosomes (trans)."
    ),
    "how": """
### Biology
Chromatin conformation capture (including Pore-C) counts physical proximity.
Bright regions interact more often. Mitochondrial DNA and unplaced contigs are
usually excluded because they are not standard nuclear chromosomes.

### Resolution by organism
| Organism | Recommended resolution | Why |
|----------|------------------------|-----|
| Yeast | 25 kb | Small genome — manageable bin count |
| Human / mouse | **50–100 kb** | Large genome — finer bins explode memory |

The app blocks or warns below organism-specific limits and shows estimated bin count.

### How this plot is made
- Contact matrix at your chosen resolution
- Log-scaled color with a high-percentile clip so extreme bins do not wash out the map
- Black lines mark chromosome boundaries

### Reading tips
Look for bright diagonal blocks (chromosome self-association) and any unusual
trans enrichment between specific chromosome pairs.
""",
    "example_caption": (
        "Example: whole-genome matrix with chromosome labels on both axes; "
        "brighter = more contacts (log scale)."
    ),
    "example_stem": "genome_wide",
}

CHROMOSOME = {
    "title": "Chromosome / region contact map",
    "blurb": (
        "Zoom into one chromosome (or a sub-region) to see local contact patterns — "
        "domains, loops, and chromosome-arm structure that are hard to see genome-wide."
    ),
    "how": """
### Biology
A single-chromosome map highlights cis contacts along that chromosome. Strong
near-diagonal signal is expected (nearby loci contact more). Blocks or stripes can
reflect domains or other organized structure.

### Parameter: vmax (color scale ceiling)
**What it is:** On a log-scaled heatmap, `vmax` is the upper color limit. Contacts
at or above `vmax` share the hottest color. It does **not** change the underlying data —
only how color is mapped for viewing.

**Starting point (balanced, ~10–25 kb):** try **0.05–0.2**. The project notebook used **0.1**.

**How to tell if vmax is right**
| What you see | What to do |
|--------------|------------|
| Map mostly black / empty | Raise `vmax`, or check balancing / resolution |
| Map washed out, little structure | Lower `vmax` |
| Domains/structure visible; colorbar used across the range | Good |

Tip: if unsure, start at `0.1` and adjust by ~2× until structure is clear.

### Resolution tip
For individual chromosome maps, **~10 kb** often shows more detail than 25 kb
when depth allows. The app defaults to 10 kb when available.

### Batch “all chromosomes”
When generating every chromosome at once, **one shared vmax** is used for all plots
so color scales are comparable. Tune vmax on a single chromosome first, then run batch.
""",
    "example_caption": (
        "Example: square contact map for one chromosome. Adjust vmax until domain "
        "structure is visible without washing out the plot."
    ),
    "example_stem": "chromosome",
}

EIGENVECTORS = {
    "title": "Eigenvectors / compartments",
    "blurb": (
        "The first eigenvector (E1) summarizes large-scale compartment-like patterns "
        "(often A/B-like): regions that prefer to contact similar regions. A phasing "
        "track sets the sign so positive E1 points toward the expected active side."
    ),
    "how": """
### Biology
Compartments are genome-wide interaction preferences, coarser than TADs. In mammals,
A is typically active/open and B inactive/closed. In yeast the picture can differ,
but E1 is still a useful summary of contact polarization.

### Two resolutions (important)
| Step | Typical yeast | Typical human / mouse |
|------|---------------|------------------------|
| **Calling** (`eigs_cis`) | 25 kb | **100 kb** |
| **Map viewing** (this page) | Same as calling | Same as calling |
| **Finer local maps** | Chromosome map @ 10 kb | Chromosome map @ 10 kb |

This page defaults to **compartment calling** resolution from your organism profile.
Use **Chromosome map** for finer-bin contact heatmaps.

### Phasing track
See the phasing table on this page. Summary:
- **Yeast** — GC from FASTA (notebook default)
- **Human / mouse** — upload RNA-seq or H3K27ac when possible; GC is fallback

### Chromosomes
Profile rules drop mitochondria, unplaced/alt contigs, and (for mammals) chrY from
compartment calling unless you disable filtering in the sidebar.
""",
    "example_caption": (
        "Example: contact map with E1 track below — red/blue mark opposite compartment sides."
    ),
    "example_stem": "eigenvectors",
}

TADS = {
    "title": "TADs / insulation",
    "blurb": (
        "Topologically associating domains (TADs) are local neighborhoods of preferential "
        "contact. Insulation score finds boundaries where contacts across a locus are "
        "depleted — dips in the track often mark domain edges."
    ),
    "how": """
### Biology
Insulation measures how strongly a locus “blocks” contacts between its left and right
flanks over a chosen **window** (genomic distance).

### Two windows, simple boundary story
At ~**10 kb** resolution, use windows of **10×** and **25×**
binsize (typically **100 kb** and **250 kb**). Both insulation score curves are plotted.

Boundaries on the figure are simplified for biology reading:
- **Strong** — called boundaries from **Window 1** (e.g. 100 kb)
- **Weak** — called boundaries from **Window 2** (e.g. 250 kb)

Both windows are standard cooltools boundary calls at different scales; the
strong/weak labels are a dashboard simplification, not a separate published method.

| Setting | Effect |
|---------|--------|
| Window too small | Noisy, many false boundaries |
| Window too large | Merges real domains; fewer boundaries |
| Resolution for TADs | Prefer **~10 kb** when depth allows |

### Explore, scrub, and bookmark
1. **Compute** insulation once (full genome tables).
2. **Triangle** — contact map for the scrubbed viewport.
3. **Detail insulation** — log2 scores and boundaries **only in that viewport** (readable scale).
4. **Overview strip** — full-chromosome score curves with shaded band showing where you are scrubbing (no boundary clutter).
5. **Bookmark** regions → export PNGs + CSVs + `bookmarks_manifest.csv`.

CSV tables always cover the full genome for stats; bookmarked PNGs are curated figures.

### Other methods (later / reference)
Insulation is the default here. Directionality index and Arrowhead are more common
in deep mammalian Hi-C; plants may need conservative insulation settings.
""",
    "example_caption": (
        "Example: triangle contact map with dual-window insulation scores; "
        "strong ticks from the 100 kb window, weak ticks from the 250 kb window."
    ),
    "example_stem": "tads",
}

SECTION2_CARDS = [
    NORMALIZE,
    NORMALIZATION_QC,
    GENOME_WIDE,
    CHROMOSOME,
    EIGENVECTORS,
    TADS,
]
