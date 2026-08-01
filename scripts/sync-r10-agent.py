#!/usr/bin/env python3
"""Sync r10/instructions/chiptuning-v1.md → Supabase cloud agents row (training org)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS = ROOT / "r10" / "instructions" / "chiptuning-v1.md"

ORG_ID = "a1111111-1111-4111-8111-111111111111"
AGENT_ID = "a2222222-2222-4222-8222-222222222222"
ORG_NAME = "R10 Chip Tuning Training"
AGENT_NAME = "R10 Chip Advisor"


def load_instructions() -> str:
    if not INSTRUCTIONS.is_file():
        print(f"FAIL missing {INSTRUCTIONS}", file=sys.stderr)
        sys.exit(1)
    text = INSTRUCTIONS.read_text(encoding="utf-8").strip()
    if len(text) < 200:
        print("FAIL instructions too short", file=sys.stderr)
        sys.exit(1)
    return text


def connect():
    try:
        import psycopg2
    except ImportError:
        print("FAIL install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    project = os.environ.get("SUPABASE_PROJECT_ID", "sywrcfyhbdnpferfeama")
    password = os.environ.get("SUPABASE_DB_PASSWORD", "")
    host = os.environ.get(
        "SUPABASE_SESSION_POOLER_HOST",
        "aws-1-ap-northeast-2.pooler.supabase.com",
    )
    if not password:
        print("FAIL SUPABASE_DB_PASSWORD not set", file=sys.stderr)
        sys.exit(1)

    dsn = (
        f"host={host} port=5432 dbname=postgres "
        f"user=postgres.{project} password={password} sslmode=require"
    )
    return psycopg2.connect(dsn)


def main() -> int:
    instructions = load_instructions()
    sha = hashlib.sha256(instructions.encode("utf-8")).hexdigest()
    model = os.environ.get("R10_AGENT_MODEL", "gpt-5-mini")

    agent_extra = {
        "mode": "active",
        "description": "R10 chip-tuning training agent (fiction sandbox)",
        "protocol": "chat_completions",
        "api_url": "openai",
        "model": model,
        "temperature": 0.4,
        "max_tokens": 512,
        "instructions": instructions,
    }
    org_extra = {
        "response_delay_seconds": 0,
        "default_agent_id": AGENT_ID,
    }

    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into public.organizations (id, name, extra)
                    values (%s, %s, %s::jsonb)
                    on conflict (id) do update
                    set name = excluded.name,
                        extra = organizations.extra || excluded.extra::jsonb
                    """,
                    (ORG_ID, ORG_NAME, json.dumps(org_extra)),
                )
                cur.execute(
                    """
                    insert into public.agents (id, organization_id, user_id, name, ai, extra)
                    values (%s, %s, null, %s, true, %s::jsonb)
                    on conflict (id) do update
                    set name = excluded.name,
                        extra = excluded.extra::jsonb,
                        updated_at = now()
                    """,
                    (AGENT_ID, ORG_ID, AGENT_NAME, json.dumps(agent_extra)),
                )
                cur.execute(
                    """
                    update public.organizations
                    set extra = coalesce(extra, '{}'::jsonb) || %s::jsonb
                    where id = %s
                    """,
                    (json.dumps({"default_agent_id": AGENT_ID}), ORG_ID),
                )
                cur.execute(
                    """
                    update public.organizations
                    set extra = extra - 'welcome_message'
                    where id = %s and extra ? 'welcome_message'
                    """,
                    (ORG_ID,),
                )
    finally:
        conn.close()

    print("OK sync-r10-agent")
    print(f"org_id={ORG_ID}")
    print(f"agent_id={AGENT_ID}")
    print(f"instructions_chars={len(instructions)}")
    print(f"instructions_sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
