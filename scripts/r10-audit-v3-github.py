#!/usr/bin/env python3
"""R10 audit v3 — GitHub runner (no prod / no docker / no live DB)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCS = ROOT / "supabase/functions"

REQUIRED_FUNCTIONS = [
    "agent-client",
    "generic-dispatcher",
    "generic-webhook",
    "instagram-dispatcher",
    "instagram-management",
    "instagram-webhook",
    "mcp",
    "media-preprocessor",
    "storage-gc",
    "whatsapp-dispatcher",
    "whatsapp-management",
    "whatsapp-web-management",
    "whatsapp-webhook",
]


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    return ok


def main() -> int:
    fails: list[str] = []
    print("=== R10 AUDIT V3 (GITHUB) ===")
    print("NOTE: combat 24h / WA silence / live prompt — prod-only; skipped here.")

    shared = FUNCS / "_shared"
    if not check("fn__shared", shared.is_dir(), str(shared)):
        fails.append("shared")

    for fn in REQUIRED_FUNCTIONS:
        idx = FUNCS / fn / "index.ts"
        size = idx.stat().st_size if idx.is_file() else 0
        ok = idx.is_file() and size > 100
        if not check(f"fn_{fn}", ok, f"{size} bytes"):
            fails.append(fn)

    catalog = FUNCS / "_shared/r10_catalog_matcher_index.json"
    if catalog.is_file():
        data = json.loads(catalog.read_text(encoding="utf-8"))
        patterns = data.get("patterns") or []
        brands = sorted({p.get("b", "").strip() for p in patterns if p.get("b")})
        if not check("catalog_patterns", len(patterns) > 0, f"patterns={len(patterns)} brands={len(brands)}"):
            fails.append("catalog")
    else:
        check("catalog_patterns", True, "skipped (upstream fork — no R10 catalog file)")

    routing = FUNCS / "_shared/r10RoutingMap.ts"
    if routing.is_file():
        text = routing.read_text(encoding="utf-8")
        for city in ("Алматы", "Астана", "Өскемен"):
            if city not in text:
                if not check(f"routing_has_{city}", False, "missing in map source"):
                    fails.append("routing")
                break
        else:
            check("routing_map_source", True, "core cities present")
    else:
        check("routing_map_source", True, "skipped (upstream fork)")

    summary = {"passed": len(fails) == 0, "fail_count": len(fails), "fails": fails, "runner": "github"}
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
