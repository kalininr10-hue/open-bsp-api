"""Training-only catalog matcher — mirrors prod r10CatalogMatcher.ts (read-only port).

Not deployed to OpenBSP Edge. Used for catalog eval + SFT seed generation on GitHub.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
INDEX_PATH = DATA_DIR / "r10_catalog_matcher_index.json"

_RAW: list[dict[str, Any]] = []
_by_token: dict[str, list[int]] = {}
_model_idx: list[int] = []
_ready = False


def _load_raw() -> list[dict[str, Any]]:
    global _RAW
    if _RAW:
        return _RAW
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    _RAW = list(data.get("patterns") or [])
    return _RAW


def _esc_re(s: str) -> str:
    return re.escape(s)


def _ensure_token_index() -> None:
    global _ready, _by_token, _model_idx
    if _ready:
        return
    raw = _load_raw()
    _model_idx = []
    _by_token = {}
    for i, p in enumerate(raw):
        if p.get("m"):
            _model_idx.append(i)
        for tok in str(p.get("n", "")).split():
            if len(tok) < 2:
                continue
            _by_token.setdefault(tok, []).append(i)
    _ready = True


@lru_cache(maxsize=8192)
def _pattern_re(i: int) -> re.Pattern[str]:
    raw = _load_raw()
    esc = _esc_re(raw[i]["n"])
    return re.compile(rf"(?:^|[^\w]){esc}(?:[^\w]|$)", re.IGNORECASE | re.UNICODE)


def normalize_matcher_text(raw: str) -> str:
    text = str(raw or "").lower().replace("ё", "е")
    text = re.sub(r"[^\w\s.+-/]", " ", text, flags=re.UNICODE)
    text = re.sub(r"м\s+(\d{1,3})", r"m\1", text, flags=re.IGNORECASE)
    text = re.sub(r"m\s+(\d{1,3})", r"m\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _candidate_indices(text: str) -> list[int]:
    _ensure_token_index()
    tokens = [t for t in text.split() if len(t) >= 2]
    seen: set[int] = set()
    for tok in tokens:
        for i in _by_token.get(tok, []):
            seen.add(i)
    if not seen:
        return []
    raw = _load_raw()
    return sorted(seen, key=lambda i: raw[i].get("l", 0), reverse=True)


def _match_from_candidates(text: str, indices: list[int]) -> dict[str, str]:
    raw = _load_raw()
    for i in indices:
        p = raw[i]
        if not p.get("m"):
            continue
        if _pattern_re(i).search(text):
            return {"brand": p["b"], "model": p["m"]}
    for i in indices:
        p = raw[i]
        if p.get("m"):
            continue
        if not _pattern_re(i).search(text):
            continue
        brand = p["b"]
        for j in _model_idx:
            p2 = raw[j]
            if p2["b"] != brand or not p2.get("m"):
                continue
            if _pattern_re(j).search(text):
                return {"brand": p2["b"], "model": p2["m"]}
        return {"brand": brand}
    return {}


def resolve_vehicle_from_catalog_blob(blob: str) -> dict[str, str]:
    text = normalize_matcher_text(blob)
    if not text:
        return {}
    return _match_from_candidates(text, _candidate_indices(text))


def resolve_vehicle_from_dialog(
    texts: list[dict[str, str]],
    prefer_incoming: bool = True,
) -> dict[str, str]:
    incoming = "\n".join(m.get("text", "") for m in texts if m.get("direction") == "incoming")
    full = "\n".join(m.get("text", "") for m in texts)
    if prefer_incoming:
        hit = resolve_vehicle_from_catalog_blob(incoming)
        if hit.get("brand"):
            return hit
    return resolve_vehicle_from_catalog_blob(full)
