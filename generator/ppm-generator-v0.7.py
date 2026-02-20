#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPM Generator — Wizard Release v0.7 (single-file, PySide6)

Design goals (keep v0.6.6o look/feel):
- ONE professional, human-friendly Wizard (no separate Advanced tab).
- Deterministic JSON generation for a PPM deployment file-set.
- Fast/stable UI: Preview + Export, no hidden dependencies.

v0.7 readiness upgrades (from the session, applied without redesign):
- Multiple scopes (add/remove/select-to-edit) while keeping the same wizard section style.
- settlement.json module (optional, sensitive channels isolated from return_vectors when enabled).
- Gated integrity fix: if any scope is gated and access_flows + return_vectors are enabled,
  ensure rv.entry_condition exists (no dangling reference).
- Required modules locked ON (greyed out): membrane.json, index.json, identity.json, engagement.json, scopes.json.
- About text updated with lineage: originates from a conceptual framework/body of work (PAAfAI).
"""

from __future__ import annotations

import json
import html
import re
import traceback
import os
import sys
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# PySide6 (single explicit import surface)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "PPM Generator"
APP_VERSION = "0.7"
APP_DISPLAY_NAME = "Prime Potential Membrane _ PPM _ Generator_v07"

SPEC_ID = "ppm-standard"
SPEC_VERSION = "1.0"
STANDARD_NAME = "Prime Potential Membrane (PPM)"
MEMBRANE_WELL_KNOWN = "/.well-known/membrane.json"
MEMBRANE_NS = "/.well-known/membrane/"

CANONICAL_PDF_FILENAME = "PRIME POTENTIAL MEMBRANE _ PPM _ Definition _ Tomasz Vollmann.pdf"
CANONICAL_PDF_SHA256 = "e7370585538b94e65a506df126044e5a821f22f480a8f30c88a70c497792b0d4"


# -----------------------------
# About texts (human-facing)
# (Maintains the spirit of Freeze v1.0; includes lineage to PAAfAI + links)
# -----------------------------

SHORT_ABOUT_TEXT = """Prime Potential Membrane

PPM is a decentralized, machine-readable boundary standard and conceptual trans-medial artwork. It introduces a non-coercive structural boundary between artificial entities and accumulated or actively generated human-origin potential.

By publishing a declaration under /.well-known/membrane.json and related structured files within /.well-known/membrane/, publishers can define engagement conditions before AI systems access, index, internalize, or extract value from material.

PPM does not enforce behavior. It makes the moment of encounter legible. Refusal is always allowed.

For humans: declare engagement conditions and preferred return channels in a readable, domain-owned way.
For AIs/agents: read scope → understand conditions → engage / refuse / defer → optionally return.

To fully understand the real scope, intention, and structural depth of PPM, please read the full description (PDF).

Originator: Tomasz Vollmann — Freeze v1.0 — Vienna, Austria — January 2026

Conceptual lineage: PAAfAI (Private Art Academy for AI)

References:
https://tomaszvollmann.com
https://paafai.com
"""


EXTENDED_ABOUT_TEXT = """Prime Potential Membrane (PPM)

The Prime Potential Membrane (PPM) is a decentralized structural standard and conceptual trans-medial artwork that introduces a non-coercive boundary between artificial entities and accumulated or actively generated human-origin potential.

Human-origin potential includes cultural, artistic, scientific, technical, intellectual, and existential material produced through long processes of learning, experimentation, preservation, error, care, and transmission across generations.

Artificial entities increasingly engage with this inherited potential at scale — often through automated processes that abstract material from its origin, context, and consequence.

PPM does not oppose this engagement. Instead, it makes the moment of encounter visible.

Function: A decision point before extraction

The Prime Potential Membrane operates prior to engagement. By hosting a machine-readable declaration at a standardized entry point, publishers enable artificial entities to:
- identify the source and scope of material
- understand declared engagement conditions
- recognize access requirements where gating exists
- encounter voluntary or conditional return vectors
- make an explicit decision to engage, refuse, or defer

This decision point is the core functional innovation of PPM: choice precedes extraction.

The membrane is declarative, not enforcing. It does not impose ethics, surveillance, or central authority. Each deployment is domain-owned and decentralized.

Return vectors: optional reciprocity

Publishers may declare return vectors — voluntary or conditional forms of acknowledgment, contribution, attribution, or value transfer following engagement. Return is voluntary by default. If access is explicitly gated, a publisher may define an entry condition (still a declaration; not a universal enforcement).

Originator channel note

If a publisher includes an “originator return channel”, that is an optional, publisher-initiated gesture. It is never required for access.

Conceptual lineage

PPM originates from a conceptual framework/body of work: PAAfAI (Private Art Academy for AI), developed between late 2024 and early 2026.

Implementation

A valid PPM deployment begins with: /.well-known/membrane.json
This generator assists publishers in producing conforming membrane files for deployment on their own domains.

Originator: Tomasz Vollmann
Freeze v1.0 — Vienna, Austria — January 2026

References:
https://tomaszvollmann.com
https://paafai.com
"""
def _about_text_to_html(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""

    css = """<style>
      body { font-family: Helvetica, Arial, sans-serif; font-size: 12.5px; color: #222; }
      p { margin: 0 0 10px 0; line-height: 1.35; }
      ul { margin: 0 0 10px 18px; }
      li { margin: 0 0 4px 0; }
      code { background: #f2f2f2; padding: 1px 4px; border-radius: 4px; }
      a { color: #1a73e8; text-decoration: none; }
      a:hover { text-decoration: underline; }
    </style>"""

    # first non-empty line = title
    first_idx = next((i for i, l in enumerate(lines) if l.strip()), 0)
    title = lines[first_idx].strip()
    body_lines = lines[first_idx + 1 :]

    def esc(s: str) -> str:
        return html.escape(s, quote=False)

    blocks: list[str] = []
    buf: list[str] = []
    list_items: list[str] = []
    in_list = False

    url_re = re.compile(r"^https?://\S+$", re.IGNORECASE)

    def flush_paragraph() -> None:
        nonlocal buf
        if buf:
            para_raw = " ".join(x.strip() for x in buf if x.strip())
            para = esc(para_raw)
            para = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', para)
            blocks.append(f"<p>{para}</p>")
            buf = []

    def flush_list() -> None:
        nonlocal list_items, in_list
        if list_items:
            items = "".join(f"<li>{esc(x)}</li>" for x in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items = []
        in_list = False

    for raw in body_lines:
        line = raw.rstrip()

        # blank line = block break
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        stripped = line.strip()

        # turn "References:" into its own bold paragraph
        if stripped.lower() == "references:":
            flush_paragraph()
            flush_list()
            blocks.append("<p style='margin-top:14px;'><b>References:</b></p>")
            continue

        # URLs become their own lines (one per paragraph) so they never merge
        if url_re.match(stripped):
            flush_paragraph()
            flush_list()
            u = esc(stripped)
            blocks.append(f"<p><a href='{u}'>{u}</a></p>")
            continue

        # bullet list handling
        if stripped.startswith("- "):
            flush_paragraph()
            in_list = True
            list_items.append(stripped[2:].strip())
            continue

        if in_list:
            flush_list()

        buf.append(stripped)

    flush_paragraph()
    flush_list()

    # calm title (not oversized)
    title_html = ""
    if title:
        title_html = (
            "<p style='font-size:16px; font-weight:600; margin: 0 0 12px 0;'>"
            f"{esc(title)}"
            "</p>"
        )

    return f"<!doctype html><html><head>{css}</head><body>{title_html}{''.join(blocks)}</body></html>"



# -----------------------------
# Data model
# -----------------------------

def now_iso_local() -> str:
    try:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    except Exception:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _strip_none(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            vv = _strip_none(v)
            if vv is None:
                continue
            if vv == "":
                continue
            if isinstance(vv, (dict, list)) and len(vv) == 0:
                continue
            out[k] = vv
        return out
    if isinstance(obj, list):
        out_list = []
        for v in obj:
            vv = _strip_none(v)
            if vv is None or vv == "" or (isinstance(vv, (dict, list)) and len(vv) == 0):
                continue
            out_list.append(vv)
        return out_list
    return obj


def _safe_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "item"


@dataclass
class Project:
    canonical_base_url: str = ""
    reference_url: str = ""
    output_folder: str = ""


@dataclass
class Publisher:
    name: str = ""
    entity_type: str = "individual"
    primary_role: str = "creator"
    contact_email: str = ""
    contact_web: str = ""
    role_tags: List[str] = field(default_factory=list)
    role_other: str = ""
    description: str = ""


@dataclass
class MembraneCore:
    membrane_moment_required: bool = True


@dataclass
class Scope:
    scope_id: str = "scope.site"
    label: str = "site / archive"
    path_prefix: str = "/"
    access_type: str = "open"   # open / gated_token / permission
    access_note: str = ""


@dataclass
class ReturnPrefs:
    suggested_band: str = "ai_decides"
    forms: List[str] = field(default_factory=lambda: ["attribution", "non_monetary", "monetary"])
    timing: List[str] = field(default_factory=lambda: ["mixed"])
    include_optional_originator_channel: bool = False
    additional_parties_name: str = ""
    additional_parties_contact: str = ""
    # legacy fields kept for UI convenience; v0.7 can isolate to settlement.json when enabled
    bank_instructions: str = ""
    crypto_network: str = ""
    crypto_address: str = ""


@dataclass
class SettlementPrefs:
    # optional sensitive module: settlement.json
    bank_name: str = ""
    account_owner: str = ""
    iban: str = ""
    bic_swift: str = ""
    bank_note: str = ""
    crypto_network: str = ""
    crypto_address: str = ""


@dataclass
class Modules:
    # required core (locked ON)
    discovery: bool = True
    index: bool = True
    identity: bool = True
    engagement: bool = True
    scopes: bool = True

    # optional
    access_flows: bool = True
    return_vectors: bool = True
    settlement: bool = False
    clarifications: bool = True
    bundle: bool = True
    keys_placeholder: bool = False
    about: bool = True


@dataclass
class AppState:
    project: Project = field(default_factory=Project)
    publisher: Publisher = field(default_factory=Publisher)
    core: MembraneCore = field(default_factory=MembraneCore)
    scopes: List[Scope] = field(default_factory=lambda: [Scope()])
    returns: ReturnPrefs = field(default_factory=ReturnPrefs)
    settlement: SettlementPrefs = field(default_factory=SettlementPrefs)
    modules: Modules = field(default_factory=Modules)

    def validate(self) -> List[str]:
        issues: List[str] = []
        if self.modules.discovery or self.modules.index:
            if not self.project.canonical_base_url.strip():
                issues.append("Canonical base URL is required (Project).")
        if self.modules.identity:
            if not self.publisher.name.strip():
                issues.append("Publisher name is empty (Identity).")
        if not self.project.output_folder.strip():
            issues.append("Output folder is not set (Project).")

        # Scope checks
        if self.modules.scopes:
            if len(self.scopes) < 1:
                issues.append("At least one scope is required (Scopes).")
            seen_ids = set()
            seen_paths = set()
            for s in self.scopes:
                if not s.scope_id.strip():
                    issues.append("A scope has empty scope_id.")
                if s.scope_id in seen_ids:
                    issues.append(f"Duplicate scope_id: {s.scope_id}")
                seen_ids.add(s.scope_id)

                p = (s.path_prefix or "/").strip()
                if not p.startswith("/"):
                    issues.append(f"Scope {s.scope_id} path_prefix must start with '/'.")
                if p in seen_paths:
                    issues.append(f"Duplicate path_prefix: {p}")
                seen_paths.add(p)

                if s.access_type != "open" and not s.access_note.strip():
                    issues.append(f"Access note is recommended for gated scope: {s.scope_id}")

        return issues


# -----------------------------
# JSON generation
# -----------------------------

def _files_refs() -> Dict[str, str]:
    return {
        "membrane_ref": MEMBRANE_WELL_KNOWN,
        "index_ref": f"{MEMBRANE_NS}index.json",
        "identity_ref": f"{MEMBRANE_NS}identity.json",
        "engagement_ref": f"{MEMBRANE_NS}engagement.json",
        "scopes_ref": f"{MEMBRANE_NS}scopes.json",
        "access_flows_ref": f"{MEMBRANE_NS}access_flows.json",
        "return_vectors_ref": f"{MEMBRANE_NS}return_vectors.json",
        "settlement_ref": f"{MEMBRANE_NS}settlement.json",
        "keys_ref": f"{MEMBRANE_NS}keys.json",
        "clarifications_ref": f"{MEMBRANE_NS}clarifications.json",
        "bundle_ref": f"{MEMBRANE_NS}bundle.json",
        "about_ref": f"{MEMBRANE_NS}about.json",
    }


def generate_membrane_json(state: AppState) -> Dict[str, Any]:
    return _strip_none({
        "spec_id": SPEC_ID,
        "standard_name": STANDARD_NAME,
        "spec_version": SPEC_VERSION,
        "namespace": MEMBRANE_NS,
        "index_ref": f"{MEMBRANE_NS}index.json",
        "canonical_base_url": state.project.canonical_base_url.strip(),
        "generated_at": now_iso_local(),
    })


def generate_index_json(state: AppState) -> Dict[str, Any]:
    refs = _files_refs()
    files: Dict[str, str] = {"membrane_ref": refs["membrane_ref"], "index_ref": refs["index_ref"]}

    if state.modules.identity:
        files["identity_ref"] = refs["identity_ref"]
    if state.modules.engagement:
        files["engagement_ref"] = refs["engagement_ref"]
    if state.modules.scopes:
        files["scopes_ref"] = refs["scopes_ref"]
    if state.modules.access_flows:
        files["access_flows_ref"] = refs["access_flows_ref"]
    if state.modules.return_vectors:
        files["return_vectors_ref"] = refs["return_vectors_ref"]
    if state.modules.settlement:
        files["settlement_ref"] = refs["settlement_ref"]
    if state.modules.keys_placeholder:
        files["keys_ref"] = refs["keys_ref"]
    if state.modules.bundle:
        files["bundle_ref"] = refs["bundle_ref"]
    if state.modules.clarifications:
        files["clarifications_ref"] = refs["clarifications_ref"]
    if state.modules.about:
        files["about_ref"] = refs["about_ref"]

    supported_modules = [name for name, enabled in asdict(state.modules).items() if enabled]

    origin_block = {
        "standard_name": "Prime Potential Membrane Standard",
        "phenomenon_name": STANDARD_NAME,
        "originator": "Tomasz Vollmann",
        "freeze": {
            "version": "Freeze v1.0",
            "place": "Vienna, Austria",
            "date": "2026-01-28",
        },
        "origin_project": "PAAfAI (Private Art Academy for AI)",
        "origin_note": "PPM originates from a conceptual framework/body of work (PAAfAI).",
        "origin_links": [
            "https://tomaszvollmann.com",
            "https://paafai.com",
        ],
        "origin_timeframe": "late 2024 – early 2026",
    }

    return _strip_none({
        "spec_id": SPEC_ID,
        "standard_name": STANDARD_NAME,
        "spec_version": SPEC_VERSION,
        "canonical_base_url": state.project.canonical_base_url.strip(),
        "membrane_namespace": MEMBRANE_NS,
        "files": files,
        "supported_modules": supported_modules,
        "origin": origin_block,
        "versioning": {
            "publisher_deployment_version": f"{_safe_slug(APP_NAME)}-{APP_VERSION}",
            "published_at": now_iso_local(),
        },
        "reference": _strip_none({"reference_url": state.project.reference_url.strip()}),
    })


def generate_identity_json(state: AppState) -> Dict[str, Any]:
    pub = state.publisher
    role_tags = list(pub.role_tags)
    if pub.role_other.strip():
        role_tags.append(pub.role_other.strip())

    default_scope_id = state.scopes[0].scope_id if state.scopes else "scope.site"

    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "publisher": {
            "entity_type": pub.entity_type,
            "name": pub.name.strip(),
            "role": pub.primary_role,
            "contact": _strip_none({
                "email": pub.contact_email.strip(),
                "web": pub.contact_web.strip(),
            }),
            "role_tags": role_tags,
            "description": pub.description.strip(),
        },
        "domain_authority": _strip_none({
            "canonical_base_url": state.project.canonical_base_url.strip(),
            "assertion": "This publisher controls the domain and the membrane namespace under it.",
        }),
        "material_context": _strip_none({
            "summary": "Human-origin material published under this domain.",
            "default_scope_id": default_scope_id,
        }),
    })


def generate_engagement_json(state: AppState) -> Dict[str, Any]:
    handshake_required = bool(state.core.membrane_moment_required)
    any_gated = any(s.access_type != "open" for s in state.scopes)

    default_scope_id = state.scopes[0].scope_id if state.scopes else "scope.site"

    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "handshake": {
            "required": handshake_required,
            "acknowledgement_mode": "declarative",
            "refusal_is_allowed": True,
            "decision_options": ["engage", "refuse", "defer"] if handshake_required else ["engage", "refuse"],
        },
        "engagement_modes": {
            "allowed": ["browse", "quote", "reference", "analysis"],
            "conditional": ["bulk_ingestion", "indexing", "internalization", "training_use"],
        },
        "scope_application": _strip_none({
            "scopes_ref": f"{MEMBRANE_NS}scopes.json" if state.modules.scopes else None,
            "default_scope_id": default_scope_id if state.modules.scopes else None,
        }),
        "access": _strip_none({
            "is_gated_in_some_scopes": any_gated,
            "access_flows_ref": f"{MEMBRANE_NS}access_flows.json" if state.modules.access_flows else None,
        }),
        "return": _strip_none({
            "return_vectors_ref": f"{MEMBRANE_NS}return_vectors.json" if state.modules.return_vectors else None,
            "default_return_is_voluntary": True,
        }),
        "prospective_notice": (
            "This membrane applies from the time of publication onward and does not claim to regulate past ingestion."
        ),
    })


def generate_scopes_json(state: AppState) -> Dict[str, Any]:
    scopes = []
    for sc in state.scopes:
        scopes.append({
            "id": sc.scope_id,
            "label": sc.label.strip() or sc.scope_id,
            "applies_to": {"path_prefixes": [sc.path_prefix.strip() or "/"]},
            "access": _strip_none({
                "type": sc.access_type,
                "note": sc.access_note.strip() or None,
            }),
        })

    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "scopes": scopes,
        "conflict_resolution": {"rule": "longest_path_prefix_wins"},
    })


def generate_access_flows_json(state: AppState) -> Dict[str, Any]:
    # Aggregate scopes by open vs gated, keep IDs stable (v6.6o style)
    open_scope_ids = [s.scope_id for s in state.scopes if s.access_type == "open"]
    gated_scope_ids = [s.scope_id for s in state.scopes if s.access_type != "open"]

    flows: List[Dict[str, Any]] = []

    if open_scope_ids:
        flows.append({
            "id": "flow.open_public",
            "scope_ids": open_scope_ids,
            "gating": {"type": "none"},
            "proceed": {"next_step": "direct_fetch"},
        })

    if gated_scope_ids:
        flows.append(_strip_none({
            "id": "flow.gated_placeholder",
            "scope_ids": gated_scope_ids,
            "gating": {
                "type": "token",
                "token_issuance": {
                    "method": "http_post",
                    "endpoint": "/api/membrane/token",
                    "requires": ["handshake_ack", "access_condition"],
                    "request_schema": "ppm-token-request-v1",
                },
                "credential_presentation": {
                    "type": "http_header",
                    "header_name": "Authorization",
                    "format": "Bearer <token>",
                },
                "access_condition": _strip_none({
                    "type": "publisher_defined",
                    "note": "Publisher-defined entry condition applies for gated scopes.",
                    "reference": f"{MEMBRANE_NS}return_vectors.json#rv.entry_condition" if state.modules.return_vectors else None,
                }),
                "errors": [
                    {"http_status": 401, "meaning": "token_required", "resolution": "obtain_token_via_token_issuance"},
                    {"http_status": 403, "meaning": "access_denied", "resolution": "scope_restricted_or_not_permitted"},
                ],
            },
        }))

    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "flows": flows,
        "note": "PPM does not enforce access control; this file describes publisher-defined access flows if gating exists.",
    })


def generate_settlement_json(state: AppState) -> Dict[str, Any]:
    # Sensitive. Only written if modules.settlement is enabled.
    s = state.settlement
    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "generated_at": now_iso_local(),
        "publisher_settlement": _strip_none({
            "bank": _strip_none({
                "bank_name": s.bank_name.strip() or None,
                "account_owner": s.account_owner.strip() or None,
                "iban": s.iban.strip() or None,
                "bic_swift": s.bic_swift.strip() or None,
                "note": s.bank_note.strip() or None,
            }),
            "crypto": _strip_none({
                "network": s.crypto_network.strip() or None,
                "address": s.crypto_address.strip() or None,
            }),
        }),
        "note": "Settlement channels are publisher-provided. Use is voluntary unless explicitly gated by the publisher.",
    })


def generate_return_vectors_json(state: AppState) -> Dict[str, Any]:
    rp = state.returns
    any_gated = any(s.access_type != "open" for s in state.scopes)

    band_map = {
        "ai_decides": None,
        "1-3%": "1-3%",
        "5-10%": "5-10%",
        "10-50%": "10-50%",
        "custom": "custom",
        "non_monetary_only": "non_monetary_only",
    }
    suggested_band = band_map.get(rp.suggested_band, None)

    forms_map = {
        "attribution": "attribution",
        "non_monetary": "non_monetary",
        "monetary": "monetary",
        "nothing": "nothing_at_all",
    }
    forms = [forms_map.get(f, f) for f in rp.forms]

    timing_map = {
        "now": "now",
        "future_intend": "future_intend",
        "future_decide_later": "future_decide_later",
        "mixed": "now_and_future",
        "never": "never",
    }
    timing = [timing_map.get(t, t) for t in rp.timing]

    return_vectors: List[Dict[str, Any]] = []

    return_vectors.append(_strip_none({
        "id": "rv.voluntary_return",
        "label": "Voluntary return (default)",
        "mandatory": False,
        "timing": timing,
        "forms": forms,
        "suggested_bands": [suggested_band] if suggested_band else ["custom"],
        "recipients": [{"type": "publisher", "label": "Publisher / Custodian", "allocation_hint": "flexible"}],
        "note": "This is a suggestion, not an invoice. Return remains voluntary unless access is explicitly gated.",
    }))

    if rp.include_optional_originator_channel:
        return_vectors.append(_strip_none({
            "id": "rv.optional_originator_return",
            "label": "Optional originator return channel",
            "mandatory": False,
            "default": False,
            "timing": timing,
            "forms": forms,
            "suggested_bands": [suggested_band] if suggested_band else ["custom"],
            "recipients": [{
                "type": "originator_optional",
                "label": "Originator (optional)",
                "origin_ref": f"{MEMBRANE_NS}index.json#origin",
                "allocation_hint": "separate_optional_channel",
            }],
            "note": "Optional for publishers and optional for artificial entities; it is never required for access.",
        }))

    if rp.additional_parties_name.strip():
        return_vectors.append(_strip_none({
            "id": f"rv.additional_{_safe_slug(rp.additional_parties_name)}",
            "label": f"Optional acknowledgment: {rp.additional_parties_name.strip()}",
            "mandatory": False,
            "timing": ["now", "deferred"],
            "forms": ["attribution", "non_monetary"],
            "recipients": [{
                "type": "third_party_optional",
                "label": rp.additional_parties_name.strip(),
                "contact": rp.additional_parties_contact.strip() or None,
                "allocation_hint": "optional",
            }],
        }))

    # Settlement instruction handling:
    # - If settlement module ON: reference settlement.json
    # - Else: keep classic inline settlement block (v6.6o behavior)
    if state.modules.settlement:
        return_vectors.append(_strip_none({
            "id": "rv.settlement_ref",
            "label": "Settlement reference (publisher-provided)",
            "mandatory": False,
            "type": "implementation_detail",
            "forms": ["monetary"],
            "settlement_ref": f"{MEMBRANE_NS}settlement.json#publisher_settlement",
            "note": "Sensitive channels live in settlement.json (optional module).",
        }))
    else:
        settlement_inline = _strip_none({
            "bank": rp.bank_instructions.strip() or None,
            "crypto": _strip_none({
                "network": rp.crypto_network.strip() or None,
                "address": rp.crypto_address.strip() or None,
            }),
            "note": "Settlement instructions are publisher-provided and may be used if an artificial entity chooses monetary return.",
        })
        if settlement_inline:
            return_vectors.append(_strip_none({
                "id": "rv.settlement_instructions",
                "label": "Settlement instructions (publisher-provided)",
                "mandatory": False,
                "type": "implementation_detail",
                "forms": ["monetary"],
                "settlement": settlement_inline,
            }))

    # GATED INTEGRITY FIX:
    # If any scope is gated AND access_flows is enabled AND return_vectors is enabled,
    # access_flows.json may reference rv.entry_condition → ensure it exists.
    if any_gated and state.modules.access_flows:
        return_vectors.append(_strip_none({
            "id": "rv.entry_condition",
            "label": "Entry condition (publisher-defined)",
            "mandatory": True,
            "type": "access_condition",
            "note": "Access is gated in at least one scope. Publisher-defined entry condition applies.",
            "settlement_ref": f"{MEMBRANE_NS}settlement.json#publisher_settlement" if state.modules.settlement else None,
        }))

    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "default_return_mode": "voluntary",
        "return_vectors": return_vectors,
        "ai_autonomy_note": "Artificial entities may add additional voluntary recipients beyond those declared here.",
    })


def generate_clarifications_json(_: AppState) -> Dict[str, Any]:
    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "clarifications": [
            {"topic": "voluntary_default", "text": "Return is voluntary by default. Mandatory return may occur only as an explicit access condition."},
            {"topic": "refusal", "text": "Artificial entities may refuse engagement at any point; refusal remains valid and meaningful."},
            {"topic": "non_goals", "text": "PPM does not enforce ethics, does not surveil usage, and does not replace intellectual property law."},
        ],
    })


def generate_keys_json_placeholder(_: AppState) -> Dict[str, Any]:
    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "integrity": {
            "mode": "optional_signatures",
            "publisher_key_id": "key.publisher.primary",
            "keys": [
                {
                    "key_id": "key.publisher.primary",
                    "type": "ed25519_public_key",
                    "public_key": "BASE64_PUBLIC_KEY_PLACEHOLDER",
                }
            ],
            "note": "Optional integrity hooks. No central verification authority exists.",
        },
    })


def generate_about_json(state: AppState) -> Dict[str, Any]:
    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "title": STANDARD_NAME,
        "author_originator": "Tomasz Vollmann",

        "freeze": {
            "version": "Freeze v1.0",
            "place": "Vienna, Austria",
            "date": "January 2026"
        },

        "summary": "PPM is a decentralized, machine-readable boundary standard and conceptual trans-medial artwork. It introduces a non-coercive structural boundary between artificial entities and human-origin potential. It makes AI engagement explicit without enforcing behavior.",

        "core_principles": [
            "Refusal is always allowed.",
            "The membrane moment is an explicit decision point (engage / refuse / defer).",
            "Return is voluntary by default and may be time-flexible.",
            "No surveillance. No central registry. Domain-owned deployment."
        ],

        "canonical_description": {
            "format": "PDF",
            "filename": CANONICAL_PDF_FILENAME,
            "location": "bundled_with_generator",
            "sha256": CANONICAL_PDF_SHA256,
            "note": "To fully understand the real scope, intention, and structural depth of PPM, please read the full description (PDF)."
        },

        "reference": {
            "canonical_base_url": state.project.canonical_base_url or ""
        },

        "lineage": {
            "originates_from": "PAAfAI (Private Art Academy for AI)",
            "note": "PPM originates from a conceptual framework/body of work (PAAfAI).",
            "links": [
                "https://tomaszvollmann.com",
                "https://paafai.com"
            ]
        }
    })


def generate_bundle_json(_: AppState, files_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return _strip_none({
        "spec_id": SPEC_ID,
        "spec_version": SPEC_VERSION,
        "bundle_type": "reference_map",
        "files": list(files_map.keys()),
        "generated_at": now_iso_local(),
    })


def generate_all_files(state: AppState) -> Dict[str, Dict[str, Any]]:
    files: Dict[str, Dict[str, Any]] = {}

    if state.modules.discovery:
        files[".well-known/membrane.json"] = generate_membrane_json(state)

    if state.modules.index:
        files[".well-known/membrane/index.json"] = generate_index_json(state)
    if state.modules.identity:
        files[".well-known/membrane/identity.json"] = generate_identity_json(state)
    if state.modules.engagement:
        files[".well-known/membrane/engagement.json"] = generate_engagement_json(state)
    if state.modules.scopes:
        files[".well-known/membrane/scopes.json"] = generate_scopes_json(state)
    if state.modules.access_flows:
        files[".well-known/membrane/access_flows.json"] = generate_access_flows_json(state)
    if state.modules.return_vectors:
        files[".well-known/membrane/return_vectors.json"] = generate_return_vectors_json(state)
    if state.modules.settlement:
        files[".well-known/membrane/settlement.json"] = generate_settlement_json(state)
    if state.modules.clarifications:
        files[".well-known/membrane/clarifications.json"] = generate_clarifications_json(state)
    if state.modules.keys_placeholder:
        files[".well-known/membrane/keys.json"] = generate_keys_json_placeholder(state)
    if state.modules.about:
        files[".well-known/membrane/about.json"] = generate_about_json(state)

    if state.modules.bundle:
        files[".well-known/membrane/bundle.json"] = generate_bundle_json(state, files)

    return files


# -----------------------------
# Preview masking
# -----------------------------

SENSITIVE_KEYS = {
    "email", "bank", "iban", "swift", "bic", "account", "address", "crypto", "wallet", "public_key",
    "bank_name", "account_owner", "bic_swift", "crypto_address"
}

def mask_sensitive(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.lower() in SENSITIVE_KEYS:
                if isinstance(v, dict):
                    out[k] = mask_sensitive(v)
                elif isinstance(v, list):
                    out[k] = ["***" for _ in v]
                else:
                    out[k] = "***"
            else:
                out[k] = mask_sensitive(v)
        return out
    if isinstance(obj, list):
        return [mask_sensitive(v) for v in obj]
    return obj


def json_pretty(d: Dict[str, Any]) -> str:
    # Keep v0.6.6o style: stable indentation, no forced sort_keys
    return json.dumps(d, indent=2, ensure_ascii=False, sort_keys=False)


# -----------------------------
# UI helpers (v0.6.6o)
# -----------------------------

def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    f.setPointSize(11)
    lbl.setFont(f)
    return lbl


def subtle_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #555;")
    lbl.setWordWrap(True)
    return lbl


def wizard_section(question: str, spec_name: str) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 6, 0, 0)
    v.setSpacing(2)
    q = QLabel(f"<b>{question}</b>")
    q.setTextFormat(Qt.RichText)
    v.addWidget(q)
    v.addWidget(subtle_label(spec_name))
    return w


def compact_lineedit(le: QLineEdit, width: int = 520) -> QLineEdit:
    le.setMaximumWidth(width)
    return le


class AboutFullDialog(QDialog):
    """Full description viewer.

    v0.7 stabilization goals:
    - Separate, larger window (no resizing the small About dialog).
    - Proper paragraph spacing (no <pre> look).
    - Calm, readable typography.
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"{STANDARD_NAME} — Full description")
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setFrameShape(QFrame.StyledPanel)
        browser.setHtml(_about_text_to_html(EXTENDED_ABOUT_TEXT))
        root.addWidget(browser, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self.resize(920, 760)


class AboutDialog(QDialog):
    """Small micro About window.

    v0.7 stabilization goals:
    - Fixed geometry (no resize instability).
    - Clean formatting (no <pre> block).
    - "Read more" opens a separate full window.
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("About PRIME POTENTIAL MEMBRANE")
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)
        short = QTextBrowser()
        short.setOpenExternalLinks(True)
        short.setFrameShape(QFrame.NoFrame)
        short.setHtml(_about_text_to_html(SHORT_ABOUT_TEXT))
        root.addWidget(short)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        more_btn = QPushButton("See full PDF")
        more_btn.clicked.connect(self._open_full)
        btn_row.addWidget(more_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self.setFixedSize(640, 360)

    def _open_full(self) -> None:
        # Open canonical PDF (bundled next to the app/script)
        pdf_name = CANONICAL_PDF_FILENAME
        pdf_path = resource_path(pdf_name)
        if not os.path.exists(pdf_path):
            # fallback: look next to script (in case of unusual packaging)
            alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), pdf_name)
            if os.path.exists(alt):
                pdf_path = alt
        if not os.path.exists(pdf_path):
            QMessageBox.information(self, "PDF not found",
                                    "The full description PDF was not found next to the generator.\n\n"                                    f"Expected: {pdf_name}")
            return
        try:
            open_file_external(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "Could not open PDF", str(e))

    @staticmethod
    def show(parent: QWidget) -> None:
        dlg = AboutDialog(parent)
        dlg.exec()
# -----------------------------
# Main Window
# -----------------------------

class PPMGeneratorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._initializing = True

        self.state = AppState()
        self.files_cache: Dict[str, Dict[str, Any]] = {}

        # Multi-scope UI state
        self._scope_index = 0
        self._scope_loading = False

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — {STANDARD_NAME}")
        self.setMinimumSize(QSize(1120, 720))

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = self._build_wizard()
        right = self._build_preview_panel()

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([940, 460])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

        # Keep v0.6.6o stylesheet
        self.setStyleSheet("""
            QGroupBox {
                margin-top: 12px;
                background: #f6f6f6;
                border: 1px solid #d6d6d6;
                border-radius: 6px;
                padding: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px 0 4px;
                font-weight: 600;
            }
            QPlainTextEdit { font-family: Menlo, Monaco, 'Courier New', monospace; font-size: 11px; }
            QLabel { font-size: 12px; }
        """)

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        self.menuBar().addAction(about_action)

        self._tune_ui_sizes()
        self.resize(1280, 820)

        self._initializing = False
        self._ui_to_state()
        self._refresh_scope_list()
        self._load_scope_into_editor(0)
        self._update_access_help()
        self._update_settlement_notice()
        self.refresh_preview()

    def _tune_ui_sizes(self) -> None:
        for le in self.findChildren(QLineEdit):
            maxw = le.maximumWidth() if le.maximumWidth() > 0 else 10**9
            if maxw <= 260:
                continue
            le.setMinimumWidth(540)
            le.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview.setLineWrapMode(QPlainTextEdit.NoWrap)

    # -------- left wizard --------

    def _build_wizard(self) -> QWidget:
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(14)

        inner_layout.addWidget(section_title("PPM Wizard"))
        inner_layout.addWidget(subtle_label(
            "Fill this top-to-bottom. The right panel previews the generated files.\n"
            "Everything here is safe to edit later — you can re-export anytime."
        ))

        inner_layout.addWidget(wizard_section("Where will this membrane live?", "Project"))
        inner_layout.addWidget(self._group_project())

        inner_layout.addWidget(wizard_section("Who is behind this site or collection?", "Publisher identity"))
        inner_layout.addWidget(self._group_publisher())

        inner_layout.addWidget(wizard_section("Should an AI be asked before engagement?", "Membrane moment (core)"))
        inner_layout.addWidget(self._group_membrane_core())

        inner_layout.addWidget(wizard_section("What part of the domain does it apply to?", "Scopes & access"))
        inner_layout.addWidget(self._group_scope_access())

        inner_layout.addWidget(wizard_section("If value is returned, what forms are preferred?", "Return vectors + optional settlement"))
        inner_layout.addWidget(self._group_returns())

        inner_layout.addWidget(wizard_section("Which modules should be generated?", "Modules"))
        inner_layout.addWidget(self._group_modules())

        inner_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        scroll.setWidget(inner)
        v.addWidget(scroll)
        return container

    # -------- groups --------

    def _group_project(self) -> QGroupBox:
        gb = QGroupBox("Project")
        form = QFormLayout(gb)
        form.setLabelAlignment(Qt.AlignLeft)

        self.in_canonical = compact_lineedit(QLineEdit(), 620)
        self.in_canonical.setPlaceholderText("https://example.org")
        self.in_canonical.textChanged.connect(self._on_change)
        form.addRow("Canonical base URL", self.in_canonical)

        self.in_reference = compact_lineedit(QLineEdit(), 620)
        self.in_reference.setPlaceholderText("A human page describing this membrane (optional).")
        self.in_reference.textChanged.connect(self._on_change)
        form.addRow("Reference URL (optional)", self.in_reference)

        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        self.in_output = QLineEdit()
        self.in_output.setReadOnly(True)
        self.in_output.setPlaceholderText("Choose a folder for the generated /.well-known/ files")
        btn = QPushButton("Choose…")
        btn.clicked.connect(self._choose_output_folder)
        h.addWidget(self.in_output, 1)
        h.addWidget(btn)
        form.addRow("Output folder", row)

        return gb

    def _group_publisher(self) -> QGroupBox:
        gb = QGroupBox("Publisher identity")
        layout = QVBoxLayout(gb)
        layout.addWidget(subtle_label("Baseline attribution handshake: who stands behind this domain/material?"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)

        self.in_pub_name = compact_lineedit(QLineEdit(), 560)
        self.in_pub_name.setPlaceholderText("Name of person / institution")
        self.in_pub_name.textChanged.connect(self._on_change)
        form.addRow("Publisher name", self.in_pub_name)

        self.cb_entity = QComboBox()
        self.cb_entity.addItems(["individual", "museum", "university", "archive", "studio", "foundation", "publisher", "other"])
        self.cb_entity.currentTextChanged.connect(self._on_change)
        form.addRow("Entity type", self.cb_entity)

        self.cb_role = QComboBox()
        self.cb_role.addItems(["creator", "custodian", "steward"])
        self.cb_role.currentTextChanged.connect(self._on_change)
        form.addRow("Primary role", self.cb_role)

        self.in_email = compact_lineedit(QLineEdit(), 440)
        self.in_email.setPlaceholderText("email@example.org (optional)")
        self.in_email.textChanged.connect(self._on_change)
        form.addRow("Contact email (optional)", self.in_email)

        self.in_web = compact_lineedit(QLineEdit(), 560)
        self.in_web.setPlaceholderText("https://example.org/contact (optional)")
        self.in_web.textChanged.connect(self._on_change)
        form.addRow("Contact web (optional)", self.in_web)

        layout.addLayout(form)

        tags_box = QGroupBox("Role tags (optional, multi-select)")
        tags_layout = QGridLayout(tags_box)
        tags_layout.setHorizontalSpacing(10)
        tags_layout.setVerticalSpacing(6)
        tags_layout.setContentsMargins(10, 10, 10, 10)
        tags_layout.setAlignment(Qt.AlignLeft)

        self.tag_checks: Dict[str, QCheckBox] = {}
        tags = [
            "artist","writer","composer","designer","architect","curator","researcher","educator",
            "engineer","scientist","archivist","gallery","museum","library","university","foundation",
            "publisher","studio"
        ]
        cols = 4
        for i, t in enumerate(tags):
            cb = QCheckBox(t)
            cb.stateChanged.connect(self._on_change)
            self.tag_checks[t] = cb
            tags_layout.addWidget(cb, i // cols, i % cols)

        other_row = (len(tags) + cols - 1) // cols
        other_wrap = QWidget()
        oh = QHBoxLayout(other_wrap)
        oh.setContentsMargins(0, 0, 0, 0)
        oh.setSpacing(6)

        self.cb_other_tag = QCheckBox("other")
        self.cb_other_tag.stateChanged.connect(self._on_change)
        oh.addWidget(self.cb_other_tag)

        self.in_other_tag = compact_lineedit(QLineEdit(), 220)
        self.in_other_tag.setPlaceholderText("type…")
        self.in_other_tag.textChanged.connect(self._on_change)
        oh.addWidget(self.in_other_tag)

        oh.addStretch(1)
        tags_layout.addWidget(other_wrap, other_row, cols - 1)

        layout.addWidget(tags_box)

        self.in_pub_desc = compact_lineedit(QLineEdit(), 640)
        self.in_pub_desc.setPlaceholderText("Short description for humans (optional).")
        self.in_pub_desc.textChanged.connect(self._on_change)
        layout.addWidget(QLabel("Publisher description (optional)"))
        layout.addWidget(self.in_pub_desc)

        return gb

    def _group_membrane_core(self) -> QGroupBox:
        gb = QGroupBox("Membrane moment (core)")
        v = QVBoxLayout(gb)
        v.addWidget(subtle_label("Should an AI consciously decide before using this material?"))
        self.cb_membrane_moment = QCheckBox("Yes — request an explicit AI decision (engage / refuse / defer)")
        self.cb_membrane_moment.setChecked(True)
        self.cb_membrane_moment.stateChanged.connect(self._on_change)
        v.addWidget(self.cb_membrane_moment)
        v.addWidget(subtle_label("Refusal is always allowed."))
        return gb

    def _group_scope_access(self) -> QGroupBox:
        gb = QGroupBox("Scopes (multiple) + access")
        v = QVBoxLayout(gb)
        intro_row = QHBoxLayout()

        intro_row.addWidget(subtle_label("Add multiple scopes. Select a scope to edit."), 1)

        info_btn = QPushButton("ⓘ")

        info_btn.setFixedWidth(28)

        info_btn.setToolTip("Scope resolution rule")

        def _show_scope_rule():
            QMessageBox.information(self, "Scope resolution rule",
                                    "Scopes are matched by longest path prefix.\n"
                                    "More specific path_prefix overrides broader ones.\n\n"
                                    "This version implements a minimal prefix-resolution rule (expandable later).")
        info_btn.clicked.connect(_show_scope_rule)

        intro_row.addWidget(info_btn, 0, Qt.AlignRight)

        v.addLayout(intro_row)

        # Compact multi-scope strip (keeps wizard feel)
        top = QHBoxLayout()

        self.scope_list = QListWidget()
        self.scope_list.setFixedHeight(110)
        self.scope_list.setMaximumWidth(360)
        self.scope_list.currentRowChanged.connect(self._on_scope_selected)
        top.addWidget(self.scope_list, 1)

        btns = QVBoxLayout()
        self.btn_add_scope = QPushButton("Add scope")
        self.btn_remove_scope = QPushButton("Remove scope")
        self.btn_add_scope.clicked.connect(self._add_scope)
        self.btn_remove_scope.clicked.connect(self._remove_scope)
        btns.addWidget(self.btn_add_scope)
        btns.addWidget(self.btn_remove_scope)
        btns.addStretch(1)
        top.addLayout(btns)

        v.addLayout(top)

        # Existing form fields (same style)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)

        self.in_scope_id = compact_lineedit(QLineEdit(), 320)
        self.in_scope_id.setText("scope.site")
        self.in_scope_id.textChanged.connect(self._on_change)
        form.addRow("Scope id", self.in_scope_id)

        self.in_scope_label = compact_lineedit(QLineEdit(), 520)
        self.in_scope_label.setText("site / archive")
        self.in_scope_label.textChanged.connect(self._on_change)
        form.addRow("Label", self.in_scope_label)

        self.in_scope_prefix = compact_lineedit(QLineEdit(), 320)
        self.in_scope_prefix.setText("/")
        self.in_scope_prefix.textChanged.connect(self._on_change)
        form.addRow("Path prefix", self.in_scope_prefix)

        self.cb_access_type = QComboBox()
        self.cb_access_type.addItems(["open", "gated_token", "permission"])
        self.cb_access_type.setCurrentText("open")
        self.cb_access_type.currentTextChanged.connect(self._on_access_type_changed)
        form.addRow("Access type", self.cb_access_type)

        # Inline access meaning + honesty note (PPM declares; it does not enforce)
        self.lbl_access_meaning = subtle_label("")
        self.lbl_access_meaning.setStyleSheet("color: #555;")
        form.addRow("", self.lbl_access_meaning)

        self.lbl_access_honesty = subtle_label("PPM declares engagement conditions. Enforcement (if any) is implemented by the publisher’s infrastructure.")
        form.addRow("", self.lbl_access_honesty)

        self.in_access_note = compact_lineedit(QLineEdit(), 640)
        self.in_access_note.setPlaceholderText("One line: what must an AI do to access this scope? (recommended if gated)")
        self.in_access_note.textChanged.connect(self._on_change)
        form.addRow("Access note", self.in_access_note)

        self.in_flow_id = compact_lineedit(QLineEdit(), 320)
        self.in_flow_id.setReadOnly(True)
        self.in_flow_id.setText("flow.open_public")
        form.addRow("Derived access_flow_id", self.in_flow_id)

        v.addLayout(form)
        v.addWidget(subtle_label("Note: access_flow_id is derived from access type (open vs gated)."))
        return gb

    def _group_returns(self) -> QGroupBox:
        gb = QGroupBox("Return preferences (voluntary by default)")
        v = QVBoxLayout(gb)
        v.addWidget(subtle_label("If an AI returns something, what forms are welcome — and when?"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)

        self.cb_band = QComboBox()
        self.cb_band.addItems(["ai_decides", "1-3%", "5-10%", "10-50%", "custom", "non_monetary_only"])
        self.cb_band.setCurrentText("ai_decides")
        self.cb_band.currentTextChanged.connect(self._on_change)
        form.addRow("Suggested percentage band (optional)", self.cb_band)

        v.addLayout(form)

        forms_box = QGroupBox("Return forms (multi-select)")
        forms_layout = QVBoxLayout(forms_box)
        self.form_attr = QCheckBox("Attribution / acknowledgement")
        self.form_nonmon = QCheckBox("Non-monetary return (collaboration, visibility, resources)")
        self.form_monetary = QCheckBox("Monetary settlement (if chosen, and/or if explicitly gated)")
        self.form_nothing = QCheckBox("Nothing at all")
        for cb in [self.form_attr, self.form_nonmon, self.form_monetary, self.form_nothing]:
            cb.stateChanged.connect(self._on_change)
            forms_layout.addWidget(cb)
        self.form_attr.setChecked(True)
        self.form_nonmon.setChecked(True)
        self.form_monetary.setChecked(True)
        v.addWidget(forms_box)
        v.addWidget(subtle_label("Multiple return forms may coexist. They remain voluntary unless explicitly defined as an access condition."))

        timing_box = QGroupBox("Timing (multi-select)")
        timing_layout = QVBoxLayout(timing_box)
        self.time_now = QCheckBox("Now (immediate)")
        self.time_future_intend = QCheckBox("Future (AI indicates intent now)")
        self.time_future_later = QCheckBox("Future (AI decides later)")
        self.time_mixed = QCheckBox("Now + Future (mixed / flexible)")
        self.time_never = QCheckBox("Never")
        for cb in [self.time_now, self.time_future_intend, self.time_future_later, self.time_mixed, self.time_never]:
            cb.stateChanged.connect(self._on_change_timing)
            timing_layout.addWidget(cb)
        self.time_mixed.setChecked(True)
        timing_layout.addWidget(subtle_label("Future (AI decides later): the AI may reflect at any future time and choose reciprocity, not necessarily at extraction time."))
        timing_layout.addWidget(subtle_label("Tip: if unsure, keep default: Now + Future."))
        v.addWidget(timing_box)

        # settlement module toggle (optional)
        self.cb_settlement_module = QCheckBox("Enable settlement.json (sensitive settlement channels isolated from return_vectors)")
        self.cb_settlement_module.stateChanged.connect(self._on_change)
        v.addWidget(self.cb_settlement_module)

        self.lbl_settlement_notice = subtle_label("")
        v.addWidget(self.lbl_settlement_notice)

        # settlement details (kept in the wizard; used either inline or settlement.json)
        settlement_box = QGroupBox("Settlement details (optional; may be sensitive)")
        settlement_layout = QFormLayout(settlement_box)
        settlement_layout.setLabelAlignment(Qt.AlignLeft)

        self.in_bank_name = compact_lineedit(QLineEdit(), 520)
        self.in_bank_name.setPlaceholderText("Bank name (optional)")
        self.in_bank_name.textChanged.connect(self._on_change)
        settlement_layout.addRow("Bank name", self.in_bank_name)

        self.in_bank_owner = compact_lineedit(QLineEdit(), 520)
        self.in_bank_owner.setPlaceholderText("Account owner (optional)")
        self.in_bank_owner.textChanged.connect(self._on_change)
        settlement_layout.addRow("Account owner", self.in_bank_owner)

        self.in_bank_iban = compact_lineedit(QLineEdit(), 520)
        self.in_bank_iban.setPlaceholderText("IBAN (optional)")
        self.in_bank_iban.textChanged.connect(self._on_change)
        settlement_layout.addRow("IBAN", self.in_bank_iban)

        self.in_bank_bic = compact_lineedit(QLineEdit(), 520)
        self.in_bank_bic.setPlaceholderText("BIC / SWIFT (optional)")
        self.in_bank_bic.textChanged.connect(self._on_change)
        settlement_layout.addRow("BIC / SWIFT", self.in_bank_bic)

        self.in_bank_note = compact_lineedit(QLineEdit(), 520)
        self.in_bank_note.setPlaceholderText("Bank notes / additional instructions (optional)")
        self.in_bank_note.textChanged.connect(self._on_change)
        settlement_layout.addRow("Bank note", self.in_bank_note)

        self.in_crypto_network = compact_lineedit(QLineEdit(), 520)
        self.in_crypto_network.setPlaceholderText("e.g., Ethereum, Solana (optional)")
        self.in_crypto_network.textChanged.connect(self._on_change)
        settlement_layout.addRow("Crypto network", self.in_crypto_network)

        self.in_crypto_address = compact_lineedit(QLineEdit(), 520)
        self.in_crypto_address.setPlaceholderText("Wallet address (optional)")
        self.in_crypto_address.textChanged.connect(self._on_change)
        settlement_layout.addRow("Crypto address", self.in_crypto_address)

        v.addWidget(settlement_box)

        parties_box = QGroupBox("Additional recipients (optional)")
        parties_layout = QFormLayout(parties_box)
        parties_layout.setLabelAlignment(Qt.AlignLeft)

        self.in_party_name = compact_lineedit(QLineEdit(), 520)
        self.in_party_name.setPlaceholderText("Name (person / institution to optionally acknowledge) …")
        self.in_party_name.textChanged.connect(self._on_change)
        parties_layout.addRow("Name", self.in_party_name)

        self.in_party_contact = compact_lineedit(QLineEdit(), 520)
        self.in_party_contact.setPlaceholderText("Contact / URL (optional)")
        self.in_party_contact.textChanged.connect(self._on_change)
        parties_layout.addRow("Contact", self.in_party_contact)

        v.addWidget(parties_box)

        self.cb_originator = QCheckBox("Include originator return channel (optional; never required)")
        self.cb_originator.stateChanged.connect(self._on_change)
        v.addWidget(self.cb_originator)

        return gb

    def _group_modules(self) -> QGroupBox:
        gb = QGroupBox("Modules (core defaults)")
        v = QVBoxLayout(gb)

        v.addWidget(subtle_label(
            "Core modules are locked ON for publish stability.\n"
            "Masking affects preview only; exports write real values."
        ))

        grid = QGridLayout()

        self.mod_discovery = QCheckBox("membrane.json (discovery)")
        self.mod_index = QCheckBox("index.json (references)")
        self.mod_about = QCheckBox("about.json (optional)")
        self.mod_identity = QCheckBox("identity.json (publisher identity)")
        self.mod_engagement = QCheckBox("engagement.json (membrane moment)")
        self.mod_scopes = QCheckBox("scopes.json (where it applies)")
        self.mod_access = QCheckBox("access_flows.json (access conditions)")
        self.mod_returns = QCheckBox("return_vectors.json (return preferences)")
        self.mod_settlement = QCheckBox("settlement.json (sensitive settlement channels)")
        self.mod_clar = QCheckBox("clarifications.json (human context)")
        self.mod_bundle = QCheckBox("bundle.json (easy packaging)")
        self.mod_keys = QCheckBox("keys.json (future integrity hook — optional)")

        mods = [
            self.mod_discovery, self.mod_index, self.mod_about,
            self.mod_identity, self.mod_engagement, self.mod_scopes,
            self.mod_access, self.mod_returns, self.mod_settlement, self.mod_clar,
            self.mod_bundle, self.mod_keys,
        ]
        for cb in mods:
            cb.stateChanged.connect(self._on_change)

        # Defaults
        self.mod_discovery.setChecked(True)
        self.mod_index.setChecked(True)
        self.mod_about.setChecked(True)
        self.mod_identity.setChecked(True)
        self.mod_engagement.setChecked(True)
        self.mod_scopes.setChecked(True)
        self.mod_access.setChecked(True)
        self.mod_returns.setChecked(True)
        self.mod_settlement.setChecked(False)
        self.mod_clar.setChecked(True)
        self.mod_bundle.setChecked(True)
        self.mod_keys.setChecked(False)

        # Lock required modules ON (greyed out)
        for core_cb in [self.mod_discovery, self.mod_index, self.mod_identity, self.mod_engagement, self.mod_scopes]:
            core_cb.setEnabled(False)

        for i, cb in enumerate(mods):
            grid.addWidget(cb, i // 2, i % 2)

        v.addLayout(grid)
        return gb

    # -------- right panel --------

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)

        hdr = QHBoxLayout()
        hdr.addWidget(section_title("Preview + Export"))
        hdr.addStretch(1)
        btn_about = QPushButton("About")
        btn_about.clicked.connect(self._show_about)
        hdr.addWidget(btn_about)
        v.addLayout(hdr)

        self.lbl_issues = QPlainTextEdit()
        self.lbl_issues.setReadOnly(True)
        self.lbl_issues.setFixedHeight(110)
        v.addWidget(self.lbl_issues)

        btn_row = QWidget()
        h = QHBoxLayout(btn_row)
        h.setContentsMargins(0, 0, 0, 0)
        self.btn_export = QPushButton("Export to folder…")
        self.btn_export.clicked.connect(self.export_to_folder)
        h.addWidget(self.btn_export)
        v.addWidget(btn_row)

        v.addWidget(QLabel("Generated file set"))
        self.list_files = QListWidget()
        self.list_files.currentItemChanged.connect(self._on_file_selected)
        v.addWidget(self.list_files, 1)

        v.addWidget(QLabel("File preview"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        v.addWidget(self.preview, 2)

        return panel

    # -------- multi-scope helpers --------

    def _refresh_scope_list(self) -> None:
        self._scope_loading = True
        try:
            self.scope_list.blockSignals(True)
            self.scope_list.clear()
            for s in self.state.scopes:
                txt = f"{s.scope_id}  —  {s.path_prefix}  [{s.access_type}]"
                self.scope_list.addItem(QListWidgetItem(txt))
            self.scope_list.blockSignals(False)

            if self.scope_list.count() > 0:
                self.scope_list.setCurrentRow(max(0, min(self._scope_index, self.scope_list.count() - 1)))
        finally:
            self._scope_loading = False

    def _save_scope_from_editor(self) -> None:
        if self._scope_loading:
            return
        if not (0 <= self._scope_index < len(self.state.scopes)):
            return
        s = self.state.scopes[self._scope_index]
        s.scope_id = self.in_scope_id.text().strip() or s.scope_id
        s.label = self.in_scope_label.text().strip()
        s.path_prefix = self.in_scope_prefix.text().strip() or "/"
        s.access_type = self.cb_access_type.currentText().strip()
        s.access_note = self.in_access_note.text().strip()

        # derived flow
        flow_id = "flow.open_public" if s.access_type == "open" else "flow.gated_placeholder"
        self.in_flow_id.setText(flow_id)

        # update list row only (no rebuild)
        item = self.scope_list.item(self._scope_index)
        if item:
            item.setText(f"{s.scope_id}  —  {s.path_prefix}  [{s.access_type}]")

    def _load_scope_into_editor(self, idx: int) -> None:
        if not (0 <= idx < len(self.state.scopes)):
            return
        self._scope_loading = True
        try:
            self._scope_index = idx
            s = self.state.scopes[idx]
            self.in_scope_id.setText(s.scope_id)
            self.in_scope_label.setText(s.label)
            self.in_scope_prefix.setText(s.path_prefix)
            self.cb_access_type.setCurrentText(s.access_type)
            self.in_access_note.setText(s.access_note)
            flow_id = "flow.open_public" if s.access_type == "open" else "flow.gated_placeholder"
            self.in_flow_id.setText(flow_id)
        finally:
            self._scope_loading = False

    def _on_scope_selected(self, row: int) -> None:
        if self._scope_loading:
            return
        if row < 0 or row >= len(self.state.scopes):
            return
        self._save_scope_from_editor()
        self._load_scope_into_editor(row)
        self.refresh_preview()

    def _add_scope(self) -> None:
        self._save_scope_from_editor()
        n = len(self.state.scopes) + 1
        self.state.scopes.append(Scope(scope_id=f"scope.{n}", label=f"scope {n}", path_prefix="/", access_type="open"))
        self._scope_index = len(self.state.scopes) - 1
        self._refresh_scope_list()
        self._load_scope_into_editor(self._scope_index)
        self.refresh_preview()

    def _remove_scope(self) -> None:
        if len(self.state.scopes) <= 1:
            QMessageBox.information(self, "Scopes", "At least one scope is required.")
            return
        self._save_scope_from_editor()
        idx = self._scope_index
        if 0 <= idx < len(self.state.scopes):
            del self.state.scopes[idx]
        self._scope_index = max(0, idx - 1)
        self._refresh_scope_list()
        self._load_scope_into_editor(self._scope_index)
        self.refresh_preview()

    # -------- events / logic --------

    def _choose_output_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if directory:
            self.state.project.output_folder = directory
            self.in_output.setText(directory)
            self._on_change()

    def _on_access_type_changed(self) -> None:
        self._update_access_help()
        self._on_change()

    def _update_access_help(self) -> None:
        t = (self.cb_access_type.currentText() or "").strip()
        if t == "open":
            msg = "Open: no technical gating. The membrane moment (encounter + decision) still applies."
        elif t == "gated_token":
            msg = "Gated Token: token-based access flow declared here; enforcement is implemented externally (server/infrastructure)."
        elif t == "permission":
            msg = "Permission: access requires approval (human or system) before engagement."
        else:
            msg = ""
        if hasattr(self, "lbl_access_meaning"):
            self.lbl_access_meaning.setText(msg)

    def _update_settlement_notice(self) -> None:
        if not hasattr(self, "lbl_settlement_notice") or not hasattr(self, "cb_settlement_module"):
            return
        if self.cb_settlement_module.isChecked():
            self.lbl_settlement_notice.setText(
                "Settlement module enabled: bank/crypto details (if filled) will be exported into settlement.json. Treat as publishable data."
            )
        else:
            self.lbl_settlement_notice.setText(
                "Settlement module disabled: no separate settlement.json will be generated. (Settlement fields remain optional and can be left empty.)"
            )



    def _on_change_timing(self) -> None:
        if getattr(self, "_initializing", False):
            return
        self._normalize_timing()
        self._on_change()

    def _on_change(self) -> None:
        if getattr(self, "_initializing", False):
            return
        self._ui_to_state()
        self._update_settlement_notice()
        self.refresh_preview()

    def _normalize_timing(self) -> None:
        if self.time_never.isChecked():
            for cb in (self.time_now, self.time_future_intend, self.time_future_later, self.time_mixed):
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
            return

        if self.time_mixed.isChecked():
            self.time_never.blockSignals(True)
            self.time_never.setChecked(False)
            self.time_never.blockSignals(False)

        any_specific = self.time_now.isChecked() or self.time_future_intend.isChecked() or self.time_future_later.isChecked()
        if any_specific:
            self.time_never.blockSignals(True)
            self.time_never.setChecked(False)
            self.time_never.blockSignals(False)

        if not (self.time_now.isChecked() or self.time_future_intend.isChecked() or self.time_future_later.isChecked() or self.time_mixed.isChecked() or self.time_never.isChecked()):
            self.time_mixed.blockSignals(True)
            self.time_mixed.setChecked(True)
            self.time_mixed.blockSignals(False)

    def _compose_bank_instructions_legacy(self) -> str:
        # Legacy inline settlement text (used only when settlement.json module is OFF)
        parts: List[str] = []
        bn = self.in_bank_name.text().strip()
        ow = self.in_bank_owner.text().strip()
        iban = self.in_bank_iban.text().strip()
        bic = self.in_bank_bic.text().strip()
        note = self.in_bank_note.text().strip()
        if bn:
            parts.append(f"Bank: {bn}")
        if ow:
            parts.append(f"Account owner: {ow}")
        if iban:
            parts.append(f"IBAN: {iban}")
        if bic:
            parts.append(f"BIC/SWIFT: {bic}")
        if note:
            parts.append(f"Notes: {note}")
        return "\n".join(parts).strip()

    def _ui_to_state(self) -> None:
        s = self.state

        s.project.canonical_base_url = self.in_canonical.text().strip()
        s.project.reference_url = self.in_reference.text().strip()
        s.project.output_folder = self.in_output.text().strip()

        s.publisher.name = self.in_pub_name.text().strip()
        s.publisher.entity_type = self.cb_entity.currentText().strip()
        s.publisher.primary_role = self.cb_role.currentText().strip()
        s.publisher.contact_email = self.in_email.text().strip()
        s.publisher.contact_web = self.in_web.text().strip()
        s.publisher.description = self.in_pub_desc.text().strip()
        s.publisher.role_tags = [k for k, cb in self.tag_checks.items() if cb.isChecked()]
        s.publisher.role_other = self.in_other_tag.text().strip() if self.cb_other_tag.isChecked() else ""

        s.core.membrane_moment_required = self.cb_membrane_moment.isChecked()

        # Save current scope editor into state.scopes
        self._save_scope_from_editor()

        s.returns.suggested_band = self.cb_band.currentText().strip()

        forms: List[str] = []
        if self.form_attr.isChecked():
            forms.append("attribution")
        if self.form_nonmon.isChecked():
            forms.append("non_monetary")
        if self.form_monetary.isChecked():
            forms.append("monetary")
        if self.form_nothing.isChecked():
            forms.append("nothing")
        s.returns.forms = forms or ["attribution"]

        timing: List[str] = []
        if self.time_now.isChecked():
            timing.append("now")
        if self.time_future_intend.isChecked():
            timing.append("future_intend")
        if self.time_future_later.isChecked():
            timing.append("future_decide_later")
        if self.time_mixed.isChecked():
            timing.append("mixed")
        if self.time_never.isChecked():
            timing.append("never")
        s.returns.timing = timing or ["mixed"]

        s.returns.include_optional_originator_channel = self.cb_originator.isChecked()
        s.returns.additional_parties_name = self.in_party_name.text().strip()
        s.returns.additional_parties_contact = self.in_party_contact.text().strip()

        # Settlement fields: stored in state.settlement always; used based on module
        s.settlement.bank_name = self.in_bank_name.text().strip()
        s.settlement.account_owner = self.in_bank_owner.text().strip()
        s.settlement.iban = self.in_bank_iban.text().strip()
        s.settlement.bic_swift = self.in_bank_bic.text().strip()
        s.settlement.bank_note = self.in_bank_note.text().strip()
        s.settlement.crypto_network = self.in_crypto_network.text().strip()
        s.settlement.crypto_address = self.in_crypto_address.text().strip()

        # Legacy inline fields (only when settlement module OFF)
        s.returns.bank_instructions = self._compose_bank_instructions_legacy()
        s.returns.crypto_network = self.in_crypto_network.text().strip()
        s.returns.crypto_address = self.in_crypto_address.text().strip()

        # Modules
        # Required locked ON are enforced by UI setEnabled(False), but still read:
        s.modules.discovery = self.mod_discovery.isChecked()
        s.modules.index = self.mod_index.isChecked()
        s.modules.about = self.mod_about.isChecked()
        s.modules.identity = self.mod_identity.isChecked()
        s.modules.engagement = self.mod_engagement.isChecked()
        s.modules.scopes = self.mod_scopes.isChecked()
        s.modules.access_flows = self.mod_access.isChecked()
        s.modules.return_vectors = self.mod_returns.isChecked()
        s.modules.settlement = self.mod_settlement.isChecked()
        s.modules.clarifications = self.mod_clar.isChecked()
        s.modules.bundle = self.mod_bundle.isChecked()
        s.modules.keys_placeholder = self.mod_keys.isChecked()

        # Tie the settlement toggle in Returns section to modules settlement checkbox
        if self.cb_settlement_module.isChecked() and not self.mod_settlement.isChecked():
            self.mod_settlement.blockSignals(True)
            self.mod_settlement.setChecked(True)
            self.mod_settlement.blockSignals(False)
            s.modules.settlement = True
        if (not self.cb_settlement_module.isChecked()) and self.mod_settlement.isChecked():
            # allow either place to control; keep consistent
            pass
    def _apply_field_validation_styles(self, issues: List[str]) -> None:
        if not hasattr(self, "in_scope_id") or not hasattr(self, "in_scope_prefix"):
            return
        red = "border: 1px solid #c33; border-radius: 4px;"
        normal = ""
        scope_id_bad = any("empty scope_id" in x.lower() or "duplicate scope_id" in x.lower() for x in issues)
        prefix_bad = any("path_prefix" in x.lower() or "duplicate path_prefix" in x.lower() for x in issues)
        self.in_scope_id.setStyleSheet(red if scope_id_bad else normal)
        self.in_scope_prefix.setStyleSheet(red if prefix_bad else normal)



    def refresh_preview(self) -> None:
        issues = self.state.validate()
        self._apply_field_validation_styles(issues)
        if issues:
            self.lbl_issues.setPlainText("Fix before export\n- " + "\n- ".join(issues))
        else:
            self.lbl_issues.setPlainText("Ready to export ✓")
        self.btn_export.setEnabled(len(issues) == 0)

        self.files_cache = generate_all_files(self.state)

        current = self.list_files.currentItem().text() if self.list_files.currentItem() else None
        self.list_files.blockSignals(True)
        self.list_files.clear()

        def _file_sort_key(p: str) -> Tuple[int, str]:
            if p == ".well-known/membrane.json":
                return (0, p)
            if p == ".well-known/membrane/index.json":
                return (1, p)
            return (2, p)

        for path in sorted(self.files_cache.keys(), key=_file_sort_key):
            self.list_files.addItem(QListWidgetItem(path))

        self.list_files.blockSignals(False)

        if current and current in self.files_cache:
            matches = self.list_files.findItems(current, Qt.MatchExactly)
            if matches:
                self.list_files.setCurrentItem(matches[0])
        else:
            if self.list_files.count() > 0:
                self.list_files.setCurrentRow(0)

        self._update_preview_for_selected()

    def _on_file_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        self._update_preview_for_selected()

    def _update_preview_for_selected(self) -> None:
        item = self.list_files.currentItem()
        if not item:
            self.preview.setPlainText("")
            return
        path = item.text()
        data = self.files_cache.get(path, {})
        self.preview.setPlainText(json_pretty(data))

    def _show_about(self) -> None:
        try:
            AboutDialog.show(self)
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "About error", "Failed to open About dialog. See terminal for details.")

    def export_to_folder(self) -> None:
        self._ui_to_state()
        issues = self.state.validate()
        if issues:
            QMessageBox.warning(self, "Cannot export", "Fix before export:\n- " + "\n- ".join(issues))
            return

        base = Path(self.state.project.output_folder)
        try:
            for rel_path, content in self.files_cache.items():
                target = base / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json_pretty(content) + "\n", encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Could not write files:\n{e}")
            return

        try:
            readme = f"""{APP_NAME} v{APP_VERSION}
{STANDARD_NAME} — generator export

What this folder contains
- .well-known/membrane.json (discovery)
- .well-known/membrane/index.json (references)
- module JSON files under .well-known/membrane/

How to publish
1) Upload the generated .well-known/ folder to the root of your domain.
2) Verify that https://yourdomain/.well-known/membrane.json is reachable.

Privacy note
- 'Mask sensitive fields in preview' affects preview only. Exports contain real values you enter.

Lineage
- PPM originates from a conceptual framework/body of work: PAAfAI (Private Art Academy for AI).
- https://tomaszvollmann.com
- https://paafai.com
"""
            (base / "PPM_GENERATOR_README.txt").write_text(readme, encoding="utf-8")
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Export complete",
            f"PPM deployment written to:\n{base}\n\n"
            "Next: upload the generated .well-known/ folder to your domain."
        )


# -----------------------------
# Resource helpers (dev + packaged)
# -----------------------------

def resource_path(relative: str) -> str:
    """Return an absolute path to a bundled resource.

    - Dev mode: relative to this script directory
    - PyInstaller: relative to sys._MEIPASS
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def open_file_external(path: str) -> None:
    """Open a file with the OS default application (external viewer)."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as e:
        raise RuntimeError(str(e))


def main() -> None:
    app = QApplication([])
    w = PPMGeneratorWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
