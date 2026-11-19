# Source provenance and local changes

Sources are user-supplied ZIP snapshots received on 9 November 2026. Hashes are recorded in source-snapshots.json. No Git commit identity is inferred from the archive names.

## STRUCT.ai — Kiyolegend/Sturct-ai

Original `artifacts/trading-api/services/` files copied into `backend/vendor/struct/`: pip_utils, zigzag_engine, structure_engine, trend_engine, zones_engine, momentum_engine, atr_utils, bos_engine, choch_engine.

Original `artifacts/trading-dashboard/src/components/TradingChart.tsx` retained in `frontend/src/components/TradingChart.tsx`. Only the necessary interface declarations from `hooks/use-trading-api.ts` and `components/TopBar.tsx` were retained, avoiding original network hooks and broker UI.

Modifications: moved optional `symbol` to the end of `detect_zones` to repair its syntax while preserving positional call compatibility; added externally supplied EMA series to the chart; renamed the repurposed SL selection marker to “Selected”. Original internal frontend OB/FVG helpers remain in the copied chart but their toggles are disabled so they do not conflict with the backend FX Signal Desk findings. No original broker routes are imported.

README licence declaration: “MIT”. The supplied ZIP lacks a separate licence file. Original README excerpt is preserved alongside this document; authorship/notice completeness still needs resolving before redistribution beyond the local project.

## FX Signal Desk — luciferalive/FX-Signal-Desk

`fxbot/indicators.py`, `zones.py`, `sessions.py`, and `patterns.py` copied into `backend/vendor/fxdesk/`. MIT licence text and copyright notice retained in `FX-Signal-Desk-main-LICENSE.txt`.

Modification: replaced RSI implementation with a documented Wilder recurrence seeded with the first 14 price changes. Warmup remains unavailable; flat prices give 50, gains without losses give 100, losses without gains give 0. Tests reproduce the original rising/flat failures and verify the repair.

## Forex Scalper Agent V2 — ayia/forex-scalper-agent-v2

Extracted `ConsensusValidator.check_h1_alignment` from root `consensus_validator.py` into `backend/vendor/scalper.py` under `TechnicalAlignment`. Body retained; broker/config imports and singleton initialization omitted. The wrapper sets EMA periods 20/50 and labels the returned data as technical alignment, not independent positioning sentiment. The heuristic alignment score is not presented as a probability.

The original divergence code was not reused. New `backend.analysis.divergences` compares adjacent chronological confirmed pivots. The original price-derived retail/institutional sentiment estimate was not imported.

README licence declaration: “MIT License”. The supplied ZIP lacks a separate licence file; declaration excerpt retained here.

## ForexDashboard — HamoonSoleimani/ForexDashboard

Extracted `calculate_pivot_points`, `TradingStrategy.analyze_orderbook`, and `TradingStrategy.analyze_positionbook` from `ForexDashboard.py` into `backend/vendor/forexdashboard.py`. Scoring function bodies retained; new initialization accepts an injected snapshot reader and sets the upstream position thresholds to .65/.35. `backend.analysis.BookReader` adapts normalized JSON snapshots to those methods.

Tkinter startup, account credentials, live trading, and order submission are not imported. MIT licence text and copyright notice retained in `ForexDashboard-main-LICENSE.txt`.

## New integration files

`backend/main.py`: request validation, demo and analysis routes, optional static frontend serving.
`backend/analysis.py`: shared prefix processing, aggregation, adapters, evidence responses, divergence replacement, initial EMA bias.
`frontend/src/main.tsx` and `style.css`: unified interface and local import/replay flows.
`tests/test_integration.py`: integration regression checks.

Third-party libraries are installed through requirements.txt / frontend/package-lock.json. Lightweight Charts attribution is visible in the interface; its installed LICENSE and NOTICE are included in docs. This record does not replace a full dependency-licence audit.

## P04 adaptations (11 November 2026)

Canonical indicators now live in `backend/indicators.py`. FX exports point there and the shadowed duplicate pivot declaration was removed. FX FVG/OB/S/R and STRUCT BOS accept shared ATR input; STRUCT's standalone ATR helper delegates to the canonical implementation. Scalper accepts shared EMA values, retains exact EMA precision and treats equal EMAs as neutral/unaligned. Its original extracted method is therefore no longer byte/AST-identical. The volatility threshold branch (1.5 high / 0.6 low) of `analysis/regime_detector.py` was adapted into `backend/adapters.py`; ADX, full regime classification, ML and confidence code were not imported. Original archives remain unchanged. Current hashes, source mapping and adaptation notes are in `source-inventory-p04.json`; P01 inventory remains historical evidence.

## P05 causal replacements (11 November 2026)

`backend/lifecycle.py` is integration-owned chronological logic. It replaces retrospective event timing/selection rather than modifying upstream STRUCT/FX snapshot engines. FVG/OB displacement thresholds retain the selected FX Desk values; BOS retains STRUCT's 0.05 ATR ratio with instrument pip minimum, evaluated at the break rather than the latest snapshot. Strict pivot/confirmation, immutable revisions, structure references and explicit expiry are versioned integration policies. Shared P04 EMA/RSI/ATR formulas remain unchanged. Source snapshots and historical P04 inventory remain intact.

## P06 sentiment archive boundary (11 November 2026)

`backend/sentiment.py` is integration-owned local archive/provider selection. ForexDashboard scoring bodies are unchanged. Normalization, bucket validation, retrieval-time availability and named freshness policy are enforced before those methods; provenance is always unverified for uploaded records. No live source, credentials or provider code was added.

## Integrated analysis v1 (P09) current wiring

- STRUCT.ai vendor adapters supply selected-timeframe swings, labels, trend, BOS/CHoCH, supply/demand and momentum.
- FX Signal Desk supplies S/R, FVG, OB and candle patterns, with the shared canonical indicator bundle.
- Scalper supplies EMA alignment and selected volatility logic; no broker execution or invented institutional sentiment is imported.
- ForexDashboard supplies completed-session pivots and optional archived book scoring; the latter is visibly unavailable without eligible input.
- Integration-owned code supplies P03 datasets/calendars, P05 causal journal, P06 archive boundary, P07 canonical chart renderer and P08 horizon scenarios. TradingChart.tsx is inactive provenance code; AnalysisChart.tsx is the active renderer.

Earlier modification notes above describe their original integration checkpoints. Current inputs/availability are tested by P09_ACCEPTANCE.md; exact upstream ZIP hashes remain in source-snapshots.json. Real provider data provenance is separate in REAL_DATA_P09.md, with raw market files excluded from the package.

## P10 replay boundary

Integration-owned replay_api.py and Replay.tsx implement the clock and forming bars using existing dataset/calendar/analysis contracts. No upstream execution engine was imported. Minute provider decoding reuses the P09 decoder with explicit 60-second granularity; observed gaps remain intact. Data provenance is in minute-data-p10.json and REPLAY_CLOCK.md.

## P11 paper execution

orders.py and order_api.py are integration-owned deterministic entry execution code. No upstream broker/execution code or live connectivity was imported. The fixed spread is an explicit simulation policy, not sourced historical market data. Prices come from the existing immutable minute store. See PAPER_ORDERS.md for rounding, timing and gap rules.

## P12 account execution

accounting.py is integration-owned USD accounting and protective exit logic; it reuses P11 validation and preserves that endpoint. Fixed spread/slippage, commission rounding, USD/JPY conversion and conservative intrabar rules are explicit simulation policies, not provider execution claims. No broker or external account connection was added. See PAPER_ACCOUNT.md.
