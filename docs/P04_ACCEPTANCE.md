# P04 acceptance — integrated analysis adapters

Completed 11 November 2026. P04-A, P04-B and P04-C complete. **Wait for explicit authorization before P05.**

## Delivered

- One typed market snapshot/context shared by selected STRUCT, FX Desk, Scalper, ForexDashboard, divergence and sentiment adapters. Additive `module_runs` records snapshot ID, execution status and calculation version.
- Canonical indicator bundle computed once for selected-timeframe analysis; shared EMA values and ATR inputs injected into connected algorithms. Shadowed pivot declaration removed; old active ATR/EMA variants replaced.
- Explicit warmup, Wilder ATR/RSI seeds, flat-series behavior and observed-bar missing-data policy. Equal EMAs no longer imply bearish alignment.
- Selected Scalper ATR volatility branch adapted with source attribution, without ML/ADX/classification/confidence claims. Canonical volatility assessment is available; UI presentation remains P07.
- Named module errors on both API paths, no neutral fallback or partial-success chart. Canonical response validation remains active.
- Coverage/revision/exclusion documentation in ANALYSIS_ADAPTERS.md and exact source mapping in source-inventory-p04.json. No new dependencies, original archives unchanged.

## Verification

`./verify.sh` passed: **117 tests**, dependency consistency, TypeScript/Vite production build, and real HTTP startup/assets/legacy analysis/CSV import/metadata/range/dataset-ID analysis. Full test duration 13.73 seconds in the existing project environment. The prior Starlette TestClient httpx deprecation remains the only test warning.

23 added adapter/indicator cases cover numeric seed/recurrence fixtures, warmup/flat/nonfinite values, common snapshot IDs, matching EMA outputs, prevention of duplicate ATR calls, no mutation of shared candles, named module failures (legacy and dataset API), malformed output, FVG/OB geometry/invalidation, S/R, candle patterns, swing ordering, labels, BOS/CHoCH time/direction, supply/demand geometry, pivot values, selected volatility thresholds and observed-bar gap semantics. Existing divergence confirmation, prefix-causality, book sentiment, dataset and calendar checks passed.

Provenance generator checked 19 mappings, unchanged P01 local files and upstream hashes. `git diff --check` passed. Synthetic canonical examples regenerated and validated by the suite. Frontend code/bundle unchanged; no new browser QA was needed or claimed. P03's blocked browser file-selection check remains a known test limitation.

## Consequential behavior changes

Wilder SMA-seeded ATR replaces STRUCT rolling ATR and FX Desk first-observation seeded smoothing, so threshold-based findings can differ from P03. EMA warmup is now withheld, and Scalper returns exact shared EMA values. Regime thresholds are heuristics, not probabilities. All are documented and versioned `p04-adapters-v1` / `p04-indicators-v1`. Contract remains 1.1.0; storage remains v1.

## Next handoff

P05-A: historical finding lifecycle and causality. STRUCT's alternating swings, current-trend break classification, latest-ATR BOS buffer, zone freshness and FX zone filtering remain snapshot-dependent and provisional. No permanent event history or simulator is implemented in this phase. No real provider data obtained. HTTP smoke server shut down; no persistent server started.

Checkpoint: `p04-complete`; source ZIP excludes datasets, environments and Git. Start P05 only after user says “Proceed”.
