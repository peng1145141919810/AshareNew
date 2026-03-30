# Customs Source Findings

## Conclusion
- The official free source exists.
- The official free source is not currently stable for automatic ingestion from this environment.

## Official Source Confirmed
- National Bureau of Statistics methodology note states that:
  - `stats.customs.gov.cn` is the official online query endpoint
  - it is open to the public without registration
  - it supports monthly formal data since 2017 by:
    - country/region
    - commodity at 2/4/6/8-digit level
    - trade mode
    - province
- Source:
  - https://www.stats.gov.cn/zs/tjws/zytjzbqs/zckze/202501/t20250121_1958385.html

## Environment Result
- `online.customs.gov.cn` is reachable from this machine.
- `stats.customs.gov.cn` returns anti-bot / gateway failure symptoms here:
  - HTTP `412` challenge page with JS protection on plain HTTP requests
  - HTTP `504` on HTTPS in this environment
  - headless-browser probe only obtains anti-bot cookies and an empty page body, not usable query content

## Practical Meaning
- Customs aggregate monthly data is not blocked by lack of official truth.
- It is blocked by access mechanics in the current environment.
- Therefore:
  - do not fill the customs truth layer with scraped substitutes
  - do not replace it with proxies
  - keep it marked `blocked` until one of the following is validated

## Acceptable Next Paths
- Path A:
  - manual browser export from the official query site, then deterministic import
- Path B:
  - non-headless browser automation that passes the official site challenge and exports deterministic files
- Path C:
  - official monthly bulletin / quick-release files from the customs portal if a stable downloadable table URL is confirmed

## Working Alternative Source
- `gov.cn` official release pages are currently the most practical automatic source for a customs summary truth layer.
- Scope currently supported:
  - monthly or cumulative national import/export summary
  - release date
  - official source URL
- Scope not supported:
  - full country tables
  - full commodity-code tables
  - province / trade-regime complete detail

## Additional Finding
- The official English customs site has indexed monthly statistics pages under:
  - `https://english.customs.gov.cn/Statics/<uuid>.html`
- Search-engine indexed examples confirm official pages such as:
  - `(1) China's Total Export & Import Values, Dec 2025 (in USD)`
  - `(4) China's Total Export & Import Values by Country/Region, Dec 2025 (in USD)`
  - `Review of China’s Foreign Trade in the First Quarter of 2025`
- In the current environment, direct requests to these `english.customs.gov.cn/Statics/...` pages also return gateway failure, so the path is promising but not yet locally ingestible as an automated source.

## Local Diagnostic Tool
- `python F:\quant_data\AshareC#\tools\probe_customs_source.py`
