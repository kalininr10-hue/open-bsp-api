#!/usr/bin/env python3
"""Reset training conversation messages (fiction sandbox only)."""

from __future__ import annotations

import os
import sys

OLD_CONV_ID = "c3333333-3333-4333-8333-333333333333"

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
    conv_id = os.environ.get("R10_TRAINING_CONV_ID", OLD_CONV_ID)
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "delete from public.messages where conversation_id = %s",
                    (conv_id,),
                )
                deleted = cur.rowcount
                cur.execute(
                    """
                    update public.conversations
                    set status = 'active', updated_at = now()
                    where id = %s
                    """,
                    (conv_id,),
                )
    finally:
        conn.close()

    print("OK reset-training-conversation")
    print(f"conversation_id={conv_id}")
    print(f"deleted_messages={deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
