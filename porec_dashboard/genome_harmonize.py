"""Detect and fix chromosome naming mismatches between cooler and FASTA."""

from __future__ import annotations

from pathlib import Path

import bioframe
import cooler

# Primary GRCh38 RefSeq accession → UCSC (from NCBI assembly_report).
_REFSEQ_TO_UCSC: dict[str, str] = {
    "NC_000001.11": "chr1",
    "NC_000002.12": "chr2",
    "NC_000003.12": "chr3",
    "NC_000004.12": "chr4",
    "NC_000005.10": "chr5",
    "NC_000006.12": "chr6",
    "NC_000007.14": "chr7",
    "NC_000008.11": "chr8",
    "NC_000009.12": "chr9",
    "NC_000010.11": "chr10",
    "NC_000011.10": "chr11",
    "NC_000012.12": "chr12",
    "NC_000013.11": "chr13",
    "NC_000014.9": "chr14",
    "NC_000015.10": "chr15",
    "NC_000016.10": "chr16",
    "NC_000017.11": "chr17",
    "NC_000018.10": "chr18",
    "NC_000019.10": "chr19",
    "NC_000020.11": "chr20",
    "NC_000021.9": "chr21",
    "NC_000022.11": "chr22",
    "NC_000023.11": "chrX",
    "NC_000024.10": "chrY",
    "NC_012920.1": "chrM",
}


def fasta_chrom_style(fasta_records: dict[str, str]) -> str:
    keys = list(fasta_records.keys())
    if any(k.startswith("chr") for k in keys):
        return "ucsc"
    if any(k.startswith("NC_") for k in keys):
        return "refseq"
    return "other"


def cooler_chrom_style(clr: cooler.Cooler) -> str:
    chroms = list(clr.chromnames)
    if any(c.startswith("chr") for c in chroms):
        return "ucsc"
    if chroms and chroms[0].isdigit():
        return "ensembl_no_prefix"
    return "other"


def remap_fasta_to_ucsc(fasta_records: dict[str, str]) -> dict[str, str]:
    """Rename RefSeq primary chromosomes to UCSC chr names (best-effort)."""
    out: dict[str, str] = {}
    for name, seq in fasta_records.items():
        out[_REFSEQ_TO_UCSC.get(name, name)] = seq
    return out


def load_fasta_for_cooler(
    clr: cooler.Cooler,
    fasta_path: str | Path,
    chromosomes: list[str] | None = None,
) -> dict[str, str]:
    """
    Load FASTA and rename records when mcool uses UCSC names but FASTA uses RefSeq.

    When ``chromosomes`` is given, only those names must be present in FASTA
    (e.g. after excluding chrEBV and alt contigs from compartment calling).
    """
    fasta = bioframe.load_fasta(str(fasta_path))
    mcool_chroms = set(chromosomes) if chromosomes is not None else set(clr.chromnames)
    if mcool_chroms.issubset(fasta.keys()):
        return fasta
    if cooler_chrom_style(clr) == "ucsc" and fasta_chrom_style(fasta) == "refseq":
        remapped = remap_fasta_to_ucsc(fasta)
        if mcool_chroms.issubset(remapped.keys()):
            return remapped
    missing = sorted(mcool_chroms - set(fasta.keys()))[:5]
    raise ValueError(
        "Chromosome names in the mcool do not match the reference FASTA. "
        f"Example missing in FASTA: {missing}. "
        "GSE149117 and most Hi-C mcools use UCSC names (chr1, …). "
        "Re-download **hg38** from the sidebar (UCSC primary assembly) or use a "
        "chr-named FASTA that includes alt contigs."
    )


def fasta_mcool_compatible(
    clr: cooler.Cooler,
    fasta_path: str | Path,
    chromosomes: list[str] | None = None,
) -> tuple[bool, str]:
    """Quick check for sidebar warnings (uses FASTA index when available)."""
    path = Path(fasta_path)
    fai = path.with_suffix(path.suffix + ".fai") if path.suffix else Path(str(path) + ".fai")
    if not fai.is_file():
        fai = Path(str(fasta_path) + ".fai")
    if not fai.is_file():
        return True, ""
    fasta_chroms = {line.split("\t", 1)[0] for line in fai.read_text().splitlines() if line.strip()}
    mcool_chroms = set(chromosomes) if chromosomes is not None else set(clr.chromnames)
    if mcool_chroms.issubset(fasta_chroms):
        return True, ""
    if cooler_chrom_style(clr) == "ucsc" and fasta_chrom_style(dict.fromkeys(fasta_chroms)) == "refseq":
        remapped = set(remap_fasta_to_ucsc(dict.fromkeys(fasta_chroms)).keys())
        if mcool_chroms.issubset(remapped):
            return True, "RefSeq FASTA detected — will remap primary chromosomes to UCSC names at runtime."
        return False, (
            "FASTA uses RefSeq accessions (NC_*) but mcool uses UCSC names (chr*). "
            "Re-download hg38 from the reference catalog (UCSC assembly) or use harmonized FASTA."
        )
    missing = len(mcool_chroms - fasta_chroms)
    return False, (
        f"{missing} mcool chromosome(s) not found in FASTA index. "
        "Check that assembly and contig naming match (UCSC chr* for GSE149117)."
    )
