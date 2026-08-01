#!/usr/bin/env python3
"""Seed billing reference data + subscription for R10 training org on cloud."""

from __future__ import annotations

import os
import sys

ORG_ID = "a1111111-1111-4111-8111-111111111111"


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
    return psycopg2.connect(
        host=host,
        port=5432,
        dbname="postgres",
        user=f"postgres.{project}",
        password=password,
        sslmode="require",
    )


SEED_SQL = """
-- expose billing to PostgREST (training cloud)
alter role authenticator set pgrst.db_schemas = 'public, storage, graphql_public, billing';
notify pgrst, 'reload config';

insert into billing.products (id, name, unit, kind) values
  ('messages', 'Messages', 'count', 'counter'),
  ('conversations', 'Conversations', 'count', 'counter'),
  ('storage', 'Storage', 'gb', 'gauge'),
  ('ai_credits', 'AI Credits', 'usd', 'balance')
on conflict (id) do nothing;

insert into billing.tiers (id, name, level, active) values
  ('free', 'Free', 0, true),
  ('starter', 'Starter', 1, true)
on conflict (id) do nothing;

insert into billing.tiers_products (tier_id, product_id, interval, cap) values
  ('free', 'messages', 'month', 5000),
  ('free', 'storage', 'lifetime', 1),
  ('free', 'ai_credits', 'lifetime', 0),
  ('starter', 'messages', 'month', 100000),
  ('starter', 'storage', 'lifetime', 100),
  ('starter', 'ai_credits', 'lifetime', 0)
on conflict do nothing;

insert into billing.plans (id, min_tier, price, billing_cycle, is_default, active) values
  ('free', 0, 0, null, true, true),
  ('starter', 1, 5, 'month', false, true)
on conflict (id) do nothing;

insert into billing.plans_products (plan_id, product_id, interval, included, unit_price) values
  ('free', 'messages', 'month', 5000, null),
  ('free', 'storage', 'lifetime', 1, null),
  ('free', 'ai_credits', 'lifetime', 1.00, null),
  ('starter', 'messages', 'month', 25000, 0.001),
  ('starter', 'storage', 'lifetime', 25, 0.025),
  ('starter', 'ai_credits', 'lifetime', 1, null)
on conflict do nothing;

insert into billing.costs (provider, product, quantity, unit, pricing) values
  ('openai', 'gpt-5-mini', 1000000, 'tokens', '{"input": 0.25, "output": 2.00, "cache_read": 0.03}'),
  ('openai', 'gpt-4.1-mini', 1000000, 'tokens', '{"input": 0.25, "output": 2.00, "cache_read": 0.03}')
on conflict (provider, product, effective_at) do nothing;
"""


def main() -> int:
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SEED_SQL)

                cur.execute(
                    "select 1 from billing.subscriptions where organization_id = %s",
                    (ORG_ID,),
                )
                if cur.fetchone() is None:
                    cur.execute(
                        """
                        insert into billing.subscriptions (organization_id, tier_id)
                        values (%s, 'free')
                        """,
                        (ORG_ID,),
                    )
                    cur.execute(
                        "select billing.change_plan(%s, 'free')",
                        (ORG_ID,),
                    )

                cur.execute("select count(*) from billing.products")
                products = cur.fetchone()[0]
                cur.execute(
                    "select count(*) from billing.subscriptions where organization_id = %s",
                    (ORG_ID,),
                )
                subs = cur.fetchone()[0]
    finally:
        conn.close()

    print("OK seed-billing-training")
    print(f"products={products} subscription={subs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
