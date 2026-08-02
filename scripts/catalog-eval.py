#!/usr/bin/env python3
"""Run catalog-regression.json against training matcher (catalog-wide, no prod)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r10" / "catalog"))

from matcher import resolve_vehicle_from_catalog_blob  # noqa: E402

SCENARIOS = ROOT / "r10" / "scenarios" / "catalog-regression.json"


def _match_model(got: str, expect: str) -> bool:
    if not expect:
        return True
    if expect == got:
        return True
    return bool(re.search(expect, got, re.IGNORECASE))


def main() -> int:
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    failed = []
    for case in data["cases"]:
        hit = resolve_vehicle_from_catalog_blob(case["input"])
        exp = case.get("expect") or {}
        exp_brand = exp.get("brand")
        exp_model = exp.get("model")
        ok = True
        if exp_brand and hit.get("brand") != exp_brand:
            ok = False
        if ok and exp_model and not _match_model(hit.get("model", ""), exp_model):
            ok = False
        if ok and not exp_brand and hit:
            ok = False
        if not ok:
            failed.append(
                {
                    "id": case["id"],
                    "input": case["input"],
                    "expect": exp,
                    "got": hit,
                }
            )
    if failed:
        print("FAIL catalog-regression", len(failed), "of", len(data["cases"]))
        for f in failed:
            print(json.dumps(f, ensure_ascii=False))
        return 1
    print("OK catalog-regression", len(data["cases"]), "cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
