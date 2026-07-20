"""Load and normalize cooler / mcool files."""

from __future__ import annotations

import fnmatch
from typing import Iterable

import cooler
import pandas as pd

# Always dropped when exclude_mito is True (mitochondria / plastids / viral spike-ins).
_DEFAULT_MITO_EXCLUDE = frozenset(
    {
        "chrM",
        "chrMT",
        "MT",
        "Mito",
        "mitochondrion",
        "chrC",
        "Pt",
        "Cp",
        "chrEBV",
        "EBV",
    }
)

# Common GRCh38 / mm10 alt and unplaced contig patterns.
_DEFAULT_ALT_PATTERNS = (
    "chrUn_*",
    "*_random*",
    "*_alt*",
    "GL*",
    "KI*",
    "NT_*",
    "*EBV*",
)


def _matches_patterns(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def analysis_chromosomes(
    clr: cooler.Cooler,
    exclude: Iterable[str] | None = None,
    *,
    exclude_mito: bool = True,
    profile: dict | None = None,
    purpose: str = "general",
) -> list[str]:
    """
    Chromosomes to use in plots and cooltools views.

    ``exclude`` (legacy): explicit name blocklist; merged with profile excludes.
    ``exclude_mito``: drop mito/plastid names and profile ``ui.exclude_chromosomes``.
    ``purpose``: ``general``, ``genome_wide``, or ``compartment`` (stricter for eigs).
    """
    skip: set[str] = set()
    patterns: list[str] = []

    if exclude_mito:
        skip |= _DEFAULT_MITO_EXCLUDE
        if profile:
            ui = profile.get("ui", {})
            skip |= set(ui.get("exclude_chromosomes") or [])
            patterns.extend(ui.get("exclude_patterns") or [])
            if purpose == "compartment":
                skip |= set(ui.get("compartment_exclude") or [])
            elif purpose == "genome_wide":
                skip |= set(ui.get("genome_wide_exclude") or [])
        else:
            patterns.extend(_DEFAULT_ALT_PATTERNS)

    if exclude is not None:
        skip |= set(exclude)

    chroms: list[str] = []
    for name in clr.chromnames:
        if name in skip:
            continue
        if patterns and _matches_patterns(name, patterns):
            continue
        chroms.append(name)
    return chroms


def estimate_genome_bins(clr: cooler.Cooler, chromosomes: Iterable[str]) -> int:
    """Total bin count across selected chromosomes at this cooler resolution."""
    total = 0
    for chrom in chromosomes:
        total += int(clr.chromsizes[chrom]) // clr.binsize
    return total


def list_resolutions(mcool_path: str) -> list[int]:
    """Return available resolutions (bp) sorted ascending."""
    uris = cooler.fileops.list_coolers(mcool_path)
    resolutions: list[int] = []
    for uri in uris:
        # e.g. /resolutions/1000 or ::/resolutions/1000
        part = uri.rstrip("/").split("/")[-1]
        if part.isdigit():
            resolutions.append(int(part))
    return sorted(set(resolutions))


def open_cooler(mcool_path: str, resolution: int) -> cooler.Cooler:
    """Open one resolution from an .mcool (or plain .cool) file."""
    if mcool_path.endswith(".cool") and "::" not in mcool_path:
        # single-resolution cool
        try:
            return cooler.Cooler(mcool_path)
        except Exception:
            pass
    uri = f"{mcool_path}::resolutions/{resolution}"
    return cooler.Cooler(uri)


def has_weights(clr: cooler.Cooler) -> bool:
    """True if ICE balance weights are already stored."""
    return "weight" in clr.bins().columns


def balance_cooler(clr: cooler.Cooler, *, store: bool = True) -> None:
    """Run ICE balancing and optionally store weights in the file."""
    cooler.balance_cooler(clr, store=store)


def chromsizes_table(clr: cooler.Cooler) -> pd.DataFrame:
    """Chromosome sizes as a small dataframe."""
    return pd.DataFrame(
        {
            "chrom": list(clr.chromnames),
            "length": [int(clr.chromsizes[c]) for c in clr.chromnames],
        }
    )
