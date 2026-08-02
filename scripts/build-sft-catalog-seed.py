#!/usr/bin/env python3
"""Build SFT seed jsonl: catalog matcher hits + fiction session keys (no prod, no cabinet).

Per r10-dialog-success-metric: dataset = combat dialogues + catalog engine pass.
This script writes structured seeds for future fine-tune — not assistant fiction.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r10" / "catalog"))

from matcher import resolve_vehicle_from_catalog_blob  # noqa: E402

CATALOG_SCENARIOS = ROOT / "r10" / "scenarios" / "catalog-regression.json"
OUT_DIR = ROOT / "r10" / "catalog" / "sft-seed"
OUT_FILE = OUT_DIR / "catalog-matcher-seed.jsonl"


def main() -> int:
    data = json.loads(CATALOG_SCENARIOS.read_text(encoding="utf-8"))
    meta = data.get("meta") or {}
    prefix = meta.get("session_prefix", "regression:catalog:")
    phone = meta.get("fiction_phone", "87776543210")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for case in data["cases"]:
        hit = resolve_vehicle_from_catalog_blob(case["input"])
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session": f"{prefix}{case['id']}",
            "fiction_phone": phone,
            "user_text": case["input"],
            "matcher_hit": hit,
            "expect": case.get("expect") or {},
            "kind": "catalog_matcher_seed",
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK wrote {len(lines)} rows -> {OUT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
