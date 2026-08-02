# Routing data snapshot (prod read-only)

| File | Prod source |
|------|-------------|
| `branches.json` | `r10RoutingMap.ts` → `R10_BRANCHES` |
| `city_aliases.json` | `r10RoutingMap.ts` `CITY_ALIASES` + `CITY_COORDS` keys |
| `nearest_hubs.json` | `nearestBranchMap.json` + `nearestBranches` routing data |

**Snapshot date:** 2026-08-02 (local mirror of prod OpenBSP routing; SSH verify when available).

Refresh manually when prod routing changes — commit to GitHub, never auto-SSH from CI.

Training injection mimics prod `R10_LEAD_STATE` / routing context — **local dev only**, not OpenBSP Edge.
