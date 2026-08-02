# R10 training law (OpenBSP manufacturer)

**Project law:** OpenBSP `AgentExtra` + `r10/instructions/chiptuning-v1.md` = GitHub source of truth.

| Layer | Rule |
|-------|------|
| Prompt | `instructions/chiptuning-v1.md` only |
| LLM params | `scripts/sync-r10-agent.py` → DB `agents.extra` |
| API key | `OPENAI_API_KEY` GitHub secret → `sync-agent-apikey-from-env.py` — **no prod** |
| Platform | vanilla OpenBSP Edge — **no** `r10*` combat code |
| Fiction | `regression:` + `87776543210` |

**Forbidden:** prod SSH, `api.r10.kz`, combat seatbelts (`r10DeliveryOnly`, catalog, routing), combat audit workflows.

Canon: OpenBSP README § AgentExtra · `scripts/README.md`
