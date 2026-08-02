#!/usr/bin/env python3
"""Set training agent api_key from OPENAI_API_KEY env (GitHub secret). Cloud only — no prod."""

from __future__ import annotations

import json
import os
import sys

AGENT_ID = "a2222222-2222-4222-8222-222222222222"


def connect():
    import psycopg2

    project = os.environ.get("SUPABASE_PROJECT_ID", "sywrcfyhbdnpferfeama")
    password = os.environ.get("SUPABASE_DB_PASSWORD", "")
    host = os.environ.get(
        "SUPABASE_SESSION_POOLER_HOST",
        "aws-1-ap-northeast-2.pooler.supabase.com",
    )
    if not password:
        raise RuntimeError("SUPABASE_DB_PASSWORD not set")
    return psycopg2.connect(
        host=host,
        port=5432,
        dbname="postgres",
        user=f"postgres.{project}",
        password=password,
        sslmode="require",
    )


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or not api_key.startswith("sk-"):
        print("SKIP OPENAI_API_KEY not set (agent keeps existing api_key)")
        return 0

    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("select extra from agents where id = %s", (AGENT_ID,))
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("training agent missing — run sync-r10-agent.py first")
                extra = row[0] or {}
                if isinstance(extra, str):
                    extra = json.loads(extra)
                extra["api_key"] = api_key
                extra["api_url"] = "openai"
                cur.execute(
                    "update agents set extra = %s::jsonb, updated_at = now() where id = %s",
                    (json.dumps(extra), AGENT_ID),
                )
    finally:
        conn.close()

    print("OK training agent api_key set from OPENAI_API_KEY (not printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
