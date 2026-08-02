# R10 OpenBSP training (cloud sandbox)

Training on **GitHub + Supabase cloud** per **OpenBSP `AgentExtra`** (manufacturer schema).  
Not combat `api.r10.kz`. No R10 seatbelt code (`r10DeliveryOnly`, catalog, routing).

## Source of truth (Git)

| Path | OpenBSP field / role |
|------|----------------------|
| `instructions/chiptuning-v1.md` | `agents.extra.instructions` — prompt only (dialogue law, RU snapshot from prod DB) |
| `scripts/sync-r10-agent.py` | writes all other `AgentExtra` fields to cloud DB |
| `scenarios/fiction-smoke.json` | fiction regression spec (CI JSON check only) |

## AgentExtra (OpenBSP manufacturer)

Prompt and LLM params are **separate fields** in `agents.extra` (see repo `README.md` § AgentExtra):

| Field | Training value | Set by |
|-------|----------------|--------|
| `instructions` | `r10/instructions/chiptuning-v1.md` | sync script |
| `protocol` | `chat_completions` | sync script |
| `api_url` | `openai` | sync script |
| `model` | `gpt-5-mini` (env `R10_AGENT_MODEL`) | sync script |
| `temperature` | `1` (required for gpt-5-mini) | sync script |
| `max_tokens` | `512` | sync script |
| `mode` | `active` | sync script |
| `api_key` | not in git | `OPENAI_API_KEY` GitHub secret → `sync-agent-apikey-from-env.py` |

**Not in instructions markdown** — only in sync → DB.

## Cloud IDs

- Organization: `a1111111-1111-4111-8111-111111111111` — R10 Chip Tuning Training
- Agent: `a2222222-2222-4222-8222-222222222222` — R10 Chip Advisor

## GitHub CI

Push to `main` or `r10/chiptuning-training` (paths `r10/**`, `scripts/sync-r10-agent.py`) → workflow **R10 Chip Tuning Training**:

1. `python3 scripts/sync-r10-agent.py` → cloud Postgres
2. `python3 scripts/sync-agent-apikey-from-env.py` → `api_key` from `OPENAI_API_KEY` (if set)
3. validate `fiction-smoke.json`

### Secrets / variables

| Name | Kind |
|------|------|
| `SUPABASE_DB_PASSWORD` | secret |
| `SUPABASE_ACCESS_TOKEN` | secret |
| `SUPABASE_SERVICE_ROLE_KEY` | secret |
| `OPENAI_API_KEY` | secret → `agents.extra.api_key` via CI |
| `SUPABASE_PROJECT_ID` | variable (`sywrcfyhbdnpferfeama`) |
| `SUPABASE_SESSION_POOLER_HOST` | variable |

## Manual sync

```bash
export SUPABASE_DB_PASSWORD='...'
export OPENAI_API_KEY='sk-...'   # optional
python3 scripts/sync-r10-agent.py
python3 scripts/sync-agent-apikey-from-env.py
```

Preserves existing `api_key` in DB; overwrites `instructions` + LLM params from Git.

## Browser chat (local, no WhatsApp)

```powershell
$env:SUPABASE_DB_PASSWORD = '...'
python r10/dev/training-chat-server.py
```

→ http://127.0.0.1:8787 — messages `service=local` → OpenBSP `agent-client` Edge.  
Needs `api_key` on training agent (`OPENAI_API_KEY` in GitHub secrets + CI sync).
