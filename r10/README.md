# R10 OpenBSP training (cloud sandbox)

Training contour for a **new** chip-tuning bot — not a copy of combat `api.r10.kz`.

| Path | Purpose |
|---|---|
| `instructions/chiptuning-v1.md` | Agent prompt (Git source of truth) |
| `scenarios/fiction-smoke.json` | Fiction regression cases (`regression:` + phone `87776543210`) |

## Sync to Supabase cloud

On push to `main` or `r10/chiptuning-training`, workflow **R10 Chip Tuning Training** runs `scripts/sync-r10-agent.py`.

Fixed IDs:

- Organization: `a1111111-1111-4111-8111-111111111111` — R10 Chip Tuning Training
- AI agent: `a2222222-2222-4222-8222-222222222222` — R10 Chip Advisor

## GitHub secrets / variables

| Name | Kind |
|---|---|
| `SUPABASE_DB_PASSWORD` | secret |
| `SUPABASE_ACCESS_TOKEN` | secret |
| `OPENAI_API_KEY` | secret (optional — edge functions) |
| `SUPABASE_PROJECT_ID` | variable (`sywrcfyhbdnpferfeama`) |
| `SUPABASE_SESSION_POOLER_HOST` | variable (`aws-1-ap-northeast-2.pooler.supabase.com`) |

## Local sync

```bash
export SUPABASE_DB_PASSWORD='...'
python3 scripts/sync-r10-agent.py
```
