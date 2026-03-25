# Bridge And Fidelity Rules

## Fidelity First

- This skeleton is a translation boundary, not a redesign license.
- Existing Python logic, authority boundaries, and operational sequencing are the source of truth.
- C# replacements must preserve:
  - research authority
  - release freeze authority
  - safety gate authority
  - OMS actual-state authority
  - broker dispatch as an execution arm only

## Bridge Strategy

- Python remains the active runtime for:
  - V6 planning
  - event ingest and extraction
  - industry router
  - V5 research
  - current broker execution scripts
- C# is introduced first around:
  - path governance
  - contract loading
  - scheduler representation
  - safety evaluation
  - OMS ledger catalog
  - operator command generation

## Cross-Language Rules

- Cross-language traffic should pass through explicit contracts, not ad hoc dictionaries.
- File contracts are preferred over implicit in-memory coupling.
- Generated commands must preserve the current Python entrypoints and flags.
- Any future C# executor must call Python using the canonical research Python or the dedicated gmtrade Python according to the current boundary.
