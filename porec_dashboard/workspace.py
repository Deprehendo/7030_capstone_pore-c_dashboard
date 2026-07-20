"""Working copies for normalized data — never overwrite the user's original mcool."""

from __future__ import annotations

import shutil
from pathlib import Path

from .paths import PROJECT_ROOT

WORKSPACE_DIR = PROJECT_ROOT / "workspace"
NORMALIZED_DIR = WORKSPACE_DIR / "normalized"
DEMO_DIR = WORKSPACE_DIR / "demo"
REFERENCES_DIR = WORKSPACE_DIR / "references"


def ensure_normalized_dir() -> Path:
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    return NORMALIZED_DIR


def ensure_demo_dir() -> Path:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    return DEMO_DIR


def ensure_references_dir() -> Path:
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    return REFERENCES_DIR


def is_under_normalized(path: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(NORMALIZED_DIR.resolve())
        return True
    except (ValueError, OSError):
        return False


def working_copy_path(source: str | Path) -> Path:
    """Destination path for a balanced working copy of `source`."""
    ensure_normalized_dir()
    src = Path(source).resolve()
    name = src.name
    if name.endswith(".mcool"):
        base = name[: -len(".mcool")]
        suffix = ".mcool"
    elif name.endswith(".cool"):
        base = name[: -len(".cool")]
        suffix = ".cool"
    else:
        base = src.stem
        suffix = ".mcool"
    if not base.endswith(".balanced"):
        base = f"{base}.balanced"
    return NORMALIZED_DIR / f"{base}{suffix}"


def ensure_working_mcool(source: str | Path, *, force_new_copy: bool = False) -> Path:
    """
    Return a writable working copy under workspace/normalized/.

    If `source` is already a normalized working file, return it as-is.
    Otherwise copy the original once (unless force_new_copy) and return the copy.
    """
    src = Path(source).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"mcool not found: {src}")

    if is_under_normalized(src) and not force_new_copy:
        return src

    dest = working_copy_path(src)
    if dest.exists() and not force_new_copy:
        return dest

    ensure_normalized_dir()
    shutil.copy2(src, dest)
    return dest


def prefer_balanced_mcool(source: str | Path) -> Path:
    """
    If a balanced working copy exists for `source`, return it.

    Keeps analysis on ICE-weighted data after Normalize without overwriting
    the user's explicit choice of a different file.
    """
    src = Path(source).resolve()
    if is_under_normalized(src):
        return src
    dest = working_copy_path(src)
    if dest.is_file():
        return dest
    return src
