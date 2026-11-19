# FX system — development document

Version 3.1 · Updated 18 November 2026 · Planning approved for review; no phase started by this document update.

## Current state and document authority

**P01–P15 complete. P16 final simulator acceptance is in progress.** P17 onward has not started. Historical test results are recorded in the status file; this document does not claim a new acceptance run.

This is the main entry point for development. It consolidates the indicator roadmap, trader journey and selected external engineering recommendations without duplicating their implementations.

- [Development status](DEVELOPMENT_STATUS.md): authoritative current phase, results, blockers and next action.
- [Original roadmap](DEVELOPMENT_ROADMAP.md): detailed P01–P16 requirements, preserved unchanged.
- [Indicator roadmap](INDICATOR_DEVELOPMENT_ROADMAP.md): detailed P17–P28 specifications and gates.
- [Trader journey and platform design](TRADER_JOURNEY_AND_PLATFORM_DESIGN.md): UI composition, discovery and architecture decisions.
- [External proposals review](EXTERNAL_PROPOSALS_REVIEW.md): keep/merge/defer decisions, source evidence and technical qualifications.
- [Product advancement roadmap](PRODUCT_ADVANCEMENT_ROADMAP.md): P29–P46 for the new evidence, realism, decision and training capabilities.
- [Post-completion research](POST_COMPLETION_PRODUCT_RESEARCH.md): sources and reasoning for those additions.

Where scope conflicts, preserve the existing P01–P28 acceptance requirements. Later proposals below cannot silently expand an active phase. Record any necessary scope change in the status before implementation.

## Product and stack

Retain React 19, TypeScript, Vite and Lightweight Charts; Python/FastAPI/Pydantic/Uvicorn; pandas/NumPy; SQLite; HTTPX and pytest. Canonical calculations, causal events, replay clock, account engine and saved sessions remain the single authorities for their responsibilities.

The product is an analysis and historical practice system. Real-money broker execution, FIX connectivity, smart routing and high-availability execution are outside this roadmap.

The trader journey is **Discover → Understand → Plan → Practice → Review**:

| Step | Main presentation | Decision |
|---|---|---|
| Discover | Compact opportunities/watch list with lifecycle and freshness | Inspect or watch |
| Understand | Dominant chart, selected geometry, numbered events and one evidence drawer | Accept hypothesis, wait or reject |
| Plan | Entry/stop/target bracket, costs, obstacle distance and risk | Save a conditional plan or skip |
| Practice | Replay chart, orders/positions and changed conditions | Simulate and manage deliberately |
| Review | Decision/outcome timeline and frozen evidence | Learn from results |

Build this journey incrementally in the relevant UI phases. Do not create a separate dashboard per indicator. Keep material conflicts visible, details expandable and narrow-screen navigation sequential. Readiness is a rule state, not a probability of success.

## Phase and session rules

1. One phase per explicit Proceed. Finish verification and handoff, then wait.
2. Start by reading status and the active phase, not by repeating the whole research audit.
3. Split oversized phases into named packets; reserve roughly the final quarter of the session for verification and handoff. Session duration cannot be guaranteed.
4. Each phase produces an acceptance record with changed files, checks actually run, evidence, limitations and next action. Incomplete gates remain open.
5. Preserve user data, saved-session compatibility and the preview at `http://127.0.0.1:8766/`. If a necessary restart occurs, restore and verify service.
6. No future-data leakage, silent event loss, altered accounting or undocumented numerical drift is acceptable as a performance optimization.

## Beta delivery alongside development

[Beta release plan](BETA_RELEASE_PLAN.md): deliver a private local practice beta after P16 and the distribution/onboarding gates; do not wait for P46. Subsequent complete capabilities ship after P20, P22, P24, P26 and P28 with regression checks. Preserve a pinned beta release/data directory while development continues. Collect structured trader feedback before each phase; prioritize correctness and workflow blockers without silently expanding scope.

## Core delivery sequence

Detailed gates remain in the linked phase roadmaps.

| Phase | Deliverable | Completion evidence |
|---|---|---|
| P16 | Final simulator acceptance and baseline release | Deterministic sessions, browser workflow, restore, accounting/causality checks and supported-size performance |
| P17 | Complete source/license decisions and freeze combo rules and information hierarchy | Exact detection/confirmation/expiry definitions; unresolved inputs explicitly deferred |
| P18 | Shared setup contracts and causal orchestration | Stable identities, versioned state, as-of boundaries and stale-result protection |
| P19 | Market Structure & Key Levels backend | Causal level lifecycle fixtures |
| P20 | Shared key-level chart and evidence UI | Readable selected overlays, timestamps and missing/conflicting evidence |
| P21 | Sweep → Shift → Retracement backend | Ordered sweep, structure shift, qualifying FVG and later retracement |
| P22 | Sweep workflow UI | Replay-safe numbered evidence and trigger/invalidation visibility |
| P23 | Breakout & Retest backend | Prior boundary, qualified departure and later role-flip interaction |
| P24 | Breakout workflow UI | Clear pending, confirmed, invalidated and expired states |
| P25 | Momentum at Structure backend | Fixed-RSI divergence at prior structure, separate price confirmation |
| P26 | Momentum workflow UI | Synchronized chart/RSI evidence without misleading confidence scores |
| P27 | Setup-linked journal/training | Frozen decision evidence, save/restore/export parity and blind-mode protection |
| P28 | Combined release acceptance | Regression versus P16, usability, latency, event growth, limits and reproducible package |

P16 should record dataset identity/size, runtime/hardware, latency samples and supported limits as part of its existing performance scope. Do not add a worker platform or database migration to P16. Fix actual acceptance defects; schedule nonblocking optimizations separately.

## Selected engineering improvements

These supplement existing mechanisms rather than introduce parallel ones.

| Improvement | Current evidence | Planned treatment |
|---|---|---|
| Performance visibility | No benchmark was run in the PDF review | Establish P16 baseline; expand measurement in E01 |
| Incremental charts and viewport retention | Replay calls `setData` and `fitContent` on updates; analysis chart rebuilds when data changes | E02; full replacement still required for rewind/history changes |
| Shared/incremental calculations | Replay aggregates the revealed prefix; completed analysis already has an LRU cache | E03; retain full-prefix reference and exact causal parity |
| Bounded background work | Scanner/research expansion will introduce competing work | E04 only when measurements or new workload require it |
| Recovery and durability | Saved sessions/event history already exist | P16 restore baseline; E05 tests remaining failure cases |
| Experiment provenance | Research evaluation is planned, not implemented | E06; one versioned trial ledger |

### Engineering packets — proposed, independently authorized

Default order is P16 → P17–P28, then the selected E packets. If P16 exposes a meaningful performance limit, explicitly schedule the relevant E packet after P16 before resuming P17. Record the ordering decision; do not auto-run these packets or make all of them prerequisites for indicators.

| Packet | Bounded scope | Gate and stop condition |
|---|---|---|
| E01 — Measurements | Reproducible normal replay, seek bursts, largest supported history and concurrent-request fixtures; lightweight timing/memory evidence | Record fixed inputs/hardware/versions, sample counts, cold/warm behavior and bottleneck attribution. Define workload budgets before selecting an optimization. No speedup claim yet. |
| E02 — Chart updates | Preserve chart instances and viewport; append/update only matching chronological series | Browser verification for rewind, seek, dataset/symbol changes, forming bars, gaps, overlays and narrow layout; compare frame/update cost with E01. No future bars retained. |
| E03 — Calculation reuse | Optimize one measured aggregation/feature path with shared results or checkpoints | Compare full-prefix results at every relevant clock: indicator values, event identities/times, gaps and downstream fills/accounting. Record memory and runtime. Split further paths into later packets. |
| E04 — Compute admission | One bounded execution mechanism with job identity, status, queue limits and interactive priority | Saturation, stale-result rejection, failure and cancellation checks. Running-task timeout must not be described as guaranteed cancellation. Add durable recovery only if promised; split it into E04-B if needed. |
| E05 — Recovery hardening | Disposable-copy interrupted-save/job and backup/restore scenarios; document loss/recovery guarantees | No duplicate accepted transitions; restored evidence/account parity. Fix observed gaps. Do not weaken SQLite sync settings to improve benchmarks. |
| E06 — Research ledger | Record data/code/rule versions, parameters, seeds, windows, execution assumptions, successful and failed trials | Reproduce a saved experiment and distinguish training/calibration/evaluation history. This does not produce validated probabilities. |

Each E packet depends on a completed baseline; E02–E04 additionally depend on E01 evidence. E05 reuses P16 coverage rather than repeating already-passed cases without cause. E06 requires a defined research workflow and dataset. Cancel or defer an optimization that does not improve its target metric without regressions.

## Discovery expansion — separate from infrastructure

These remain candidates, not hidden P17–P28 requirements. Select one at a time after the combo release.

| Candidate | Prerequisites and acceptance |
|---|---|
| Approaching-level watch | Existing confirmed level map; causal distance in pips/ATR; an approach never becomes an entry automatically |
| Lifecycle alerts | Existing setup transitions; user-selected watchlists, deduplication and explicit invalidation/expiry |
| Compression/expansion, pullback continuation, failed-breakout reclaim | Independent frozen rules and detector/UI packets for each family; preserve original failed setups |
| Session/prior-period extremes | Calendar/DST and period completeness fixtures |
| Relative currency strength/exposure | Synchronized multi-pair coverage, direction normalization and no inverse-pair double counting |
| Historical analogs/outcome estimates | Broader appropriate data; no future/self/overlapping matches; all candidates and failures; chronological evaluation and calibration |

Outcome estimates must define horizon, entry, stop/target, unfilled, timeout and ambiguous cases. Show sample size, costs and uncertainty or insufficient evidence. Checklist scores and correlated indicator agreement are not win probabilities.

## Dependency decisions

**No new runtime dependency is mandatory now.**

- Start measurement with existing tools. Evaluate py-spy for CPU or memray for allocation investigation only when useful.
- Pilot DuckDB/Parquet only when historical extraction warrants it; retain one authoritative candle catalog and SQLite transactions.
- Pilot Polars for one expensive transform or Numba for one numeric loop only after attribution. Include conversion/compile costs and platform checks. Numba's current documented macOS support needs special scrutiny on this project's x86_64 runtime.
- A process pool is not a durable queue. Leave Celery versus Dramatiq undecided until job recovery/deployment needs are clear. Do not add both. NATS is a separate messaging decision.
- Keep Redis, Postgres, analytical database servers, Ray, GPU compute, native rewrites, Kafka/Aeron and Kubernetes deferred until explicit requirements and measurements justify their operational cost.
- Existing TA-Lib/VectorBT/Qlib and engine research shortlist stays outside authoritative replay unless a separately approved integration passes compatibility, semantics and license checks.

The project interpreter checked during review was Python 3.14.3 / x86_64 / SQLite 3.53.0. The cited WAL-reset fix is already included in that SQLite version; this is not a reason for an emergency database migration. A running server's interpreter must be verified separately when relevant.

## Product advancement — P29–P46

The newly selected capabilities are now planned in [PRODUCT_ADVANCEMENT_ROADMAP.md](PRODUCT_ADVANCEMENT_ROADMAP.md). All are **NOT STARTED**. Complete P28 before starting P29. Relevant E packets remain conditional prerequisites, not automatic requirements to install infrastructure.

| Phases | Added capability | Existing module extended |
|---|---|---|
| P29–P30 | Dataset capability contracts and cross-feed sensitivity | Data provenance and quality |
| P31–P32 | Versioned execution assumptions and stress comparisons | Existing simulator/accounting |
| P33–P34 | Setup evidence dossiers and promotion/restriction policy | Research ledger and setup drawer |
| P35–P36 | Prospective observation without real orders | Scanner, event store and review |
| P37–P38 | Portfolio plan/scenario comparisons | Exposure and risk planning |
| P39–P40 | Personal versioned playbooks | Existing plans, rules and journal |
| P41–P42 | Targeted practice and unseen-case assessment | Replay and training |
| P43–P44 | Decision attribution and controlled alternatives | Journal and practice branches |
| P45 | Representative-user evaluation and simplification | Entire trader journey |
| P46 | Integrated acceptance and evidence-bounded release | Existing acceptance and packaging |

Usability checks begin in every UI phase; P45 is the formal evaluation, not the first user feedback. Each feature must justify its screen space. A technically complete feature can be hidden, simplified or removed if it worsens decisions.

The review ratings are provisional design opinions, not acceptance scores. Release requires correctness, declared simulation limits, honest statistical evidence, usable workflows and operational reliability. Do not average these into a score that conceals a failed gate. Setup profitability and probability calibration require separate evidence; unsupported estimates must remain unavailable.

Macro/positioning expansion, read-only real-trade imports, coach collaboration and AI assistance remain conditional tracks described in the advancement roadmap. Shared/cloud distribution requires its own security/access-control scope. Live broker execution remains excluded.

## Checkpoint and next action

At each stop update DEVELOPMENT_STATUS.md with phase/packet, completed behavior, changed files, actual verification, unresolved gate, version compatibility, server state and exact next action.

**Next action: finish P16-B release/onboarding gates.** P16-A verification is recorded in P16_ACCEPTANCE.md. No later phase starts until P16 completion and a new Proceed.
