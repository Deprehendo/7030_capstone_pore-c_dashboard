"""Organism profiles for resolution defaults, tips, and preview chromosome."""

from __future__ import annotations

import yaml

from .paths import PROJECT_ROOT

PROFILES_DIR = PROJECT_ROOT / "profiles"

_PROFILE_BY_ORGANISM = {
    "homo_sapiens": "human_hg38.yaml",
    "saccharomyces_cerevisiae": "yeast_sacCer3.yaml",
    "mus_musculus": "mouse_mm10.yaml",
}

_PROFILE_BY_REF = {
    "hg38": "human_hg38.yaml",
    "hg19": "human_hg19.yaml",
    "sacCer3": "yeast_sacCer3.yaml",
    "mm10": "mouse_mm10.yaml",
    "mm39": "mouse_mm39.yaml",
}


def load_organism_profile(name: str) -> dict:
    path = PROFILES_DIR / name
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def profile_for_reference(reference_id: str | None) -> dict | None:
    if not reference_id:
        return None
    fname = _PROFILE_BY_REF.get(reference_id)
    if not fname or not (PROFILES_DIR / fname).is_file():
        return None
    return load_organism_profile(fname)


def profile_for_demo(demo_entry: dict) -> dict | None:
    ref = demo_entry.get("reference_genome")
    if ref:
        p = profile_for_reference(ref)
        if p:
            return p
    organism = demo_entry.get("organism")
    fname = _PROFILE_BY_ORGANISM.get(organism or "")
    if fname and (PROFILES_DIR / fname).is_file():
        return load_organism_profile(fname)
    return None


def _compartment_call_bp(profile: dict | None) -> int | None:
    if not profile:
        return None
    comp = profile.get("compartment", {})
    return comp.get("call_resolution_bp") or comp.get("preferred_resolution_bp")


def normalize_resolution_defaults(resolutions: list[int], profile: dict | None) -> list[int]:
    candidates = [1000, 5000, 10000, 25000, 100000]
    if profile and profile.get("organism") == "homo_sapiens":
        candidates = [1000, 5000, 10000, 25000, 100000, 250000]
    return [r for r in candidates if r in resolutions] or resolutions[:4]


def preview_resolution_default(resolutions: list[int], profile: dict | None) -> int:
    if profile:
        pref = _compartment_call_bp(profile)
        if pref and pref in resolutions:
            return pref
    return 25_000 if 25_000 in resolutions else resolutions[len(resolutions) // 2]


def preferred_compartment_resolution(resolutions: list[int], profile: dict | None) -> int:
    """Resolution for cooltools.eigs_cis (compartment calling)."""
    call = _compartment_call_bp(profile)
    if call and call in resolutions:
        return call
    if profile and profile.get("organism") == "homo_sapiens":
        for r in (100_000, 50_000, 25_000):
            if r in resolutions:
                return r
    if 25_000 in resolutions:
        return 25_000
    return resolutions[len(resolutions) // 2]


def preview_chromosome_default(chroms: list[str], profile: dict | None) -> str:
    if not chroms:
        return ""
    prefs: list[str] = []
    if profile and profile.get("organism") == "homo_sapiens":
        prefs = ["chr21", "chr22", "chr1"]
    elif profile and profile.get("organism") == "mus_musculus":
        prefs = ["chr19", "chr1", "chr2"]
    elif profile and profile.get("organism") == "saccharomyces_cerevisiae":
        prefs = ["chrVII", "chrIV", "chrIII"]
    for p in prefs:
        if p in chroms:
            return p
    return chroms[0]


def preferred_view_resolution(
    resolutions: list[int],
    profile: dict | None,
    *,
    prefer: int = 10_000,
    fallback: int = 25_000,
) -> int:
    """Resolution for chromosome maps and TAD insulation (finer detail)."""
    if profile:
        view = profile.get("compartment", {}).get("view_resolution_bp")
        if view and view in resolutions:
            return view
        pref = profile.get("tad", {}).get("preferred_resolution_bp")
        if pref and pref in resolutions:
            return pref
    if prefer in resolutions:
        return prefer
    if fallback in resolutions:
        return fallback
    return resolutions[len(resolutions) // 2]


def view_resolution_tip(profile: dict | None) -> str:
    if profile and profile.get("ui", {}).get("notes"):
        return profile["ui"]["notes"].strip()
    return (
        "For many Pore-C datasets, **~10 kb** is a practical default for "
        "chromosome maps and TADs when that resolution exists. "
        "**Compartment calling (eigs)** uses a coarser default (see Eigenvectors page)."
    )


def compartment_resolution_tip(profile: dict | None) -> str:
    call = _compartment_call_bp(profile)
    if profile and call:
        kb = call // 1000
        org = profile.get("display_name", "this organism")
        return (
            f"For **{org}**, compartment calling (`eigs_cis`) defaults to **{kb} kb**. "
            "Mammalian Hi-C/Pore-C literature often uses 100 kb–1 Mb; yeast commonly uses 25 kb. "
            "Use the Chromosome map page for finer-bin contact views."
        )
    return (
        "Compartment calling (`eigs_cis`) uses a coarser resolution than chromosome/TAD maps. "
        "Default follows the active organism profile when set."
    )


def phasing_recommendation(profile: dict | None) -> str:
    if not profile:
        return "Upload RNA-seq or histone tracks when available; GC from FASTA is a universal fallback."
    comp = profile.get("compartment", {})
    if comp.get("phasing_note"):
        return comp["phasing_note"].strip()
    method = comp.get("default_method", "gc")
    if method == "gc" and profile.get("organism") in ("homo_sapiens", "mus_musculus"):
        return (
            "For mammals, **RNA-seq or H3K27ac** tracks usually phase compartments better than GC alone. "
            "GC from FASTA remains available as a fallback."
        )
    return "GC from reference FASTA is a practical default for this organism."


def vmax_hint(profile: dict | None) -> str:
    if profile and profile.get("organism") == "homo_sapiens":
        return "Human (balanced, ~10–25 kb): try **0.02–0.1**; tune until structure is visible."
    if profile and profile.get("organism") == "mus_musculus":
        return "Mouse (balanced, ~10–25 kb): try **0.02–0.1**; tune until structure is visible."
    return "Balanced data (~10–25 kb): try **0.05–0.2** (notebook default **0.1**)."


def genome_wide_resolution_default(resolutions: list[int], profile: dict | None) -> int:
    if profile and profile.get("organism") in ("homo_sapiens", "mus_musculus"):
        for r in (100_000, 50_000, 25_000):
            if r in resolutions:
                return r
    return 25_000 if 25_000 in resolutions else resolutions[len(resolutions) // 2]


def genome_wide_min_resolution(profile: dict | None) -> int | None:
    if not profile:
        return None
    return profile.get("ui", {}).get("genome_wide_min_resolution_bp")


def genome_wide_max_bins(profile: dict | None) -> int:
    if not profile:
        return 20_000
    return int(profile.get("ui", {}).get("genome_wide_max_bins", 20_000))
