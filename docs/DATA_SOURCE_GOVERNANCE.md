# Data Source Governance

## Rule
- No field should enter the canonical truth layer unless its upstream source and licensing status are documented first.
- If a field only has proxy or inferred values available, it must stay outside the truth layer.

## Source Classes
- `official_truth`
  - regulator or official statistics authority
- `exchange_truth`
  - stock exchange or exchange-owned data service
- `issuer_disclosure_truth`
  - issuer-filed announcement or report on a designated disclosure platform
- `derived_from_truth`
  - deterministic transformation of truth fields
- `research_proxy`
  - heuristic or substitute measure that is not the real upstream field
- `model_inferred`
  - LLM, classifier, or extraction/inference result

## Current Field Matrix
| Dataset / field family | Preferred source | Source class | Licensing | Notes |
| --- | --- | --- | --- | --- |
| A-share daily OHLCV, turnover, adjustment factors | SSE / SZSE official market data services | `exchange_truth` | paid required for robust historical bulk access | Exchange historical datasets are authoritative; do not treat scraped mirrors as truth. |
| Listed company announcements | CNINFO, SSE, SZSE disclosure pages | `issuer_disclosure_truth` | free official | CNINFO is the designated disclosure platform; exchange disclosure pages are also authoritative publication channels. |
| Financial statements and ad hoc reports | CNINFO, SSE, SZSE issuer filings | `issuer_disclosure_truth` | free official | Parse directly from filed reports; extracted fields remain `derived_from_truth` only after deterministic normalization. |
| Official indices and constituents | CSI / CNI / exchange index pages and files | `exchange_truth` | mixed: free summary, some history/licensing paid | Use official constituent/factsheet files; full history may require license. |
| Macro statistics | NBS, PBOC, SAFE | `official_truth` | free official | Prefer official release tables and avoid secondary republishes. |
| Customs aggregate monthly trade | GACC / Customs statistics portals | `official_truth` | free official for aggregate releases | Use official aggregate tables only; company-level customs data is generally not publicly free. |
| Tender / procurement notices | Government procurement portals and issuer-filed bid announcements | `issuer_disclosure_truth` for filed notices, otherwise public notice truth with mapping derived separately | free official/public | Raw notice is truth; mapping from notice to listed company/theme is not truth and must stay separate. |
| Company contract / order announcements | CNINFO, SSE, SZSE filings | `issuer_disclosure_truth` | free official | Contract amount/date/title from filings can be truth; theme mapping remains derived. |
| Analyst consensus EPS / revision | Wind / iFinD / CSMAR or equivalent licensed vendor | commercial truth-like vendor feed | paid required | No reliable free official PRC source was identified for broad historical sell-side consensus and revision panels. Do not replace with announcement proxies in the truth layer. |

## Free Official Sources Confirmed
- CSRC disclosure rules:
  - https://www.csrc.gov.cn/csrc_en/c102030/c1371072/content.shtml
- Shanghai Stock Exchange market data / announcements / historical data service:
  - https://english.sse.com.cn/markets/dataservice/products/
- CNINFO disclosure platform:
  - http://www.cninfo.com.cn/
- National Bureau of Statistics:
  - https://www.stats.gov.cn/
- PBOC:
  - http://www.pbc.gov.cn/
- SAFE:
  - http://www.safe.gov.cn/
- General Administration of Customs:
  - http://www.customs.gov.cn/

## Paid-Required Gaps
- Broad, historical analyst consensus EPS / target / revision panel for A-shares:
  - likely vendors: Wind, Tonghuashun iFinD, CSMAR
  - status: paid required
- Robust licensed historical exchange bulk data for authoritative production-grade archive use:
  - SSE / SZSE official data services
  - status: typically paid required for bulk historical or redistribution use

## Implementation Rule
- Before any future backfill:
  1. Write the field list.
  2. Assign a source class to each field.
  3. Mark each field as `free official`, `free nonofficial`, or `paid required`.
  4. Block implementation for any canonical field that lacks a defensible source.
