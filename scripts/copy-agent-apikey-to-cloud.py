#!/usr/bin/env python3
"""Copy prod combat agent api_key into cloud training agent (no edge secret needed)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

PROD_AGENT_ID = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
CLOUD_AGENT_ID = "a2222222-2222-4222-8222-222222222222"


def read_prod_api_key() -> str:
    cmd = [
        "ssh",
        "-i",
        os.path.expanduser("~/.ssh/r10_bot_timeweb_ed25519"),
        "-o",
        "StrictHostKeyChecking=accept-new",
        "root@api.r10.kz",
        (
            "docker exec supabase_db_open-bsp-api psql -U postgres -d postgres -t -A "
            f"-c \"select extra->>'api_key' from agents where id='{PROD_AGENT_ID}';\""
        ),
    ]
    key = subprocess.check_output(cmd, text=True).strip()
    if len(key) < 20:
        raise RuntimeError("prod agent api_key missing")
    return key


def connect_cloud():
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
    api_key = read_prod_api_key()
    conn = connect_cloud()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select extra from agents where id = %s",
                    (CLOUD_AGENT_ID,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("cloud training agent missing")
                extra = row[0] or {}
                if isinstance(extra, str):
                    extra = json.loads(extra)
                extra["api_key"] = api_key
                extra["api_url"] = "openai"
                extra["model"] = extra.get("model") or "gpt-4.1-mini"
                cur.execute(
                    "update agents set extra = %s::jsonb where id = %s",
                    (json.dumps(extra), CLOUD_AGENT_ID),
                )
    finally:
        conn.close()
    print("OK training agent api_key copied from prod (not printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
