# Catalog data snapshot (prod read-only)

| File | Prod source | Bytes (approx) |
|------|-------------|----------------|
| `brand_variants.json` | `/opt/open-bsp/r10-knowledge/brand_variants.json` | 14K |
| `model_aliases.json` | `/opt/open-bsp/r10-knowledge/model_aliases.json` | 109K |
| `r10_catalog_matcher_index.json` | `/opt/open-bsp/supabase/functions/_shared/r10_catalog_matcher_index.json` | 508K |

**Snapshot date:** 2026-08-02 (read-only SSH, no prod writes).

Refresh manually when prod dicts change — commit to GitHub, never auto-SSH from CI.

Matcher canon on prod: `r10CatalogMatcher.ts` → port in `../matcher.py`.
