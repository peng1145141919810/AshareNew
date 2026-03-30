# Affordable Updateable Sources

## Goal
- Build as many low-cost updateable sources as possible with:
  - free official web sources
  - current Tushare access
- Keep them in a standalone store instead of mixing them into the old deleted non-price pipeline.

## Current Entry
- Script:
  - `F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py`
- Default SQLite:
  - `F:\quant_data\AshareC#\data\sql_store\affordable_data_v1.sqlite3`
- Default CSV snapshots:
  - `F:\quant_data\AshareC#\data\affordable_feeds\latest`
- Daily automation:
  - the trade clock research phase now triggers this bundle automatically before `research_only`
  - runtime logs:
    - `F:\quant_data\AshareC#\data\trade_clock\runtime\<trade_date>\affordable_data_refresh.stdout.log`
    - `F:\quant_data\AshareC#\data\trade_clock\runtime\<trade_date>\affordable_data_refresh.stderr.log`
  - behavior:
    - default `fail_open`
    - if low-cost refresh fails, research can continue unless the operator explicitly changes the setting to fail-closed

## Datasets Supported Now

### Tushare Bundle
- `stock_basic`
- `daily`
- `adj_factor`
- `daily_basic`
- `forecast`
- `express`
- `dividend`
- `stk_holdertrade`
- `ggt_daily`
- `moneyflow_hsgt`
- `hk_hold`
- `margin`
- `margin_detail`
- `moneyflow`
- `stk_limit`

### Tushare Optional
- `fina_indicator`
- This one needs explicit `--ts-code` because the API is not practical to refresh full-universe by date only.

### Official Free Source
- `customs_summary`
- Source:
  - `gov.cn` official customs release pages
- Scope:
  - summary layer only
  - not detailed customs tables

## What Gets Stored
- Table:
  - `affordable_dataset_rows`
- Key columns:
  - `dataset`
  - `record_key`
- Common searchable columns:
  - `primary_date`
  - `secondary_date`
  - `ts_code`
- Full original row:
  - `payload_json`

- Run log table:
  - `affordable_source_runs`

## Recommended Commands

### Default affordable bundle
```powershell
C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py
```

### Only Tushare daily-style bundle for a fixed trade date
```powershell
C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py `
  --dataset daily `
  --dataset adj_factor `
  --dataset daily_basic `
  --dataset moneyflow `
  --dataset margin_detail `
  --dataset stk_limit `
  --dataset ggt_daily `
  --start-date 20260327 `
  --end-date 20260327
```

### Announcement-like datasets for a small recent range
```powershell
C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py `
  --dataset forecast `
  --dataset express `
  --dataset dividend `
  --dataset stk_holdertrade `
  --ann-start-date 20260320 `
  --ann-end-date 20260330
```

### Targeted financial indicators for selected stocks
```powershell
C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py `
  --dataset fina_indicator `
  --ts-code 000001.SZ `
  --ts-code 600519.SH `
  --start-date 20240101 `
  --end-date 20260330
```

### Customs summary only
```powershell
C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe F:\quant_data\AshareC#\scripts\update_affordable_data_bundle.py `
  --dataset customs_summary
```

## Progress Logging
- The script prints timestamped heartbeats for:
  - bundle start
  - dataset start
  - each date/code/url batch
  - dataset completion
  - bundle completion

## Current Limits
- `fina_indicator` is targeted, not full-universe by default.
- `customs_summary` is summary only and comes from `gov.cn` release pages.
- This bundle is a low-cost update layer, not an exchange-licensed institutional truth store.
