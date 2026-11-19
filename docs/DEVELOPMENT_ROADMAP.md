# Confluence development roadmap

Main development entry point: [Updated development document](DEVELOPMENT_PLAN.md), including selected engineering improvements and their separate acceptance gates.

Version: 1.0 · Created: 10 November 2026

This is the development plan for combining the four systems, validating their shared analysis, and then adding a historical trading simulator. `DEVELOPMENT_STATUS.md` is the current progress and handoff record. Update that file at the end of every development session.

Extension planned 17 November 2026: [INDICATOR_DEVELOPMENT_ROADMAP.md](INDICATOR_DEVELOPMENT_ROADMAP.md) defines P17–P28 for the combined indicators. Complete P16 first. The extension does not change P01–P16 acceptance requirements or authorize starting another phase automatically.

## 1. Objective and agreed order

Build one local React/FastAPI application that analyzes historical or live candles, displays traceable findings, separates technical bias from external sentiment, and later supports realistic historical trading practice.

**Order: complete integration of the four systems → validate the integrated pipeline → build the simulator.** A running demo does not mean integration or analysis validation is complete.

Initial scope: EUR/USD first, with instrument metadata that allows other pairs later. Starting with EUR/USD is a working default. No real-money order execution is included. A provider or broker connection is not required for the early integration phases.

### Existing baseline

An integration preview exists in this project:

- STRUCT.ai chart, structure, supply/demand, BOS/CHoCH and momentum components.
- FX Signal Desk indicators, support/resistance, FVGs, order blocks and candle patterns.
- Scalper Agent V2 EMA/momentum function and a replacement chronological divergence detector.
- ForexDashboard pivot calculations and imported book-snapshot scoring.
- Synthetic demo, hourly CSV import, replay slider and preliminary EMA-only daily/weekly bias.

Recorded verification from 9 November 2026: 16 integration tests passed, frontend typecheck/build passed, and desktop browser checks covered rendering, evidence selection, timeframe switching and replay. These results have not been rerun for this planning document. They do not establish trading accuracy, full upstream feature parity or permanent historical confirmation behavior.

## 2. How to keep work within a session

A **phase** is a milestone with an acceptance gate. A **work packet** is the maximum planned scope for one development session. Most phases below have two packets so that a large milestone does not depend on one long chat.

1. Start by reading this roadmap and `DEVELOPMENT_STATUS.md` and checking the actual files. Select the next ready packet.
2. Write a short packet plan: intended change, files likely to change and checks needed.
3. Implement only that packet and its necessary fixes. Avoid opportunistic redesigns.
4. Run its targeted checks. At a phase boundary, run the relevant integration/build checks as well.
5. Reserve roughly the last quarter of the working session for verification, documentation and handoff.
6. If the packet grows, split it at a concrete boundary into named sub-packets. Record completed work and remaining work; do not mark it complete to fit the session.
7. Update the status document with changed files, checks and exact next action before ending the session.

Session duration and context limits vary, so the packet sizes are estimates, not a guarantee that a phase fits. A clean, documented incomplete packet is preferable to an unsupported completion claim.

**Default session scope: one packet.** Continue to another packet only when explicitly requested or when the selected packet was trivial and the user has authorized broader progress. Do not begin the next phase until the current phase's acceptance gate passes, except for documented dependency investigation.

### Universal completion criteria

A packet is complete only when:

- The behavior described for that packet exists and its targeted checks pass.
- Failure, missing-data and boundary cases relevant to the change are handled.
- No known blocker is hidden behind demo data or a silent fallback.
- Any changed API/schema and run instructions are documented.
- The handoff names unresolved limitations and the next packet.

A phase is complete only when all its packets and its acceptance gate are complete. Test counts alone are not an acceptance gate.

## 3. Component ownership and connections

| Component | Primary responsibility | Connection |
|---|---|---|
| Shared data layer | Instrument definitions, candles, data quality, timeframes | Supplies every analysis module from one timestamped snapshot |
| STRUCT.ai adapter | Structure, supply/demand, BOS/CHoCH and chart rendering | Consumes candles; emits evidence and overlay geometry |
| FX Signal Desk adapter | S/R, FVGs, order blocks, price action, canonical indicators | Consumes the same candles; emits findings and indicator series |
| Scalper adapter | EMA alignment, momentum and selected regime logic | Consumes canonical indicators/candles; emits technical assessments |
| ForexDashboard adapter | External position/order-book scoring | Consumes source-stamped historical/live books available at the shared clock |
| Shared finding layer | Identity, timing, status, evidence and provenance | Normalizes all adapter outputs for UI, bias and later journaling |
| Bias engine | Daily and weekly scenarios | Combines normalized evidence under explicit versioned rules |
| Replay service | One clock, visible history and derived timeframes | Later drives both analysis and simulated execution |
| Simulator | Orders, fills, positions, account and journal | Consumes replay events and instrument/execution settings |

Choose one primary detector for overlapping concepts. Initial ownership: STRUCT.ai for swing structure and supply/demand; FX Signal Desk for FVGs, order blocks, S/R and canonical indicators; the integration detector for RSI divergence. Preserve alternative algorithms only as named comparisons, not extra independent votes.

No analysis adapter imports a source application's broker execution, GUI startup or credential configuration.

## 4. Phase index

| Phase | Outcome | Session packets | Depends on |
|---|---|---|---|
| P01 | Reproducible baseline and source map | A, B | Existing preview |
| P02 | Canonical contracts and instrument rules | A, B | P01 |
| P03 | Historical data store and timeframe service | A, B | P02 |
| P04 | Integrated analysis adapters | A, B, C | P03 |
| P05 | Historical finding lifecycle and causality | A, B | P04 |
| P06 | External sentiment integration | A, B | P05 |
| P07 | Complete analysis UI connections | A, B | P06 |
| P08 | Explainable daily/weekly bias | A, B | P07 |
| P09 | Integrated-system acceptance | A, B | P08 |
| P10 | Simulator data and replay clock | A, B | P09 |
| P11 | Order and position engine | A, B | P10 |
| P12 | Exit execution and account realism | A, B | P11 |
| P13 | Simulator trading workspace | A, B | P12 |
| P14 | Save/resume and journal | A, B | P13 |
| P15 | Practice, blind challenge and review modes | A, B | P14 |
| P16 | Simulator acceptance and release | A, B | P15 |

There are 33 initial work packets. This is a scope breakdown, not a fixed estimate of 33 sessions; split or consolidate only with recorded reasons. P09 and P16 are major release gates.

## 5. Integration phases

### P01 — Reproducible baseline and source map

**Goal:** make the existing preview a stable starting point before expanding it.

- **P01-A:** Check project instructions, environment, dependency versions, startup and current tests. Establish a local Git checkpoint if the project is not already tracked; do not create a remote repository. Record any baseline failures before changing behavior.
- **P01-B:** Inventory the extracted functions, actual callers and retained licence notices. Document module ownership, duplicate algorithms, upstream changes and existing unsupported features. Create a repeatable verification command.

**Acceptance gate:** a clean setup can build and run; baseline failures are resolved or explicitly block completion; the source map identifies exactly what is reused. Preserve original ZIP snapshots.

**Handoff:** environment/setup commands, baseline test output, source map, checkpoint identifier if Git is available, and next action P02-A.

### P02 — Canonical contracts and instrument rules

**Goal:** agree what each module consumes and returns.

- **P02-A:** Define instrument and candle schemas: symbol, source, timeframe/base interval, UTC open/close times, OHLC, volume and volume type, completed/forming state, pip/tick size, price precision and data-quality flags. Support minute data in the schema now even while the current UI remains hourly.
- **P02-B:** Define snapshot, finding, overlay and sentiment schemas; validate adapter boundaries. Specify occurrence time, confirmation time, expiry/invalidation time, evidence IDs, source version and calculation version. Represent unavailable and insufficient-history states explicitly.

**Acceptance gate:** sample payloads from all four adapters validate against the contracts; invalid timestamps, impossible candles, mismatched symbols and missing evidence fail clearly. Monetary and timestamp units are documented.

**Handoff:** schema examples, compatibility notes, migration list and P03-A.

### P03 — Historical data store and timeframe service

**Goal:** replace repeated full-array transfers with a reusable historical data foundation.

- **P03-A:** Add local dataset storage and metadata, CSV ingestion, range queries, duplicate/gap checks and dataset fingerprints. Introduce an import summary so users can verify symbol, date range, timezone, granularity and provenance. Keep synthetic data explicitly separate.
- **P03-B:** Implement timeframe aggregation, session boundaries and warmup retrieval. Define a documented FX daily/weekly calendar rather than silently assuming every trading day contains 24 UTC bars. Distinguish a missing bar from a scheduled market closure.

**Acceptance gate:** deterministic aggregation on known fixtures; incomplete candles never become completed candles; supported session/DST boundary cases pass; imports retain provenance. Hourly preview still works through the new service.

**Handoff:** dataset IDs, schema/storage version, calendar convention, quality report and P04-A.

### P04 — Integrated analysis adapters

**Goal:** give all selected analysis components one shared interface and one snapshot.

- **P04-A:** Wrap STRUCT.ai swings, labels, supply/demand and BOS/CHoCH. Return normalized outputs without source-app startup. Document which upstream rules can revise.
- **P04-B:** Wrap FX Signal Desk S/R, FVGs, order blocks and candle patterns. Establish canonical EMA/RSI/ATR behavior, including warmup, flat-series and missing-data behavior.
- **P04-C:** Connect Scalper EMA/momentum and selected regime functions to canonical inputs; connect replacement divergence. Remove duplicate indicator calculations from active paths and document intentionally excluded functions.

**Acceptance gate:** all analysis modules consume the same snapshot ID; one API run returns usable outputs; module failure is identified and does not masquerade as neutral market analysis. Validate fixtures for each connected detector and preserve source attribution.

**Handoff:** adapter coverage table, failure behavior, fixture results and P05-A.

### P05 — Historical finding lifecycle and causality

**Goal:** prevent future information from appearing as historically available analysis.

- **P05-A:** Introduce occurrence and confirmation events, deterministic finding IDs and explicit provisional/confirmed/invalidated/expired transitions. Preserve previously confirmed events; represent revisions rather than silently rewriting history.
- **P05-B:** Add prefix-replay checks and correct calculations that use future/full-window information for past signals. Separate retrospectively drawn structure from findings available at the historical clock. Version event/calculation changes.

**Acceptance gate:** future candles cannot change outputs available at an earlier saved clock; pivot findings are unavailable until their confirmation candle closes; lifecycle transitions have timestamps and evidence. Selected historical fixtures pass event-by-event replay.

**Handoff:** event model, repaired detector list, remaining excluded retrospective overlays and P06-A.

### P06 — External sentiment integration

**Goal:** give ForexDashboard a reliable connection to the common analysis clock.

- **P06-A:** Normalize imported order/position-book snapshots, instrument identifiers, source observation time and retrieval time. Validate percentages, bucket geometry, instrument matching and source-specific freshness rules.
- **P06-B:** Implement a provider interface and connect an available approved source if access exists. For historical operation, query only archived observations available at the replay clock. If access or historical coverage is absent, complete and test the adapter boundary and show unavailable; do not fabricate sentiment or ask for unnecessary credentials.

**Acceptance gate:** valid historical snapshots produce reproducible source-labelled scores; future/stale/mismatched data is excluded with a reason. Technical proxies are never labelled measured institutional or retail positioning.

**Handoff:** provider/coverage status, import format, freshness rules, adapter test results and P07-A. A live connector is explicitly deferred if unavailable; this does not make offline integration incomplete.

### P07 — Complete analysis UI connections

**Goal:** make the backend's findings inspectable on the chart.

- **P07-A:** Wire primary backend overlays for S/R, supply/demand, FVGs, order blocks and BOS/CHoCH. Stop competing client-side calculations. Add visibility controls, consistent legends, unavailable states and source labels.
- **P07-B:** Synchronize price and indicator time scales; connect evidence selection to relevant candle ranges and prices. Draw corresponding price/RSI divergence points. Verify imported-file workflows and narrow-screen layout.

**Acceptance gate:** a displayed finding maps to its backend evidence ID; toggles work; selecting it highlights the correct geometry; date/timeframe changes cannot leave stale findings presented as current. Desktop and narrow-screen browser checks pass.

**Handoff:** screenshots, interaction checks, known UX limitations and P08-A.

### P08 — Explainable daily and weekly bias

**Goal:** replace the current EMA-only prototype with explicit, reviewable scenarios.

- **P08-A:** Specify a versioned rule table for weekly and daily structure, zones, reference levels and momentum. Define conflicts, insufficient history, invalidation and the optional role of sentiment. Use bullish/bearish/neutral/mixed/unavailable states without presenting heuristic scores as probabilities.
- **P08-B:** Implement those rules and evidence-driven explanations. Connect them to chart levels and the replay clock. Validate cases where weekly and daily direction disagree and cases with no sentiment source.

**Acceptance gate:** every bias cites its evidence and change/invalidation conditions; the same inputs reproduce the same assessment; missing data never becomes an invented neutral vote; horizon disagreements remain visible.

**Handoff:** rule version, scenario fixtures, UI examples and P09-A.

### P09 — Integrated-system acceptance gate

**Goal:** finish the integrated analysis system before adding simulator behavior.

- **P09-A:** Acquire or import a bounded real EUR/USD historical dataset with documented source and granularity. Verify price/time integrity and inspect representative structure, zone, breakout and divergence examples. Synthetic fixtures remain for exact edge cases.
- **P09-B:** Run the full relevant regression suite, clean build, startup check and browser workflows. Resolve blocking findings. Update source mapping, run instructions and the integration acceptance report; create a release checkpoint/package.

**Acceptance gate:** one real dataset flows through all applicable modules to an explainable chart; causality checks pass; optional external sentiment is either verified or visibly unavailable. No unresolved data-timing or misleading-output blocker remains. All deferred functionality is listed.

**Milestone:** integrated analysis v1. Simulator development may now begin.

## 6. Simulator phases — begin only after P09

### P10 — Simulator data and replay clock

**Goal:** select a historical date and advance the market consistently.

- **P10-A:** Extend the store to a bounded real minute-level dataset with a coverage calendar. Add pair/date selection, warmup history and explicit handling of dates outside coverage or during closed markets. Never imply that selecting 2022 works unless 2022 data is present.
- **P10-B:** Implement a shared replay clock, play/pause, speed control, next-minute/next-candle steps and end-of-data behavior. Build forming 15-minute/hourly candles from revealed minute bars; use only revealed data for analysis. Separate forming-candle visualization from completed-candle signals.

**Acceptance gate:** synchronized views agree at a chosen clock; paused time does not advance; no future candle leaks; empty periods and dataset end behave predictably. Minute playback does not claim to reproduce real tick movement within each minute.

**Handoff:** coverage, clock API, warmup and timing tests, then P11-A.

### P11 — Order and position engine

**Goal:** support deterministic simulated order placement.

- **P11-A:** Define an order lifecycle and event ledger for submit/accept/reject/cancel/fill. Implement buy/sell market orders and positions using instrument units and one quote convention. Orders submitted after a bar is revealed cannot fill retrospectively inside that bar.
- **P11-B:** Add limit/stop orders, trigger rules and cancellation. Define gap behavior and price rounding. Separate execution code from chart/analysis code so identical events replay identically.

**Acceptance gate:** deterministic order fixtures pass; invalid prices/sizes fail; no order fills before submission; cancelled orders cannot fill; replaying the same event sequence reproduces positions.

**Handoff:** order state diagram, fill rules, test ledger and P12-A.

### P12 — Exit execution and account realism

**Goal:** make simulated outcomes and account values internally consistent.

- **P12-A:** Implement SL/TP, manual and partial closes, realized/unrealized P&L, balance and equity. Specify behavior when a bar touches both exits: resolve with finer data if available, otherwise flag the ambiguity and apply an explicit conservative rule. Also define entry/exit ambiguity within one bar.
- **P12-B:** Add spread/commission settings, deterministic slippage assumptions, USD account conversion for the supported pair, margin requirements and insufficient-margin handling. Define financing treatment; either model it or visibly exclude it from results.

**Acceptance gate:** hand-calculated long/short, gap, partial-close and cost fixtures match account results; costs are not double-counted; margin and equity reconcile; ambiguous fills are traceable. No random outcome changes between repeated runs unless a recorded seed is part of the session.

**Handoff:** execution-policy version, accounting examples, limitations and P13-A.

### P13 — Simulator trading workspace

**Goal:** connect replay, orders and analysis into a usable practice environment.

- **P13-A:** Build the simulator workspace with date/coverage controls, clock, playback controls, synchronized timeframe views and the order ticket. Make the simulation label persistent. Add pending-order, position and SL/TP chart lines.
- **P13-B:** Add order/position tables, cancel/close/partial-close controls, account summary and trade history. Validate inputs before submission and display rejected-order reasons. Keep analysis and execution clocks synchronized.

**Acceptance gate:** browser workflow can start a dated session, place/cancel a pending order, open/close a position, hit an exit and inspect resulting balances. Pausing freezes both execution and playback.

**Handoff:** interaction checks, screenshots and P14-A.

### P14 — Save/resume and trading journal

**Goal:** preserve a complete session across application restarts.

- **P14-A:** Persist session configuration, dataset fingerprint, replay clock, execution-policy version and event ledger. Restore orders and positions from persisted state; reject incompatible or missing datasets clearly.
- **P14-B:** Add entry/exit notes, analysis snapshots and trade review. Support exporting the journal and ledger. Keep historical evidence tied to the calculation version used during the session.

**Acceptance gate:** restarting and resuming produces identical clock, orders, balances and findings; no duplicate fills occur; exports reconcile with the session ledger.

**Handoff:** storage schema/version, restore test, export example and P15-A.

### P15 — Practice, blind challenge and review modes

**Goal:** support different training workflows without corrupting results.

- **P15-A:** Add practice-mode rewind with explicit state restoration or a new branch. Preserve the original ledger; do not silently merge trades from different histories. Add blind mode that disables rewind/future reveal and optionally hides the date.
- **P15-B:** Add review mode, prediction-before-analysis prompts and a session summary: trades, net P&L after costs, win/loss counts, drawdown and documented performance metrics. Mark interrupted/open positions and ambiguous fills in reports.

**Acceptance gate:** rewinding restores the whole account state; challenge mode does not expose future UI data; review mode cannot alter original results. Local challenge restrictions are practice controls, not tamper-proof competition enforcement.

**Handoff:** mode rules, branch examples, metric definitions and P16-A.

### P16 — Simulator acceptance and release

**Goal:** deliver a reproducible, usable simulator milestone.

- **P16-A:** Run deterministic end-to-end sessions against real historical input and controlled execution fixtures. Cover closed markets, missing data, partial candles, date jumps, stale analysis, gaps, ambiguous fills, insufficient margin, end-of-data and restore/replay.
- **P16-B:** Verify the complete browser workflow and performance on the supported dataset size. Document limits, costs, data provenance, session calendars and execution assumptions. Package a release with setup instructions and a known example session.

**Acceptance gate:** no future-data leakage or accounting blocker; repeatable results; source and assumptions are visible; save/resume and all supported order types work; the release checklist is complete.

**Milestone:** historical simulator v1. Live market feeds, broader instruments and other extensions are separate follow-up scope.

## 7. Decisions and scope control

### Working defaults

- Local-first application; React frontend and Python/FastAPI backend.
- EUR/USD and a USD-denominated simulated account for initial simulator acceptance.
- Minute data for simulator v1; no invented tick path from OHLC data.
- All persisted timestamps in UTC with explicit display/session timezone rules.
- Server-side replay authority; UI speed never changes execution rules.
- Deterministic calculations and execution; source/calculation versions recorded.

### Decisions to settle during their phase

| Decision | Settle by | Guidance |
|---|---|---|
| Data storage and snapshot API | P03-A | Prefer a simple local design; record why it fits expected dataset size |
| FX session calendar and candle convention | P03-B | Use provider metadata and tests; do not infer from machine timezone |
| Historical data provider and allowed use | P09-A | Verify coverage, granularity, accessibility and permitted use before acquisition |
| Live/archived sentiment source | P06-B | Missing access remains unavailable; no substitute price-derived positioning |
| Bias rule weights/logic | P08-A | Version and test them; no performance claims without evaluation |
| Bid/ask or midpoint execution model | P11-A | Match actual data and declare any synthesized spread |
| Ambiguity, fees, margin, financing | P12 | Document defaults and expose relevant settings |

Paid services, account creation and credential entry are not prerequisites to continuing independent local work. Ask for a decision only when a necessary choice cannot be resolved within the authorized scope.

### Deferred beyond the roadmap

Real-money execution, tick-perfect replay, multi-asset/multi-currency portfolio simulation, options, multiplayer competitions, automated strategy optimization, and profitability claims. These need separate requirements.

## 8. Session handoff template

Copy into `DEVELOPMENT_STATUS.md` after each packet:

```text
Session date:
Phase / packet:
Status: NOT STARTED / IN PROGRESS / BLOCKED / COMPLETE
Objective:
Completed behavior:
Changed files:
Tests/checks run and exact result:
Checks not run and why:
Known defects / limitations:
Decisions made:
Dataset IDs / calculation versions / checkpoint:
Running processes and how to stop or restart them:
Next packet:
Exact first action next session:
```

Do not put credentials, tokens or private account identifiers in this document.

### Reusable prompt for a new session

> Read docs/DEVELOPMENT_ROADMAP.md and docs/DEVELOPMENT_STATUS.md in the combined-analysis project. Verify the actual project state, then complete only the next ready work packet. Preserve earlier work, run the relevant checks, and update DEVELOPMENT_STATUS.md with an exact handoff. Do not begin simulator phases until P09 passes. If the packet is too large, split it explicitly and record the remaining scope.
