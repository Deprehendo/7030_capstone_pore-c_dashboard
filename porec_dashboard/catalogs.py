"""Load demo dataset and reference genome catalogs; download to workspace cache."""

from __future__ import annotations

import gzip
import shutil
from pathlib import Path
from typing import Callable
from urllib.request import urlopen

import yaml

from .paths import PROJECT_ROOT
from .workspace import DEMO_DIR, REFERENCES_DIR, ensure_demo_dir, ensure_references_dir

PROFILES_DIR = PROJECT_ROOT / "profiles"


def _load_yaml(name: str) -> dict:
    path = PROFILES_DIR / name
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_demo_datasets() -> dict:
    return _load_yaml("demo_datasets.yaml")


def load_reference_genomes() -> dict:
    return _load_yaml("reference_genomes.yaml")


def demo_cache_path(dataset_id: str) -> Path:
    entry = load_demo_datasets()[dataset_id]
    ensure_demo_dir()
    return DEMO_DIR / entry["local_name"]


def reference_cache_path(genome_id: str) -> Path:
    entry = load_reference_genomes()[genome_id]
    ensure_references_dir()
    return REFERENCES_DIR / entry["local_name"]


def download_file(
    url: str,
    dest: Path,
    *,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Path:
    """Stream download url to dest; returns dest path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    with urlopen(url) as resp:
        total = int(resp.headers.get("Content-Length", 0) or 0)
        chunk_size = 1024 * 1024
        downloaded = 0
        with tmp.open("wb") as out:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total > 0:
                    progress_callback(min(downloaded / total, 1.0), f"{downloaded / 1e6:.1f} MB")

    tmp.replace(dest)
    if progress_callback:
        progress_callback(1.0, "Done")
    return dest


def _decompress_gzip(gz_path: Path, fa_path: Path) -> Path:
    with gzip.open(gz_path, "rb") as src, fa_path.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    return fa_path


def ensure_demo_mcool(
    dataset_id: str,
    *,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Path:
    dest = demo_cache_path(dataset_id)
    if dest.is_file():
        return dest
    entry = load_demo_datasets()[dataset_id]
    download_file(entry["url"], dest, progress_callback=progress_callback)
    return dest


def ensure_reference(
    genome_id: str,
    *,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Path:
    """Download and cache reference FASTA; decompress .gz sources once."""
    fa_path = reference_cache_path(genome_id)
    if fa_path.is_file():
        return fa_path

    entry = load_reference_genomes()[genome_id]
    url = entry["url"]
    ensure_references_dir()

    if url.endswith(".gz"):
        gz_path = fa_path.with_suffix(fa_path.suffix + ".gz")
        if not gz_path.is_file():
            download_file(url, gz_path, progress_callback=progress_callback)
        elif progress_callback:
            progress_callback(1.0, "Decompressing…")
        _decompress_gzip(gz_path, fa_path)
        return fa_path

    download_file(url, fa_path, progress_callback=progress_callback)
    return fa_path
