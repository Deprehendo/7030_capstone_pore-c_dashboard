"""Resolve data paths relative to the project root (not Streamlit CWD)."""

from __future__ import annotations

from pathlib import Path

# porec_dashboard/ -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

FASTA_GLOBS = ("*.fa", "*.fasta", "*.fna")
MCOOL_GLOBS = ("*.mcool", "*.cool")


def project_root() -> Path:
    return PROJECT_ROOT


def resolve_data_path(user_path: str | Path | None) -> tuple[Path | None, list[str]]:
    """
    Resolve a user-supplied path.

    Tries, in order: absolute/expanded path, project root / path, CWD / path.
    Returns (resolved_path_or_None, list_of_tried_strings).
    """
    if user_path is None:
        return None, []
    raw = str(user_path).strip()
    if not raw:
        return None, []

    tried: list[str] = []
    candidates = [
        Path(raw).expanduser(),
        PROJECT_ROOT / raw,
        Path.cwd() / raw,
    ]
    # Also try basename under project root if a longer relative path was given
    name = Path(raw).name
    if name and name != raw:
        candidates.append(PROJECT_ROOT / name)

    seen: set[str] = set()
    for cand in candidates:
        key = str(cand.resolve()) if cand.exists() else str(cand)
        if key in seen:
            continue
        seen.add(key)
        tried.append(str(cand))
        if cand.is_file():
            return cand.resolve(), tried
    return None, tried


def discover_files(patterns: tuple[str, ...], directory: Path | None = None) -> list[Path]:
    """Find matching files in project root (non-recursive) then one level deep."""
    root = directory or PROJECT_ROOT
    found: list[Path] = []
    for pattern in patterns:
        found.extend(sorted(root.glob(pattern)))
        found.extend(sorted(root.glob(f"*/{pattern}")))
    # unique, files only
    out: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        if p.is_file():
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(rp)
    return out


def discover_fastas() -> list[Path]:
    return discover_files(FASTA_GLOBS)


def discover_mcools() -> list[Path]:
    return discover_files(MCOOL_GLOBS)


def assets_examples_dir() -> Path:
    return PROJECT_ROOT / "assets" / "examples"


def example_image_path(stem: str) -> Path | None:
    """Return path to example PNG if it exists (stem without extension)."""
    d = assets_examples_dir()
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = d / f"{stem}{ext}"
        if p.is_file():
            return p
    return None
