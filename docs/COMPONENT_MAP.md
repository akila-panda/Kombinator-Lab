# Component and call map

**Current P04 flow:** UI → dataset-ID API → P03 timeframe service → shared snapshot/context/indicator bundle → adapters → canonical envelope and legacy UI fields. See [current adapter coverage and policies](ANALYSIS_ADAPTERS.md). The original P01 inventory below is retained as historical evidence; its storage/API/duplicate-calculation descriptions are superseded by P03/P04.

## Historical P01 map

Recorded 10 November 2026. `source-inventory-p01.json` records exact local/upstream hashes and definitions for 18 files. Reproduce it with:

```bash
.venv/bin/python scripts/source_inventory.py /path/to/extracted/repos
```

This generator checks unchanged copies byte-for-byte and verifies the four extracted function/method bodies structurally against their originals. It does not require running the original applications. Hashes describe the P01 snapshot, not a promise that later phases will leave those files unchanged.

## Active flow

`frontend/src/main.tsx` → `/api/demo` or browser CSV import → `POST /api/analyze` → `backend.main.AnalysisRequest` validation → `backend.analysis.analyze` → selected module functions → normalized JSON → chart, indicator panel, evidence list and cards.

Only `/api/health`, `/api/demo` and `/api/analyze` are application API endpoints. Static assets are served from `frontend/dist`. Uploaded candles/snapshots are in memory; there is no data store, account connection, order engine or simulator.

| Origin | Active functions | Actual caller and output |
|---|---|---|
| STRUCT.ai | `detect_swings`, `swings_to_zigzag_lines` | `analysis.analyze`; swing points and zigzag geometry |
| STRUCT.ai | `classify_structure`, `detect_trend` | `analysis.analyze`; labels and snapshot trend |
| STRUCT.ai | `detect_zones` | `analysis.analyze`; supply/demand zones |
| STRUCT.ai | `detect_bos`, `detect_choch` | `analysis.analyze`; snapshot structural break events |
| STRUCT.ai | `compute_momentum` | `analysis.analyze`; body/range metrics using FX Desk ATR |
| STRUCT.ai | `compute_atr14`, `pip_size`, `asset_class` | Internal dependencies of BOS, swings, structure and zones |
| STRUCT.ai | `TradingChart` | `frontend/src/main.tsx`; candles, structure, zones, S/R, BOS/CHoCH and added EMA series |
| FX Signal Desk | `ema`, repaired `rsi`, `atr`, effective `pivot_idx` | `analysis.analyze`, `bias`, `divergences`, FX patterns/zones; indicator arrays and reference calculations |
| FX Signal Desk | `find_fvgs`, `find_obs` | `analysis.analyze`; `fx_zones` and evidence list (not chart regions yet) |
| FX Signal Desk | `sr_levels`, `more_candles` | `analysis.analyze`; chart S/R and latest candle patterns |
| FX Signal Desk | `sessions.NY` | Import dependency of `zones`; no active session-box interface |
| Scalper Agent V2 | `TechnicalAlignment.check_h1_alignment` | `analysis.analyze`; EMA20/EMA50 and latest-close momentum, called on the selected timeframe despite its historical H1 function name |
| ForexDashboard | `calculate_pivot_points` | `analysis.analyze`; previous complete daily pivot levels |
| ForexDashboard | `SnapshotStrategy.analyze_orderbook`, `analyze_positionbook` | `analysis.sentiment`; injected `BookReader` supplies imported snapshots and percent buckets |
| New integration | `frame`, `aggregate`, `bias`, `sentiment`, `divergences`, `clean` | Shared orchestration; these are not full upstream application integrations |

## Ownership and overlaps

| Concept | Intended primary owner | Current overlap / follow-up |
|---|---|---|
| Swings, labels, supply/demand | STRUCT.ai | Snapshot-dependent revisions; event lifecycle is P05 |
| BOS/CHoCH | STRUCT.ai | Uses current snapshot trend and ATR; historical causality is not fully established |
| S/R, FVG, order blocks | FX Signal Desk | STRUCT chart retains alternate OB/FVG helpers; toggles are disabled. Remove competing active paths in P07 |
| EMA/RSI/ATR | FX Signal Desk canonical indicator layer | Scalper calculates EMA independently; STRUCT BOS uses another ATR. Consolidate/calibrate in P04 |
| RSI divergence | New integration replacement | Broken Scalper detector excluded; confirmation/revision handling still needs P05 |
| Momentum | STRUCT body/range metrics + Scalper close change | Distinct metrics, not independent confidence votes; definitions must be explicit in P04 |
| Regime | Future selected Scalper adapter | No full regime detector connected today |
| External sentiment | ForexDashboard snapshot scoring | No live fetcher, historical archive or independently verified source provenance |
| Daily/weekly bias | New rule engine | Current EMA-only prototype; replace in P08 |

`fxdesk/indicators.py` contains two `pivot_idx` declarations. Python uses the second. It is retained in this phase to preserve the baseline; rationalize it with tests in P04 rather than treating both as independent implementations.

## Changes relative to source

- STRUCT zone function signature repaired by moving optional `symbol` after required parameters; its source body retained.
- STRUCT chart receives backend EMA series; its old SL marker is relabelled `Selected` for evidence inspection.
- FX RSI replaced with Wilder recurrence and explicit boundary/warmup behavior.
- Scalper method body retained; source config/singleton/startup replaced by a local wrapper with EMA20/50 settings.
- ForexDashboard pivot and two scoring method bodies retained; wrapper injects a snapshot reader and fixed default contrarian thresholds.
- Frontend type declarations extracted without original API hooks or broker components.

## Intentionally not connected

Original broker execution and account configuration; MT5 bridge; bundled executable; original authentication/GUI startup; Scalper's price-derived institutional/retail positioning labels and faulty divergence; full ML/regime engines; original automated strategies; news sources; live alerts; live sentiment access; upstream full application test suites. These exclusions prevent importing unrelated app behavior and do not imply those features were validated.

## Licence/source record

- FX Signal Desk: complete supplied MIT licence and copyright notice retained.
- ForexDashboard: complete supplied MIT licence and copyright notice retained.
- STRUCT.ai and Scalper: supplied README MIT declarations retained; separate complete licence files were absent from those ZIPs. Attribution/notice completeness remains unresolved before broader redistribution.
- React, React DOM and Lightweight Charts licence files retained; chart attribution is visible.
- Full transitive dependency licence review is not complete and is not claimed by P01.

Upstream archives are not edited. See `PROVENANCE.md` for paths and extraction details and `source-snapshots.json` for archive hashes.
