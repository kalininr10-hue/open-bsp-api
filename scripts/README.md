# R10 training scripts (OpenBSP law)

Cloud Supabase only. **No prod SSH / no api.r10.kz.**

| Script | Purpose |
|--------|---------|
| `sync-r10-agent.py` | **Canon** — `chiptuning-v1.md` → `instructions` + AgentExtra params |
| `sync-agent-apikey-from-env.py` | `OPENAI_API_KEY` env → `agents.extra.api_key` |
| `seed-billing-training.py` | Billing schema + subscription for training org |
| `bootstrap-training-chat.py` | Local `service=local` conversation row |
| `catalog-eval.py` | **Catalog** — `catalog-regression.json` vs `r10/catalog/matcher.py` |
| `build-sft-catalog-seed.py` | SFT seed jsonl from catalog matcher hits (fiction sessions) |

Removed (violate training law — prod access):

- ~~`copy-agent-apikey-to-cloud.py`~~
- ~~`copy-openai-to-cloud.py`~~
- ~~`r10-audit-v3-github.py`~~ (combat audit, not training)
