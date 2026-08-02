# R10 training law (OpenBSP manufacturer)

**Project law:** OpenBSP `AgentExtra` + `r10/instructions/chiptuning-v1.md` = GitHub source of truth.

| Layer | Rule |
|-------|------|
| Prompt | `instructions/chiptuning-v1.md` only |
| LLM params | `scripts/sync-r10-agent.py` → DB `agents.extra` |
| API key | `OPENAI_API_KEY` GitHub secret → `sync-agent-apikey-from-env.py` — **no prod** |
| Platform | vanilla OpenBSP Edge — **no** `r10*` combat code |
| **Catalog (training)** | `r10/catalog/data/*` + `matcher.py` + `catalog-eval.py` — **not** Edge combat |
| Fiction | `regression:` + `87776543210` |

**Forbidden:** prod SSH in CI, `api.r10.kz` deploy, combat seatbelts in Edge (`r10DeliveryOnly`, routing, cabinet ingest).

**Catalog law:** prod dict snapshot + systemic matcher + optional SFT seed (`build-sft-catalog-seed.py`). Not in `instructions` markdown.

Canon: OpenBSP README § AgentExtra · `scripts/README.md`
