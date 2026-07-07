# AGENTS.md (barcode_api)

## Scope
This file applies only to `apps/barcode_api`.

## Purpose
FDC (FoodData Central) + Open Food Facts barcode-to-nutrition lookup API. **MAINTENANCE phase**: production keep-alive and data freshness, not active feature development.

## Read First
`plans/current.md` (operational SSOT: current production state, Non-Negotiables, next-action queue, session log).

## Non-Negotiables
- Production Cloud Run operations, `deploy.sh`, and `commit`/`push` require explicit user instruction.
- FDC database refresh follows `docs/DATA_REFRESH_RUNBOOK.md` (local rebuild -> local verification -> versioned GCS upload -> Cloud Run restart/redeploy -> production probe -> rollback plan). Do not overwrite the production GCS object outside this runbook.
- No-fallback: unexpected states raise and stop (existing convention in `services/fdc_service.py` / `services/off_service.py`). Do not weaken this.
- Reference data changes (`data/*.json`) go through diff review; tracking policy is `ssot/DATASETS.md` §3.

## Key Commands
- Local run: `PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main`
- Lookup / health-check examples: see `README.md` "APIエンドポイント" section.
- FDC database rebuild: `python apps/barcode_api/scripts/setup_fdc_database.py --force-download` (read `docs/DATA_REFRESH_RUNBOOK.md` before running against the production dataset).
