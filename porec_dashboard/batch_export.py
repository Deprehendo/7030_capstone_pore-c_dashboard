"""Batch figure export helpers (ZIP + progress-friendly loops)."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable, Iterable, Sequence
from typing import Any


def png_zip_bytes(named_pngs: Sequence[tuple[str, bytes]]) -> bytes:
    """Build an in-memory ZIP from (filename, png_bytes) pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in named_pngs:
            zf.writestr(name, data)
    buf.seek(0)
    return buf.getvalue()


def zip_bytes_with_extra(
    named_pngs: Sequence[tuple[str, bytes]],
    extras: Sequence[tuple[str, bytes]] | None = None,
) -> bytes:
    """ZIP of PNGs plus optional extra files (e.g. CSV)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in named_pngs:
            zf.writestr(name, data)
        if extras:
            for name, data in extras:
                zf.writestr(name, data)
    buf.seek(0)
    return buf.getvalue()
