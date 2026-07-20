"""Shared Streamlit UI helpers for multipage Section 2."""

from __future__ import annotations

import html
import io

import streamlit as st
import streamlit.components.v1 as components

from porec_dashboard.paths import (
    discover_fastas,
    discover_mcools,
    example_image_path,
    resolve_data_path,
)
from porec_dashboard.catalogs import (
    demo_cache_path,
    ensure_demo_mcool,
    ensure_reference,
    load_demo_datasets,
    load_reference_genomes,
    reference_cache_path,
)
from porec_dashboard.profiles import (
    preferred_view_resolution as profile_view_resolution,
    profile_for_demo,
    profile_for_reference,
    view_resolution_tip as profile_view_tip,
)
from porec_dashboard.cooler_io import analysis_chromosomes as _analysis_chromosomes
from porec_dashboard.organism_guidance import active_row_hint
from porec_dashboard.workspace import (
    DEMO_DIR,
    NORMALIZED_DIR,
    REFERENCES_DIR,
    is_under_normalized,
    prefer_balanced_mcool,
)


def fig_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


def scroll_to_top() -> None:
    """Scroll the main view to the top when opening an analysis page."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const main = doc.querySelector('section.main');
        if (main) { main.scrollTo(0, 0); }
        window.parent.scrollTo(0, 0);
        </script>
        """,
        height=0,
    )


def nav_back_hub(*, key: str) -> None:
    if st.button("← Back to Section 2 hub", key=key):
        st.switch_page("pages/1_Section_2_Analyze.py")


def analysis_card_html(title: str, blurb: str, caption: str) -> str:
    """Centered text block used inside a bordered Streamlit container."""
    t = html.escape(title)
    b = html.escape(blurb)
    c = html.escape(caption)
    return f"""
    <div style="text-align: center; padding: 0.25rem 0.4rem 0.5rem 0.4rem;">
      <h3 style="margin: 0 0 0.55rem 0; text-align: center;">{t}</h3>
      <p style="margin: 0; text-align: center; font-size: 0.95rem; line-height: 1.35;">{b}</p>
      <p style="margin: 0.65rem 0 0 0; text-align: center; font-size: 0.8rem; color: #555;">{c}</p>
    </div>
    """


def preferred_view_resolution(
    resolutions: list[int],
    *,
    prefer: int = 10_000,
    fallback: int = 25_000,
) -> int:
    """Pick a default resolution for chromosome / eigenvector / TAD viewing."""
    profile = get_active_profile()
    return profile_view_resolution(resolutions, profile, prefer=prefer, fallback=fallback)


VIEW_RES_TIP = (
    "For many Pore-C datasets, **~10 kb** is a practical default for "
    "chromosome maps, eigenvectors, and TADs when that resolution exists "
    "(axis units are bins — finer resolution means more bins). "
    "10 kb is selected by default when available."
)
YEAST_VIEW_RES_TIP = VIEW_RES_TIP


def show_view_resolution_tip() -> None:
    st.info(profile_view_tip(get_active_profile()))


def get_active_profile() -> dict | None:
    return st.session_state.get("organism_profile")


def filtered_chromosomes(
    clr,
    exclude_mito: bool,
    *,
    purpose: str = "general",
) -> list[str]:
    """Profile-aware chromosome list for analysis pages."""
    if not exclude_mito:
        return list(clr.chromnames)
    return _analysis_chromosomes(
        clr,
        exclude_mito=True,
        profile=get_active_profile(),
        purpose=purpose,
    )


def _download_progress_bar(label: str):
    progress = st.progress(0.0, text=label)
    status = st.empty()

    def callback(fraction: float, msg: str) -> None:
        progress.progress(fraction, text=f"{label}: {msg}")
        status.caption(msg)

    return callback


def _all_mcools() -> list:
    from porec_dashboard.paths import discover_files, MCOOL_GLOBS

    found = discover_mcools()
    if DEMO_DIR.is_dir():
        for p in discover_files(MCOOL_GLOBS, DEMO_DIR):
            if p.resolve() not in {x.resolve() for x in found}:
                found.append(p.resolve())
    if NORMALIZED_DIR.is_dir():
        for p in sorted(NORMALIZED_DIR.glob("*.mcool")) + sorted(NORMALIZED_DIR.glob("*.cool")):
            if p.resolve() not in {x.resolve() for x in found}:
                found.append(p.resolve())
    return found


def _all_fastas() -> list:
    from porec_dashboard.paths import discover_files, FASTA_GLOBS

    found = discover_fastas()
    if REFERENCES_DIR.is_dir():
        for p in discover_files(FASTA_GLOBS, REFERENCES_DIR):
            if p.resolve() not in {x.resolve() for x in found}:
                found.append(p.resolve())
    return found


def show_help_block(meta: dict) -> None:
    """Title, blurb, expandable how-to, and example image."""
    st.subheader(meta["title"])
    st.write(meta["blurb"])
    with st.expander("How this works (biology & method)", expanded=False):
        st.markdown(meta["how"])
    show_example(meta.get("example_stem"), meta.get("example_caption", ""))


def show_example(stem: str | None, caption: str) -> None:
    if not stem:
        return
    path = example_image_path(stem)
    st.markdown("#### Example")
    if path is not None:
        st.image(str(path), caption=caption)
    else:
        st.info(
            f"Example image not found for `{stem}`. "
            f"Add `assets/examples/{stem}.png` to show a preview here.\n\n{caption}"
        )


def render_data_sidebar() -> tuple[str | None, str | None, bool]:
    """
    Sidebar: demo catalog, mcool + reference genome selection.

    Returns (mcool_resolved_str_or_None, fasta_resolved_str_or_None, exclude_mito).
    """
    with st.sidebar:
        st.header("Data inputs")

        demos = load_demo_datasets()
        demo_ids = list(demos.keys())
        demo_labels = {did: demos[did]["display_name"] for did in demo_ids}
        demo_options = ["(local file only)"] + [demo_labels[d] for d in demo_ids]
        demo_rev = {demo_labels[d]: d for d in demo_ids}

        default_demo_idx = 0
        active_demo = st.session_state.get("active_demo_id")
        if active_demo and active_demo in demo_labels:
            label = demo_labels[active_demo]
            if label in demo_options:
                default_demo_idx = demo_options.index(label)

        st.subheader("Demo mcool (public)")
        demo_pick = st.selectbox(
            "Public dataset",
            options=demo_options,
            index=min(default_demo_idx, len(demo_options) - 1),
            help="GSE149117 human Pore-C (GRCh38). Download once — cached under workspace/demo/.",
        )

        if demo_pick != "(local file only)":
            demo_id = demo_rev[demo_pick]
            entry = demos[demo_id]
            st.caption(f"Size: {entry.get('size_hint', '?')} · {entry.get('series', '')}")
            cached = demo_cache_path(demo_id)
            if cached.is_file():
                active = prefer_balanced_mcool(cached)
                st.success(f"Cached: `{cached.name}`")
                if active != cached.resolve():
                    st.info(f"Using balanced working copy: `{active.name}`")
                st.session_state["mcool_path"] = str(active)
                st.session_state["active_demo_id"] = demo_id
                prof = profile_for_demo(entry)
                if prof:
                    st.session_state["organism_profile"] = prof
                if entry.get("reference_genome"):
                    st.session_state.setdefault("catalog_reference_id", entry["reference_genome"])
            elif st.button(f"Download {entry.get('size_hint', '')} mcool", key=f"dl_demo_{demo_id}"):
                cb = _download_progress_bar("Downloading mcool")
                path = ensure_demo_mcool(demo_id, progress_callback=cb)
                st.session_state["mcool_path"] = str(path)
                st.session_state["active_demo_id"] = demo_id
                prof = profile_for_demo(entry)
                if prof:
                    st.session_state["organism_profile"] = prof
                if entry.get("reference_genome"):
                    st.session_state["catalog_reference_id"] = entry["reference_genome"]
                st.rerun()
        else:
            st.session_state.pop("active_demo_id", None)

        st.divider()
        st.subheader("Contact matrix (.mcool)")

        mcool_found = _all_mcools()
        mcool_options = ["(type a path below)"] + [str(p) for p in mcool_found]
        default_mcool_idx = 0
        if "mcool_path" in st.session_state and st.session_state["mcool_path"]:
            current = st.session_state["mcool_path"]
            if current in mcool_options:
                default_mcool_idx = mcool_options.index(current)

        mcool_pick = st.selectbox(
            "mcool file",
            options=mcool_options,
            index=min(default_mcool_idx, len(mcool_options) - 1),
            help="Local files, workspace/demo/, and workspace/normalized/ copies.",
        )
        mcool_typed = st.text_input(
            "Or paste .mcool path",
            value=st.session_state.get("mcool_typed", ""),
        )
        st.session_state["mcool_typed"] = mcool_typed

        if mcool_typed.strip():
            mcool_raw = mcool_typed.strip()
        elif mcool_pick != "(type a path below)":
            mcool_raw = mcool_pick
        else:
            mcool_raw = st.session_state.get("mcool_path", "")

        st.divider()
        st.subheader("Reference genome (FASTA)")

        refs = load_reference_genomes()
        ref_ids = list(refs.keys())
        ref_labels = {rid: refs[rid]["display_name"] for rid in ref_ids}
        ref_options = ["(local / none)"] + [ref_labels[r] for r in ref_ids]
        ref_rev = {ref_labels[r]: r for r in ref_ids}

        default_ref_idx = 0
        catalog_ref = st.session_state.get("catalog_reference_id")
        if catalog_ref and catalog_ref in ref_labels:
            lbl = ref_labels[catalog_ref]
            if lbl in ref_options:
                default_ref_idx = ref_options.index(lbl)

        ref_pick = st.selectbox(
            "Reference catalog",
            options=ref_options,
            index=min(default_ref_idx, len(ref_options) - 1),
            help="hg38, hg19 (human), sacCer3 (yeast), mm10, mm39 (mouse). Download once — cached under workspace/references/.",
        )

        if ref_pick != "(local / none)":
            ref_id = ref_rev[ref_pick]
            entry = refs[ref_id]
            st.caption(entry.get("notes", ""))
            cached_ref = reference_cache_path(ref_id)
            if cached_ref.is_file():
                st.success(f"Cached: `{cached_ref.name}`")
                st.session_state["fasta_path"] = str(cached_ref)
                st.session_state["catalog_reference_id"] = ref_id
                prof = profile_for_reference(ref_id)
                if prof:
                    st.session_state["organism_profile"] = prof
            elif st.button(f"Download {ref_id} reference", key=f"dl_ref_{ref_id}"):
                cb = _download_progress_bar("Downloading reference")
                path = ensure_reference(ref_id, progress_callback=cb)
                st.session_state["fasta_path"] = str(path)
                st.session_state["catalog_reference_id"] = ref_id
                prof = profile_for_reference(ref_id)
                if prof:
                    st.session_state["organism_profile"] = prof
                st.rerun()

        fasta_options = ["(none / type below)"] + [str(p) for p in _all_fastas()]
        default_fasta_idx = 0
        if "fasta_path" in st.session_state and st.session_state["fasta_path"]:
            current_f = st.session_state["fasta_path"]
            if current_f in fasta_options:
                default_fasta_idx = fasta_options.index(current_f)

        fasta_pick = st.selectbox(
            "FASTA file (local)",
            options=fasta_options,
            index=min(default_fasta_idx, len(fasta_options) - 1),
        )
        fasta_typed = st.text_input(
            "Or paste FASTA path",
            value=st.session_state.get("fasta_typed", ""),
        )
        st.session_state["fasta_typed"] = fasta_typed

        if fasta_typed.strip():
            fasta_raw = fasta_typed.strip()
        elif fasta_pick != "(none / type below)":
            fasta_raw = fasta_pick
        elif ref_pick != "(local / none)" and reference_cache_path(ref_rev[ref_pick]).is_file():
            fasta_raw = str(reference_cache_path(ref_rev[ref_pick]))
        else:
            fasta_raw = st.session_state.get("fasta_path", "")

        exclude_mito = st.checkbox(
            "Exclude mitochondrial / plastid / alt contigs",
            value=st.session_state.get("exclude_mito", True),
            help="Uses organism profile rules when a reference or demo is active "
            "(e.g. drop chrM, unplaced, and random contigs for hg38).",
        )
        st.session_state["exclude_mito"] = exclude_mito

        profile = get_active_profile()
        if profile:
            st.caption(active_row_hint(profile))

        mcool_resolved, mcool_tried = resolve_data_path(mcool_raw) if mcool_raw else (None, [])
        if mcool_resolved is not None and not is_under_normalized(mcool_resolved):
            mcool_resolved = prefer_balanced_mcool(mcool_resolved)
        fasta_resolved, fasta_tried = resolve_data_path(fasta_raw) if fasta_raw else (None, [])

        if mcool_raw and mcool_resolved is None:
            st.error("mcool not found. Tried:\n" + "\n".join(f"- `{t}`" for t in mcool_tried))
        if fasta_raw and fasta_resolved is None:
            st.error("FASTA not found. Tried:\n" + "\n".join(f"- `{t}`" for t in fasta_tried))

        if mcool_resolved is not None:
            st.session_state["mcool_path"] = str(mcool_resolved)
            label = mcool_resolved.name
            if is_under_normalized(mcool_resolved):
                st.success(f"Working mcool (balanced copy): `{label}`")
            else:
                st.success(f"mcool: `{label}`")
                from porec_dashboard.cooler_io import has_weights, list_resolutions, open_cooler

                try:
                    ress = list_resolutions(str(mcool_resolved))
                    if ress:
                        c = open_cooler(str(mcool_resolved), ress[min(len(ress) // 2, len(ress) - 1)])
                        if not has_weights(c):
                            st.warning(
                                "No ICE weights in this file yet. Run **Normalize** first, "
                                "or select the `.balanced.mcool` under workspace/normalized/."
                            )
                except Exception:
                    pass
                st.caption("Normalize writes weights to workspace/normalized/*.balanced.mcool.")
        if fasta_resolved is not None and mcool_resolved is not None:
            from porec_dashboard.cooler_io import list_resolutions, open_cooler
            from porec_dashboard.genome_harmonize import fasta_mcool_compatible

            try:
                ress = list_resolutions(str(mcool_resolved))
                clr_check = open_cooler(str(mcool_resolved), ress[0])
                ok, msg = fasta_mcool_compatible(clr_check, fasta_resolved)
                if not ok:
                    st.error(msg)
                elif msg:
                    st.warning(msg)
            except Exception:
                pass
        if fasta_resolved is not None:
            st.session_state["fasta_path"] = str(fasta_resolved)
            st.success(f"FASTA: `{fasta_resolved.name}`")
        elif not fasta_raw:
            st.session_state.pop("fasta_path", None)

        return (
            str(mcool_resolved) if mcool_resolved else None,
            str(fasta_resolved) if fasta_resolved else None,
            exclude_mito,
        )


def require_mcool() -> tuple[str, bool]:
    """Sidebar + require mcool; stop page if missing. Returns (mcool_path, exclude_mito)."""
    mcool, _fasta, exclude = render_data_sidebar()
    if not mcool:
        st.warning("Select or paste a valid `.mcool` path in the sidebar to run this analysis.")
        st.stop()
    return mcool, exclude


def get_fasta_or_warn() -> str | None:
    return st.session_state.get("fasta_path")
