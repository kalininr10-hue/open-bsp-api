#!/usr/bin/env python3
"""Run routing-regression.json against training resolver (routing-wide, no prod)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r10" / "routing"))

from resolver import branches_in_city, resolve_lead_from_dialog  # noqa: E402

SCENARIOS = ROOT / "r10" / "scenarios" / "routing-regression.json"


def main() -> int:
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    failed = []
    for case in data["cases"]:
        lead = resolve_lead_from_dialog(case["dialog"])
        exp = case.get("expect") or {}
        ok = True
        for key, val in exp.items():
            if key == "branch_count":
                if len(lead.get("branches") or []) != val:
                    ok = False
            elif key == "branch_names":
                names = [b["name"] for b in lead.get("branches") or []]
                if names != val:
                    ok = False
            elif lead.get(key) != val:
                ok = False
        if ok and exp.get("service_city"):
            if lead.get("service_city") != exp["service_city"]:
                ok = False
        if not ok:
            failed.append({"id": case["id"], "expect": exp, "got": lead})
    if failed:
        print("FAIL routing-regression", len(failed), "of", len(data["cases"]))
        for f in failed:
            print(json.dumps(f, ensure_ascii=False))
        return 1
    print("OK routing-regression", len(data["cases"]), "cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
