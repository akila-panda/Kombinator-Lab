# P09 acceptance — integrated analysis v1

Completed 13 November 2026. P09-A/B PASS. Local milestone: integrated-analysis-v1; phase checkpoint p09-complete. P10 has not started.

## Gate evidence

| Requirement | Result |
|---|---|
| Bounded real EUR/USD history | 1,539 Dukascopy BID H1 observations, January–March 2024. URLs, hashes, actual coverage and limitations in REAL_DATA_P09.md and real-data-p09.json. |
| Time/price integrity | Strict importer accepted ordered unique UTC hourly opens, finite positive OHLC with high/low bounds, and NY17 session calendar. Zero internal scheduled gaps; 623 closed slots including DST. No missing observations fabricated. |
| Applicable modules | H1/H4/D1 adapter runs succeeded. STRUCT structure/zones/breaks, FX Desk levels/FVG/OB/patterns, Scalper alignment/volatility and ForexDashboard daily pivots produced output. |
| Causality and repeatability | All canonical evidence available by replay; each timeframe's repeated full API response identical. Real 900-hour prefix unchanged after all later OHLC prices doubled. Full lifecycle/aggregation/archive regressions passed. |
| Explainable chart | Browser inspected HH 1.08424, BOS down 1.08364, OB 1.08260–1.08347 and March 28 bullish divergence. Selected SVG IDs matched backend finding IDs; divergence highlighted price and RSI panes. |
| Missing context honest | Weekly bias unavailable with 12 completed weeks; daily bias mixed. External sentiment explicitly unavailable. Snapshot annotations remain marked provisional/retrospective. |
| Browser workflow | Selected saved real dataset; verified source/coverage label, rendered chart/evidence, H1→Daily transition and removal of stale selected finding. No browser console errors observed. Screenshot: screenshots/p09-real-data.png. |
| Invalid import | Malformed OHLC rejected with HTTP 422. Decoder tests reject bad columns, nonfinite deltas, invalid time deltas, wrong granularity and zero multiplier. |

## Verification record

`./verify.sh` passed dependency consistency, the then-current 156-test suite, TypeScript/Vite production build (clean output directory), and real local HTTP startup/assets/import/replay/archive smoke. After adding seven decoder checks, the final complete suite passed **163 tests in 50.20 seconds**, with one pre-existing Starlette TestClient deprecation warning. No product dependency changed.

`scripts/accept_real_history.py` additionally passed all real-data API scenarios and wrote the reproducible report. `PORT=8766 ./start.sh` successfully started the application for browser verification; it has been stopped. Git whitespace checks passed. Source package excludes .data, environments, node_modules and raw provider downloads.

## Known limits and deferred work

No unresolved observed data-timing or misleading-output blocker remains for the integrated analysis gate. This is software acceptance, not validation of profitable predictions or historical provider delivery latency. Hourly bid candles do not supply spreads, tick paths, slippage or executable fills. Dataset edges do not imply coverage of the whole calendar quarter. The imported-source trust label remains unverified; exact acquired bytes are separately hashed in the report. Provider revisions may change later downloads.

P10–P16 simulator clock/date selection, forming bars, orders, exits/accounting, journal/training and simulator acceptance remain deferred. No claim of 2022 minute coverage is made. Live providers, news, alerts, broader instruments and broker execution remain deferred. Upstream license/notice limits before wider redistribution remain documented in PROVENANCE.md. Full upstream feature parity is not claimed.

Next: P10-A only after explicit user authorization. Acquire bounded minute-level data with coverage; implement replay clock and controls before any order execution model.
