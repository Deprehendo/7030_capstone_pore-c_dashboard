"""Session-scoped cache for expensive cooltools results."""

from __future__ import annotations

import hashlib
import json

import streamlit as st


def _stable_key(parts: tuple) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached(prefix: str, *parts) -> object | None:
    return st.session_state.get(f"{prefix}_{_stable_key(parts)}")


def set_cached(prefix: str, value: object, *parts) -> None:
    st.session_state[f"{prefix}_{_stable_key(parts)}"] = value
