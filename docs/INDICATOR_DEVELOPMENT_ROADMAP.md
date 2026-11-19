# Combined indicator development roadmap

Main development entry point: [Updated development document](DEVELOPMENT_PLAN.md), including selected engineering improvements and their separate acceptance gates.

Version 1.0 · 17 November 2026 · Planning document; implementation not started.

## Order and authority

**Complete P16 simulator acceptance first. Then begin P17–P28 below.** P01–P16 remain governed by [the original roadmap](DEVELOPMENT_ROADMAP.md). This document extends that sequence; it does not replace earlier acceptance requirements. [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) is the single current progress/handoff record.

P16 verifies the existing replay, accounting, restore and training behavior before new analysis changes are introduced. A known baseline makes later regressions attributable and provides a usable simulator release even while indicator development is incomplete. Do not postpone accounting, future-data or restore blockers until after adding indicators.

This planning request does not start P16. On the next explicit development Proceed, start P16-A. Retain its existing A/B packet split and stop at phase completion. The new phases are deliberately smaller: generally one backend feature or one UI feature per phase. Do not interpret a Proceed as permission to finish the entire roadmap.

Source/design reference: [INDICATOR_COMBINATION_RESEARCH.md](INDICATOR_COMBINATION_RESEARCH.md), with [source inventory](indicator-source-audit.json). The research covered all supplied source items but only a targeted selection of blog detail pages. Do not mark the entire blog archive reviewed. P17 records remaining research requirements and their disposition before locking definitions.

## Intended result

One shared **Market Structure & Key Levels** map plus three selectable workflows:

1. **Sweep → Shift → Retracement:** failed excursion, opposing structure break, related FVG, later return.
2. **Breakout & Retest:** a known boundary, qualified departure and later role-flip interaction.
3. **Momentum at Structure:** fixed-RSI divergence at a known level, followed by a separate price trigger.

Each workflow explains observed conditions, missing conditions, timestamps, expiry and invalidation. No combined probability score, automatic broker execution, universal buy/sell voting system or performance promise is included.

## Session and completion rules

- One phase per authorization; finish its checks and handoff, then wait for the user to proceed.
- Reserve approximately the last quarter of each session for verification and documentation. Session size is variable; no phase duration is guaranteed.
- If a phase no longer fits, split it into named A/B packets at a coherent boundary. Record exactly what remains. The next Proceed resumes the unfinished phase; it does not skip its gate.
- At session start, read the status, this phase's specification and relevant files. Verify actual state before editing. Do not repeat the entire research audit.
- Do not add deferred features because they happen to share files. Necessary fixes belong to the active phase; unrelated work is recorded separately.
- Every completed phase has `docs/Pxx_ACCEPTANCE.md`: delivered behavior, changed files, commands/check results, limitations, example evidence and next action. Backend checks focus on meaningful causal/state fixtures; UI phases include browser verification and production build.
- Preserve user datasets, saved sessions and prior calculation versions. Never migrate old sessions silently. Keep the preview server available; if a required restart occurs, restore service and verify it.
- No passing phase is defined solely by a test count. A failing acceptance condition remains open even when most tests pass.

## Phase index

All P17–P28 phases are **NOT STARTED**. Dependencies follow the sequence below.

| Phase | Bounded deliverable | Dependency |
|---|---|---|
| P16 | Existing simulator acceptance and baseline release; existing A/B packets | P15 complete |
| P17 | Source decisions and exact combo specifications | P16 |
| P18 | Versioned setup contracts and causal orchestration foundation | P17 |
| P19 | Causal key-level map backend | P18 |
| P20 | Key-level map UI and evidence inspection | P19 |
| P21 | Sweep reversal backend | P20 |
| P22 | Sweep reversal UI/replay workflow | P21 |
| P23 | Horizontal breakout/retest backend | P22 |
| P24 | Breakout/retest UI/replay workflow | P23 |
| P25 | Fixed-RSI divergence confirmation backend | P24 |
| P26 | Momentum-at-structure UI | P25 |
| P27 | Setup-linked journal and training review | P26 |
| P28 | Integrated acceptance and combined-indicator release | P27 |

The core expansion is twelve small phases after P16, not a commitment to twelve fixed-length sessions. Backend/UI splits allow each session to end with testable work rather than a partially implemented feature spanning all layers.

## P16 — Finish the simulator baseline

Use the original P16 scope unchanged:

- **A:** deterministic end-to-end real-history and controlled execution scenarios: closed markets, missing data, partial candles, date jumps, stale analysis, gaps, ambiguous fills, insufficient margin, end-of-data, restore/replay.
- **B:** complete browser workflow, supported-size performance, setup instructions, provenance/calendar/cost limitations, packaged release and example session.
- **Gate:** repeatable results; no future-data, accounting or restore blocker; supported order types and save/resume work; release checklist complete. Fix acceptance defects before declaring the baseline complete.
- **Handoff:** acceptance evidence, baseline revision/checkpoint, supported dataset bounds and exact next action P17. Recheck actual server availability rather than trusting an old PID.

No new combo indicators are part of P16. Its release is simulator v1; P28 later accepts the indicator extension against this baseline.

## P17 — Source decisions and exact rules

**Deliver:** `docs/COMBO_SPECIFICATIONS.md` and updated source decision inventory. No detector implementation.

- For every source, record reuse/concept-only/defer/reject, original notice, exact version/hash and intended behavior changes. Resolve license applicability before incorporating derived source. Do not assume a language translation changes that requirement.
- Obtain/review missing source where exact behavior is required. Four excerpts are incomplete: Sweep Reversal/FVG, Triangle, Trendline Liquidity and Divergence Variants. Missing optional triangle/trendline code must not block independently specified core workflows; explicitly defer it. Missing core source can be replaced only by a clearly documented original specification, without claiming source parity or using relabeling to bypass rights.
- Record the existing targeted blog coverage and the user's earlier request for broader reading. Complete any outstanding required coverage or obtain an explicit scope decision; do not silently declare that research requirement complete.
- Define one first-release rule per combo: pivot method, price comparisons/ties, ATR sample/seed, zone tolerance, level freshness, event ordering, gap association, invalidation, expiry and conflict handling. Specify how multiple eligible gaps/levels are selected before observing outcomes.
- Define C1 zone geometry and actual completed-timeframe selection. Default to the current timeframe and at most one supported higher timeframe; daily/weekly context is optional and unavailable when history is insufficient.
- Freeze separate meanings for confirmed primitive geometry, confirmed setup and eligible trade condition. Specify first-release regular divergence only, price-pivot anchoring and fixed RSI14. No parameter optimizer.
- Write worked bullish/bearish examples and failure timelines for each setup. Parameters are test inputs, not claimed optimal settings.

**Gate:** every core state transition and data requirement is unambiguous; source/permission decisions are recorded; remaining optional-source gaps are explicitly deferred. Any unresolved core permission or rule decision blocks the dependent implementation, not unrelated baseline work.

**Boundary:** no full-source port, no additional indicator suite, no profitability study.

## P18 — Setup contracts and causal foundation

**Deliver:** typed, versioned setup/event schema, deterministic identity and orchestration over canonical primitive events. Establish these interfaces with minimal fixtures, not speculative abstractions.

- Include setup kind/direction/state, origin and availability times, evidence IDs, frozen reference geometry, rule/parameter version, expiry/invalidation and data availability reasons.
- Consume complete causal event history, not the truncated API display summary. Never use retrospective snapshot arrays as historical setup facts.
- Reuse the current replay clock and canonical indicators. Define append-only transitions, idempotency, serialization and old-version handling. Persist setup transitions using the existing storage conventions; trading/journal links wait until P27.
- Keep unavailable inputs separate from a valid calculation finding no setup. Old sessions retain review/export semantics under existing version rules.

**Gate:** prefix/future-mutation tests, stable IDs, repeated runs, serialization, restart and incompatible-version behavior pass. No change to fill or accounting policy. Existing relevant simulator regression checks pass.

**Boundary:** no production combo detector or chart redesign.

## P19 — Market map backend

**Deliver:** causal levels/zones derived from the P17-selected confirmed anchors, with interaction events and completed-timeframe provenance.

- Reuse existing structure where definitions match. Add only missing level lifecycle behavior: creation, independent visit/test, break, explicit role-flip reference, expiry.
- Group overlapping zones for presentation without destroying individual geometries, evidence or invalidation rules. Rank nearby levels using documented relevance rules, not a claimed success probability.
- Return current/mixed/unavailable context, nearest obstacles, distances and timestamps. Missing volume is unavailable; no volume-based quality score.

**Gate:** exact zone geometry, overlap, distinct-visit counting, role changes, boundary ties and expiry fixtures; true higher-timeframe availability; insufficient history and gaps handled; earlier outputs unchanged by future bars.

**Boundary:** no sweep/trade triggers, all four upstream S/R methods, or regime classifier.

## P20 — Market map UI

**Deliver:** one readable map in the existing analysis/chart UI.

- Show nearby support/resistance, structure context, timeframe and latest interaction. Selecting a level opens evidence, geometry and occurrence/confirmation times.
- Limit default visible overlays and disclose additional hidden levels. Distinguish retrospective legacy overlays from the causal map; do not show both as equivalent confirmations.
- Display unavailable/warmup/gap states and prevent stale symbol/timeframe/replay responses from appearing as current.

**Gate:** browser checks for selection, replay stepping, timeframe/symbol changes, incomplete data and narrow layout; production build; no overlapping unreadable labels in the reference examples.

**Boundary:** no full application redesign or setup cards yet.

## P21 — Sweep reversal backend

**Deliver:** C2 state machine from a pre-existing level sweep through shift, qualifying FVG and later retracement/confirmation.

- Freeze references when the rules specify. Require temporal association of sweep, displacement, structure break and gap; do not select an unrelated nearby FVG.
- Preserve failures and expiry. Treat same-bar ordering conservatively; do not infer a wick path from OHLC. Prevent new signals from backdating eligibility.
- Reuse canonical primitives where identical; version differences from the original Pine excerpt and current FVG thresholds.

**Gate:** bullish/bearish success, sweep without shift, shift without gap, early gap invalidation, unrelated gap, late retest, duplicate event, missing data and expiry fixtures; prefix invariance and restart parity.

**Boundary:** no macro filter, divergence requirement, automated paper order or alternative entry mode.

## P22 — Sweep reversal UI

**Deliver:** selectable C2 setup card and minimal linked chart geometry.

- Show completed/missing steps, swept/broken prices, FVG bounds, confirmation times, expiry, invalidation and next obstacle.
- Replay displays only information known at that clock. Selecting a failed/expired example explains the failure rather than removing it.

**Gate:** browser walkthrough of pending, confirmed, failed and expired sequences; rewind/replay does not reveal future state; existing order controls and pause behavior remain usable; build passes.

**Boundary:** no simulated entry at the historical sweep low; no extra scoring system.

## P23 — Horizontal breakout/retest backend

**Deliver:** C3 using horizontal boundaries only.

- Pre-existing boundary → breakout pending FVG → qualified breakout → waiting for role-flip retest → held/failed/expired.
- Respect the third-candle FVG confirmation delay and P17's open/close crossing rule. Preserve fixed geometry and one opportunity per boundary event.
- Distinguish a breakout failure from a new reversal setup. Do not silently switch entry area from broken level to FVG based on later outcomes.

**Gate:** long/short, weak body, no FVG, gap-open behavior, stale level, retest held/failed/missing, timeout and duplicate cases; causal and persistence checks.

**Boundary:** no triangles, fitted trendlines or projected trendline alternative.

## P24 — Breakout/retest UI

**Deliver:** C3 card, breakout/gap/retest timeline and selected boundary overlay.

- Reuse C2 evidence presentation conventions. Distinguish first breakout time from fully qualified time and later retest time.
- Clearly show conflicting setups; shared evidence links identify overlap rather than imply independent confirmations.

**Gate:** browser success/failure/expiry walkthroughs and setup switching; no duplicate geometry storm, stale card or future state; build passes.

**Boundary:** no new charting library or mandatory agreement with reversal indicators.

## P25 — Divergence confirmation backend

**Deliver:** C4 regular RSI14 divergence at a prior key zone, then a separate price confirmation.

- Reuse existing confirmed price pivots and canonical full-prefix RSI. Freeze the specified intervening swing trigger and zone reference.
- Separate geometry confirmation from subsequent setup confirmation; reject a trigger that was already passed before the candidate became eligible under the chosen rules.
- Preserve expiry/adverse-extreme invalidation and deduplicate related pivot chains.

**Gate:** bullish/bearish, absent zone, persistent trend, unavailable RSI, previously passed trigger, invalidation/timeout and duplicate fixtures; chronological availability and persistence checks.

**Boundary:** no hidden/exaggerated divergence, oscillator voting, dynamic RSI selection or optimization.

## P26 — Momentum-at-structure UI

**Deliver:** C4 view with price/RSI endpoints, known-at times, prior zone, trigger and pending/confirmed/failed status.

- Use the existing RSI pane and shared evidence controls. Distinguish a pattern warning from a later price trigger in labels.
- Default to one selected scenario with optional supporting context. No probability or “three confirmations = stronger” badge.

**Gate:** synchronized price/RSI selection, replay visibility, warmup/failed cases, narrow layout and build; a user can identify the missing trigger and invalidation from the card.

**Boundary:** no continuation-mode UI until its independent rules exist.

## P27 — Setup-linked journal and training

**Deliver:** optional manual association of a practice trade/prediction with a setup and its frozen evidence/version.

- Store selected setup IDs and the evidence actually available at the decision clock. A single trade can have several explanations without being counted several times.
- Preserve blind prediction-before-analysis behavior and read-only historical review. Do not leak future setup outcomes into blind mode.
- Exports and restored sessions retain setup links, rule versions and unavailable/missing evidence explanations. Prior records remain reviewable under existing compatibility policy.

**Gate:** save/restart/export parity, unchanged parent practice session, no duplicate fills/trades, no retroactive evidence, blind-mode and review-mode integration checks.

**Boundary:** no automatic trading, optimizer rankings or redesign of account metrics.

## P28 — Integrated acceptance and release

**Deliver:** documented combined-indicator release, setup guide, example replay cases and explicit limits.

- Run the full applicable backend suite, dependency/build checks, end-to-end simulator regression and browser flow across all four views. Compare accounting with the P16 baseline under identical policies.
- Include failed/expired examples, restart/restore, missing history, unavailable volume, stale responses, symbol/timeframe changes and blind review behavior.
- Measure latency and event growth on declared supported dataset sizes; record actual results and limits. Fix blocking regressions; no unmeasured claim of scalability.
- Package reproducible source/configuration and acceptance artifacts without private datasets/session data. Preserve provenance and license notices for anything incorporated.

**Gate:** causal timing and persistence checks pass, old-session policy works, no accounting regression, evidence matches replay clock, chart is readable and known limitations are documented. Performance claims require measurements; trading-edge claims remain outside this gate.

**Boundary:** the current short EUR/USD minute fixture supports functional acceptance, not broad statistical validation. Do not delay a functionally correct release while inventing a profitable backtest or claiming an edge from a small sample.

## Deferred extensions — require separate authorization

These are not hidden requirements of P17–P28. Define their own small phases only when selected.

| Extension | Prerequisite and reason to keep separate |
|---|---|
| Date-aware ICT macro schedule | Reconcile source window labels, named timezone/DST policy and minute completeness; start with time context, then separately test post-window classification. |
| Intrabar inspection | Actual lower-timeframe coverage; use minute detail unless seconds data exist. No reconstructed tick path. |
| Triangle breakout subtype | Complete source review and frozen geometry/touch/apex rules; separate detector and UI phases. |
| Trendline liquidity subtype | Complete fitting and state-transition rules; compare with the horizontal baseline. Projected Trendlines with Breaks is an alternative, not mandatory confirmation. |
| Hidden/exaggerated divergence | Separate trend definition/equality tolerance and confirmation rules; separate from reversal signals. |
| Parameter research and combination evaluation | Broader licensed data, explicit execution/exit rules, chronological holdouts, trial ledger and identical costs. Begin with fixed baseline versus one added condition. Do not use evaluation history to tune live settings. |

## Handoff template

Copy a compact checkpoint into DEVELOPMENT_STATUS.md at every phase/session boundary:

```text
Active roadmap/version:
Phase / packet:
Status: not started / in progress / blocked / complete
Objective and fixed rules:
Completed behavior and changed files:
Checks actually run and results:
Acceptance conditions still open:
Source/data/permission decisions or blockers:
Calculation/schema version and saved-session compatibility:
Server availability (verified, or not checked):
Exact first action on next Proceed:
Stop boundary: finish this phase, then wait.
```

Continuation prompt:

> Read docs/DEVELOPMENT_STATUS.md and the active phase in docs/DEVELOPMENT_ROADMAP.md (through P16) or docs/INDICATOR_DEVELOPMENT_ROADMAP.md (P17 onward). Verify actual state, then complete only the authorized phase or its next unfinished packet. Preserve user data and the preview server, run relevant checks, record acceptance evidence and an exact handoff, and wait before the next phase. Do not skip P16 or promote deferred indicator features into current scope.
