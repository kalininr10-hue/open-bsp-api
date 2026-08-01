#!/usr/bin/env python3
"""Bootstrap local-service training conversation for R10 cloud org."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ORG_ID = "a1111111-1111-4111-8111-111111111111"
AGENT_ID = "a2222222-2222-4222-8222-222222222222"
CONV_ID = "c3333333-3333-4333-8333-333333333333"


def connect():
    import psycopg2

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
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select 1 from public.organizations where id = %s",
                    (ORG_ID,),
                )
                if cur.fetchone() is None:
                    print("FAIL org missing — run scripts/sync-r10-agent.py first")
                    return 1

                cur.execute(
                    """
                    insert into public.organizations_addresses
                      (organization_id, service, address, status)
                    values (%s, 'local', %s, 'connected')
                    on conflict do nothing
                    """,
                    (ORG_ID, ORG_ID),
                )

                cur.execute(
                    """
                    insert into public.conversations (
                      id, organization_id, service, organization_address,
                      contact_address, name, status, extra
                    ) values (
                      %s, %s, 'local', %s,
                      null, 'R10 Training Chat', 'active', %s::jsonb
                    )
                    on conflict (id) do update
                    set extra = excluded.extra,
                        status = 'active',
                        updated_at = now()
                    """,
                    (
                        CONV_ID,
                        ORG_ID,
                        ORG_ID,
                        json.dumps({"default_agent_id": AGENT_ID}),
                    ),
                )
    finally:
        conn.close()

    import subprocess
    import sys

    seed = Path(__file__).resolve().parents[1] / "scripts" / "seed-billing-training.py"
    subprocess.run([sys.executable, str(seed)], check=True)

    print("OK bootstrap-training-chat")
    print(f"conversation_id={CONV_ID}")
    print(f"open http://127.0.0.1:8787 after starting r10/dev/training-chat-server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
