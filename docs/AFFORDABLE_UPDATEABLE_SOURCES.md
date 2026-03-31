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
- `ccgp_bid_awards`
- `ppi_market_digest`
- `internal_expectation`

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

### Local Research Model
- `internal_expectation`
- Source mix:
  - local blend over existing low-cost rows already in `affordable_data_v1.sqlite3`
  - current inputs:
    - `forecast`
    - `express`
    - `fina_indicator`
    - `daily_basic`
    - `stock_basic`
- Scope:
  - research-only internal expected-profit / revision layer
  - not analyst consensus
  - not canonical truth

### Procurement And Supply-Chain Raw Additions
- `ccgp_bid_awards`
  - Source:
    - `https://www.ccgp.gov.cn/cggg/zygg/zbgg/`
  - Current output:
    - latest central-government procurement bid-award list items
    - title
    - publish time
    - region
    - purchaser
    - source URL
- `ppi_market_digest`
  - Source:
    - `https://www.100ppi.com/`
  - Current output:
    - latest homepage focus / forecast digest items
    - title
    - source URL
    - digest type
  - Current implementation note:
    - the script first solves the lightweight `HW_CHECK` cookie challenge before parsing the homepage

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
- `internal_expectation` is an internal model layer and must not be renamed or consumed as analyst-consensus truth.
- `ccgp_bid_awards` is a raw public-procurement feed, not a normalized supplier-chain fact table yet.
- `ppi_market_digest` is a headline/digest raw layer, not a structured full commodity price panel yet.
- This bundle is a low-cost update layer, not an exchange-licensed institutional truth store.

## Current Supply-Chain Alternatives To The Gated CNEPTP Platform
- Procurement / tender raw layer:
  - `https://www.ccgp.gov.cn/cggg/`
  - `https://www.ccgp.gov.cn/cggg/zygg/zbgg/`
  - `https://bigdata.cebpubservice.com/`
- Commodity / spot-price / inventory public web layer:
  - `https://www.100ppi.com/`
- Official macro and customs summary layer:
  - `https://www.gov.cn/`
  - `https://www.stats.gov.cn/`
- Current operating truth:
  - these are usable substitute discovery sources after `cneptp` was judged permission-gated for a personal operator
  - they are not a one-for-one replacement for the full `cneptp` risk/price/supplier database
  - current environment status:
    - `ccgp` is directly fetchable
    - `100ppi` is fetchable after lightweight challenge-cookie handling
    - `cebpubservice` is still blocked by `403` in the current environment and is not yet in the automatic bundle
