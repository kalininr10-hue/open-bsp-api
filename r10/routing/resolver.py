"""Training-only routing resolver — mirrors prod r10RoutingMap (read-only port).

Not deployed to OpenBSP Edge. Injects branch context in local training-chat only.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
ROUTING_CTX_OPEN = "[R10_ROUTING_CONTEXT]"
ROUTING_CTX_CLOSE = "[/R10_ROUTING_CONTEXT]"


@lru_cache(maxsize=1)
def _load_branches() -> list[dict[str, Any]]:
    data = json.loads((DATA_DIR / "branches.json").read_text(encoding="utf-8"))
    return list(data.get("branches") or [])


@lru_cache(maxsize=1)
def _load_aliases() -> dict[str, str]:
    data = json.loads((DATA_DIR / "city_aliases.json").read_text(encoding="utf-8"))
    return dict(data.get("aliases") or {})


@lru_cache(maxsize=1)
def _load_canonical_cities() -> set[str]:
    data = json.loads((DATA_DIR / "city_aliases.json").read_text(encoding="utf-8"))
    return set(data.get("canonical_cities") or [])


@lru_cache(maxsize=1)
def _load_nearest_hubs() -> dict[str, list[str]]:
    data = json.loads((DATA_DIR / "nearest_hubs.json").read_text(encoding="utf-8"))
    return dict(data.get("hubs") or {})


def canonical_city(raw: str | None) -> str | None:
    t = str(raw or "").strip()
    if not t:
        return None
    low = re.sub(r"\s+", " ", t.lower())
    aliases = _load_aliases()
    if low in aliases:
        return aliases[low]
    canon = _load_canonical_cities()
    if t in canon:
        return t
    for city in canon:
        if city.lower() == low:
            return city
    return None


def parse_city_from_text(text: str) -> str | None:
    if not text:
        return None
    low = text.lower()
    aliases = _load_aliases()
    # Longer aliases first to avoid partial false positives.
    for alias, city in sorted(aliases.items(), key=lambda x: -len(x[0])):
        if re.search(rf"(?:^|[^\w]){re.escape(alias)}(?:[^\w]|$)", low, re.UNICODE):
            return city
    for city in sorted(_load_canonical_cities(), key=len, reverse=True):
        if re.search(rf"(?:^|[^\w]){re.escape(city.lower())}(?:[^\w]|$)", low, re.UNICODE):
            return city
    return None


def branches_in_city(city: str = "") -> list[dict[str, Any]]:
    canon = canonical_city(city)
    if not canon:
        return []
    return [b for b in _load_branches() if b.get("city") == canon]


def has_branch_city(city: str = "") -> bool:
    return len(branches_in_city(city)) > 0


def is_multi_branch_city(city: str = "") -> bool:
    return len(branches_in_city(city)) > 1


def nearest_hub_city(client_city: str = "") -> dict[str, str] | None:
    canon = canonical_city(client_city)
    if not canon or has_branch_city(canon):
        return None
    hubs = _load_nearest_hubs().get(canon)
    if hubs:
        return {"client_city": canon, "hub_city": hubs[0]}
    return None


def fmt_branch_line(branch: dict[str, Any], n: int | None = None) -> str:
    head = f"{n} — {branch['name']}" if n else str(branch["name"])
    bits = [head]
    if branch.get("address"):
        bits.append(str(branch["address"]))
    phones = branch.get("phones") or []
    if phones:
        bits.append(" / ".join(phones))
    if branch.get("truck"):
        bits.append("(грузовой)")
    return " · ".join(bits)


def resolve_lead_from_dialog(messages: list[str]) -> dict[str, Any]:
    client_city: str | None = None
    for msg in messages:
        found = parse_city_from_text(msg)
        if found:
            client_city = found
    route_city = client_city if client_city and has_branch_city(client_city) else None
    offer = nearest_hub_city(client_city or "") if client_city and not route_city else None
    multi = bool(route_city and is_multi_branch_city(route_city))
    return {
        "client_city": client_city,
        "service_city": route_city,
        "needs_nearest_consent": bool(offer and not route_city),
        "hub_city": offer.get("hub_city") if offer else None,
        "multi_branch": multi,
        "branches": branches_in_city(route_city or "") if route_city else [],
    }


def build_routing_context_block(lead: dict[str, Any]) -> str:
    lines = [
        "Служебный контекст R10 (не цитировать клиенту целиком).",
        "Филиалы и адреса только из этого блока — не выдумывать.",
    ]
    cc = lead.get("client_city")
    if cc:
        lines.append(f"clientCity={cc}")
    sc = lead.get("service_city")
    if sc:
        lines.append(f"serviceCity={sc}")
    if lead.get("multi_branch") and lead.get("branches"):
        lines.append(f"В {sc} несколько филиалов — ждём выбор клиента:")
        for i, b in enumerate(lead["branches"], 1):
            lines.append(f"  {fmt_branch_line(b, i)}")
    elif lead.get("branches"):
        b = lead["branches"][0]
        if len(lead["branches"]) == 1:
            lines.append(f"Филиал: {fmt_branch_line(b)}")
        else:
            for i, br in enumerate(lead["branches"], 1):
                lines.append(f"  {fmt_branch_line(br, i)}")
    elif lead.get("needs_nearest_consent") and lead.get("hub_city"):
        lines.append(
            f"В {cc} своего филиала нет. Ближайший хаб: {lead['hub_city']} — "
            "сначала согласие клиента, потом филиал из хаба."
        )
        hub_branches = branches_in_city(lead["hub_city"])
        if hub_branches:
            lines.append("Филиалы хаба:")
            for i, b in enumerate(hub_branches, 1):
                lines.append(f"  {fmt_branch_line(b, i)}")
    elif cc and not has_branch_city(cc):
        lines.append(f"Город {cc}: филиала в сети нет — уточни ближайший хаб или согласие.")
    else:
        lines.append("Город клиента пока не определён — спроси город.")
    return "\n".join(lines)


def strip_routing_context(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(
        rf"{re.escape(ROUTING_CTX_OPEN)}.*?{re.escape(ROUTING_CTX_CLOSE)}\s*",
        re.DOTALL,
    )
    return pattern.sub("", text).strip()


def wrap_user_message(user_text: str, history_texts: list[str]) -> str:
    dialog = list(history_texts) + [user_text]
    lead = resolve_lead_from_dialog(dialog)
    ctx = build_routing_context_block(lead)
    return f"{ROUTING_CTX_OPEN}\n{ctx}\n{ROUTING_CTX_CLOSE}\n\n{user_text.strip()}"
