# Initial repository audit and integration plan

Date: 9 November 2026

## Scope and result

Inspected the four supplied ZIP snapshots. Extracted source is under `work/repos/` in this workspace. The original archives were not modified. SHA-256 hashes in `source-checks.json` identify the supplied snapshots; a Git commit was not established from these ZIPs.

This is a first-pass source audit and focused calculation check, not a completed runtime, security, dependency, or trading-performance audit. No applications, broker connections, bundled executables, or trading workflows were launched. No upstream code has been repaired yet.

Recommendation: build a shared analysis application and selectively adapt components. Do not merge the four applications wholesale.

## Findings with source evidence

Paths below are relative to `work/repos/`.

1. **STRUCT.ai has two Python syntax blockers.** `Sturct-ai-main/artifacts/trading-api/services/zones_engine.py:46` places required `swings` after optional `symbol`; `services/candle_pattern_engine.py:78` does the equivalent for `df` and `swings`. Python rejects these declarations. `routers/structure.py` imports both modules, and `routers/narrative.py` imports the zones module. Repair signatures and inspect every caller before evaluating runtime behavior.

2. **Scalper RSI-divergence predicates cannot identify the intended patterns.** `forex-scalper-agent-v2-main/consensus_validator.py:374–399` selects lows ascending and highs descending, then asks whether the second low is lower or the second high is higher. Both strict price predicates are false for ordinary numeric values regardless of RSI. The same defect exists in `analysis/consensus_validator.py:370–395`. A focused check of all 24 permutations of four distinct prices reproduced the ordering problem. Replace this detector with chronological, confirmed swing comparisons; merely sorting the selected two prices by time still does not establish suitable swing points.

3. **FX Signal Desk returns undefined RSI on an uninterrupted rising series.** `FX-Signal-Desk-main/fxbot/indicators.py`, function `rsi`, replaces zero average loss with NaN. Executing this isolated function on closes 1 through 40 returned NaN at the last candle, where the rising-series boundary should be 100. Define and test rising, falling, flat, and warmup behavior before reuse.

4. **Scalper's positioning labels describe technical proxies.** `forex-scalper-agent-v2-main/sentiment_analyzer.py:269–290` derives retail sentiment from RSI and institutional bias from EMAs. These values should be labelled technical assessments, not externally observed trader positioning.

5. **STRUCT.ai swings need replay-specific handling.** `Sturct-ai-main/artifacts/trading-api/services/zigzag_engine.py` uses bars on both sides of a pivot, returns the pivot timestamp, and can replace the last same-kind pivot with a later, more extreme pivot. Its spike filter also uses the median range of the entire supplied frame. These source observations require confirmation timestamps, explicit provisional states, and prefix-replay tests before historical outputs can be treated as information available at that time. This pass did not execute a full replay to quantify the effect.

6. **ForexDashboard backtesting is not implemented.** `ForexDashboard-main/ForexDashboard.py:2806–2833` creates a placeholder tab and explicitly states that no backtesting functionality is implemented. Its OANDA adapter and scoring code are candidates for extraction; the Tkinter application is not a reusable React frontend.

7. **Licence artifacts differ.** FX Signal Desk and ForexDashboard include MIT licence files with copyright notices. STRUCT.ai and Scalper state MIT in their READMEs, but no separate licence file was found in these supplied archives. Preserve available notices and resolve attribution details before distributing adapted code. Bundled dependency licences have not been audited.

## Proposed integration map

| Source | Candidate contribution | Initial decision |
|---|---|---|
| STRUCT.ai | React chart experience, structure labels, zones, FVGs, narrative concepts | Adapt after fixing syntax and validating confirmation timing; avoid carrying over its entire runtime |
| FX Signal Desk | Price action, levels, sessions, indicators, historical testing patterns | Reuse selectively after running existing tests and fixing indicator boundary behavior |
| Forex Scalper Agent V2 | EMA/momentum and regime-analysis concepts | Audit selected functions; replace divergence; relabel price-derived sentiment |
| ForexDashboard | OANDA order/position-book retrieval and scoring | Extract into a separate optional data adapter; validate failure and freshness behavior |
| New shared code | Canonical candles, findings, daily/weekly bias, replay coordination | Build explicitly; no complete combined implementation was established in this pass |

## Target architecture

One React interface and one Python/FastAPI backend. Adapters supply candles and external sentiment to independent analysis modules. Modules produce a shared finding format consumed by chart overlays and explanations.

Canonical candles need instrument identifier, timeframe, UTC open/close times, OHLC, volume type, provider, and completed/forming status. Instrument metadata must explicitly define price precision and pip/tick sizes. Daily and weekly boundaries need a documented session/timezone convention.

Each finding needs an ID, module/version, instrument, timeframe, kind, direction, exact price or zone bounds, evidence candle IDs, occurrence time, confirmation time, status, explanation, and invalidation condition. Historical replay must expose only findings knowable by its current clock.

Keep technical state, sourced positioning sentiment, daily bias, and weekly bias separate. External sentiment needs provider, observation time, retrieval time, and availability/freshness status. Missing data must remain unavailable. Bias rules should expose supporting and conflicting evidence instead of disguising a heuristic score as a calibrated probability.

## Implementation sequence and acceptance gates

1. Establish an isolated development environment, repair the syntax blockers on working copies, and run FX Signal Desk's existing tests. Define indicator conventions and check EMA/RSI against deterministic fixtures.
2. Implement canonical historical candles and a prefix-replay harness. Check gaps, duplicates, sorting, resampling, session boundaries, and forming candles. Test pivot confirmation and invalidation explicitly.
3. Deliver a historical EUR/USD chart with pair/timeframe controls, structure, zones, key prices, EMA/RSI, and clickable evidence. EUR/USD is a proposed default, not a user-selected requirement. Decide the historical data source before this milestone.
4. Add chronological RSI divergence, momentum, and price-action detectors, with stable evidence IDs and replay regression cases.
5. Add separately defined daily/weekly bias and optional external sentiment. Verify historical availability of sentiment before including it in replay; otherwise show it unavailable.
6. Add live data and alerts only after the historical workflow is validated. Broker execution is outside this proposed initial implementation scope.

## Validation performed and remaining

- Parsed all 169 Python source files: 167 parsed successfully; the two STRUCT.ai files above failed.
- Executed the isolated FX Signal Desk RSI rising-series case: failed as described.
- Checked the Scalper sorted-extreme predicates over 24 price permutations: confirmed the ordering defect. This is a predicate reproduction, not an end-to-end execution of the validator.
- Found six FX Signal Desk test modules. The repository test suite was not run: pytest and yfinance are absent from the current Python environment. No tests were found in the other three archives by filename inspection.
- Frontend build, full imports, dependency installation, live providers, complete detector coverage, and all application startup flows remain unverified.

The next concrete task is to establish the isolated test environment and complete the calculation/replay audit before choosing the final implementation base.
