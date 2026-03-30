# Affordable Source Roadmap

## Constraint
- Current affordable stack:
  - free official sources
  - free public truth-like sources only when clearly labeled and cross-checked
  - Tushare at current `2000` points
  - Tushare at future `8000` points
- Out of scope by default:
  - Wind
  - iFinD
  - CSMAR
  - exchange bulk license products

## Usable Now

### Free Official
- Listed company disclosures:
  - CNINFO
  - SSE
  - SZSE
- Macro and official releases:
  - gov.cn
  - stats.gov.cn
  - pbc.gov.cn
  - safe.gov.cn
  - customs.gov.cn
- Index methodology and some sample files:
  - csindex.com.cn

### Tushare At 2000 Points
- Daily market data:
  - `daily`
  - `adj_factor`
  - `daily_basic`
- Corporate fundamentals and event tables:
  - `forecast`
  - `express`
  - `fina_indicator`
  - `dividend`
  - `stk_holdertrade`
- Some market-behavior and connectivity data:
  - `ggt_daily`
  - many standard stock/fundamental tables

## Usable After Upgrade To 8000 Points
- Sell-side earnings forecast data:
  - `report_rc`
- This is the most important affordable upgrade because it partially covers the previously blocked analyst-consensus / forecast area.

## Source Priority By Dataset

### Price / Valuation / Turnover
- Primary:
  - Tushare `daily`, `adj_factor`, `daily_basic`
- Truth class:
  - `vendor_truth_like`
- Note:
  - acceptable for research and derived features
  - do not label as exchange-official truth

### Announcements / Financial Reports / Contract Announcements
- Primary:
  - CNINFO / SSE / SZSE disclosure pages
- Secondary:
  - Tushare announcement-related convenience data only as fetch helper
- Truth class:
  - `issuer_disclosure_truth`

### Earnings Forecast / Revision
- Current practical path:
  - before 8000 points: blocked for truth use
  - after 8000 points: test `report_rc`
- Truth class:
  - `vendor_truth_like`
- Note:
  - still not equal to a fully licensed institutional consensus master, but much better than heuristic proxies

### Northbound / Stock Connect
- Primary:
  - HKEX official disclosures when available
- Secondary:
  - Tushare connectivity tables if available for usable history
- Truth class:
  - `exchange_truth` when from HKEX
  - `vendor_truth_like` when from Tushare

### Financing / Margin Trading
- Primary:
  - SSE / SZSE official data pages
- Secondary:
  - Tushare only if clearly mapped and cross-checked

### Customs
- Summary layer:
  - gov.cn official release pages
- Detail layer:
  - blocked until official detailed source is programmatically reachable

## Hard Rules
- Do not fill missing truth with proxies just because a dataset is inconvenient.
- If a field is sourced from Tushare, label it `vendor_truth_like`, not `official_truth`.
- If a field is sourced from issuer filing text, keep the raw filing as truth and any mapped theme/product/entity field as derived or inferred.

## Immediate Build Order
1. CNINFO / SSE / SZSE source map for announcement-driven datasets.
2. Tushare 2000-point source map for price / valuation / dividend / forecast / express / indicator tables.
3. gov.cn customs summary truth layer.
4. Re-evaluate analyst forecast ingestion after Tushare reaches 8000 points.
