# R10 routing — training layer (not combat Edge)

Per owner law: **prod branch snapshot + systemic resolver + per-turn context in training-chat only**.

| Piece | Path | Role |
|-------|------|------|
| **Branches** | `data/branches.json` | Snapshot from prod `r10RoutingMap.ts` `R10_BRANCHES` |
| **Aliases** | `data/city_aliases.json` | City canonicalization (catalog-wide) |
| **Nearest hubs** | `data/nearest_hubs.json` | Cities without branch → hub city |
| **Resolver** | `resolver.py` | Python port of routing facts — not in Edge |
| **Regression** | `../scenarios/routing-regression.json` | Multi-city cases |
| **Injection** | `../dev/training-chat-server.py` | Prepends `[R10_ROUTING_CONTEXT]` per user turn |

## Not here (combat only)

- `r10RoutingMap.ts`, `r10DeliveryOnly.ts`, cabinet ingest — stay on `api.r10.kz`
- No full branch dump in `instructions/chiptuning-v1.md`

## Commands

```bash
python3 scripts/routing-eval.py
```

## Refresh from prod

Manual read-only snapshot. See `data/SNAPSHOT.md`.

Prod paths:

- `/opt/open-bsp/supabase/functions/_shared/r10RoutingMap.ts`
- `/opt/open-bsp/r10-knowledge/nearestBranchMap.json` (nearest hub overrides)

After refresh: run `routing-eval.py`, commit data + scenarios.
