# P04 analysis adapters and indicator policy

P05 update: snapshot annotations are now explicitly retrospective/provisional under contract 1.2.0. A separate chronological lifecycle run shares the snapshot ID and uses full-prefix indicators; see HISTORICAL_EVENTS.md. This document records P04’s selected adapter behavior.

## Shared run context

`backend.analysis.analyze` creates one `MarketSnapshot` before calculations. `AnalysisContext` carries that same typed snapshot, the last 500 completed selected-timeframe bars, completed daily history and a shared indicator bundle. STRUCT, FX Desk, Scalper, ForexDashboard, replacement divergence and book sentiment execute through `adapters.run`. The additive `module_runs` response reports each run's snapshot ID and calculation version `p04-adapters-v1`; canonical envelope uses that exact snapshot. Run status `succeeded` means execution succeeded, not that data or a signal is available. Missing external sentiment still returns unavailable; absent completed daily history produces no pivots.

Vendor detectors receive DataFrames derived from the validated P03 service, without startup of any original application. Context objects are frozen; pandas objects are treated as read-only by convention. Fixtures check selected adapters do not mutate the shared candle frame. Existing legacy response fields remain for the chart, alongside the normalized canonical findings, overlays and assessments. Contract schema remains 1.1.0; calculation versions change independently.

## Coverage

| Adapter | Connected functions | Shared calculations / normalized output |
|---|---|---|
| STRUCT | swings, zigzag geometry, structure labels/trend, supply/demand, BOS, CHoCH, body/range momentum | Canonical ATR injected into BOS and body ratio; canonical structural findings and zone overlays |
| FX Desk | S/R, FVG, order blocks, latest candle patterns | Shared ATR series/scalar; zone findings/geometry, S/R and pattern assessments |
| Scalper | EMA alignment and latest-close percent change | Same EMA20/50 values as chart, without separate calculation or early rounding; canonical assessment |
| Scalper selected regime | ATR volatility branch from `analysis/regime_detector.py` | ATR14 versus mean of its last 20 observations: high above 1.5×, low below 0.6×, normal otherwise; zero reference is explicitly flat. `volatility` response and canonical assessment |
| Integration | Chronological adjacent-pivot RSI divergence | Shared RSI14; existing right-hand confirmation and canonical evidence references |
| ForexDashboard | Classic daily pivots, optional imported position/order books | Same clock and dataset snapshot; daily completed OHLC only; book availability/provenance rules preserved |

No confidence/probability is inferred from volatility or alignment. STRUCT's `atr_regime` remains its distinct recent-versus-older **high-low range** heuristic, not a second ATR implementation. Scalper volatility is price-derived technical analysis, not external positioning sentiment. UI display of the new volatility assessment belongs to P07.

## Canonical indicators (`p04-indicators-v1`)

- **EMA(n):** recursive alpha `2/(n+1)`, seed first close (`adjust=False`), outputs unavailable until n observations. Flat series returns the flat price. Equal EMA20/50 reports neutral, unaligned, not bearish.
- **ATR(n):** true range is max(high-low, abs(high-previous close), abs(low-previous close)); first observation uses high-low. Seed is the mean of the first n true ranges; thereafter Wilder recurrence `(previous*(n-1)+TR)/n`. First n-1 values unavailable; flat zero-range series returns zero.
- **RSI(n):** Wilder gain/loss averages seeded from the first n changes; first n closes unavailable. Zero gains/losses yields 50, gains with zero losses 100, losses with zero gains 0.
- Periods must be positive integers. Missing/nonfinite numeric values raise errors; never forward-filled. Indicators count observed completed bars rather than elapsed wall-clock slots. P03 reports missing scheduled bars and closures in snapshot quality flags; gaps do not create synthetic bars or restart warmup. True range includes the jump from the last observed close. This policy does not make gap-containing data complete or reliable.
- Calculations on the selected timeframe share one bundle for the last 500 candles; chart arrays omit unavailable warmup values. Daily/weekly EMA prototype bias computes on its separate completed timeframe history. These are intentionally separate input series, not duplicate selected-timeframe calculation paths.

P04 changes numerical behavior: STRUCT's rolling-average ATR and FX Desk's first-TR seeded EMA smoothing are replaced with the shared SMA-seeded Wilder ATR. Detector thresholds can therefore change. EMA warmup is now explicit and Scalper's EMA output is no longer rounded before the UI formats it. RSI's P02 behavior remains unchanged. Calculations remain snapshot-based; moving the last-500 window can revise findings.

## Failure behavior

An adapter exception, missing required output keys, or nonfinite numeric output raises `ModuleFailure` with its module name. Both API paths return HTTP 500 with `detail: {error: "module_failed", module: "fxdesk", message: "fxdesk analysis failed"}` (example). No partially successful chart or neutral fallback is returned. Internal exception text is not exposed to API clients. Invalid user input remains HTTP 422; final canonical output validation failure remains a distinct HTTP 500 boundary error. The retained Scalper exception-return dictionary is promoted to an error by its adapter.

## Revision-prone rules and exclusions

STRUCT swings alternate and can replace an earlier extreme; labels and trend depend on the current sequence. BOS uses current snapshot trend and latest ATR threshold. CHoCH selects recent HL/LH levels using snapshot trend. Supply/demand freshness, quality and geometry can revise. FX FVG/OB arrays drop invalidated zones and re-sort by current distance; S/R clusters and pattern availability change with the window. These remain provisional snapshots, not permanently recorded historical events. P05 owns lifecycle/causality fixes.

Excluded: Scalper ML/ADX/full regime classifiers, adaptive strategy/risk recommendations, original faulty divergence and price-derived retail/institutional sentiment, unused FX indicators/pattern engines, broker execution, accounts, live feeds and original application startup. Only the volatility threshold branch of the regime detector is selected; no full regime classification is claimed. Disabled frontend OB/FVG helper paths remain P07 work.

## Attribution and fixtures

Source archive identities remain in `source-snapshots.json`; P01 provenance is historical and retained. `source-inventory-p04.json` records exact current hashes and adaptation reasons. Run `scripts/source_inventory_p04.py /path/to/extracted/repos` to check unchanged files and source hashes. Run the original P01 inventory generator only from the P01 checkout.

Fixtures cover seeded EMA/ATR/RSI numeric results, flat/warmup/nonfinite inputs, explicit observed-bar gaps, shared EMA equality and ATR injection, FVG/OB geometry and invalidation, repeated-price S/R, candle patterns, swing ordering, HH/HL/LH/LL classification, BOS/CHoCH break direction/time, supply/demand geometry, pivot values, selected volatility thresholds, adapter input preservation, both API failure paths and common snapshot IDs. Existing replay-prefix, divergence-confirmation, sentiment and dataset/calendar suites remain part of acceptance. These tests validate selected integrations, not strategy profitability or all upstream algorithms.
