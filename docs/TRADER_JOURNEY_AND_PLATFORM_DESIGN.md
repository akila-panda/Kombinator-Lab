# Trader journey and platform design proposal

17 November 2026. Design/research only. Supplements the indicator roadmap; does not start P16 or authorize additional implementation phases.

## Current technology, verified in the project

| Layer | Current implementation |
|---|---|
| Frontend | React 19.1.0, TypeScript ~5.9.2, Vite ^7.3.0, CSS |
| Charts | Lightweight Charts 5.1.0 plus custom SVG analysis geometry; used in AnalysisChart and replay |
| API | Python, FastAPI 0.135.2, Pydantic 2.14.3, Uvicorn 0.42.0 |
| Calculations | pandas 3.0.2, NumPy 2.4.4, canonical indicator and causal-event code |
| Persistence | SQLite datasets, journals and saved-session state |
| HTTP/test tooling | HTTPX 0.28.1, pytest 9.2.0; TypeScript/build and browser acceptance checks |
| Recorded runtime | README records Python 3.14.3 and Node 22.21.1 as verified; this design pass did not rerun application acceptance |

Sources: requirements.txt, frontend/package.json, README.md and chart imports. No Redis, Celery, DuckDB, Qlib, VectorBT or model-serving layer was installed for this proposal.

## Journey and information hierarchy

The persistent navigation follows decisions, not indicator names: **Discover → Understand → Plan → Practice → Review**. A trader can return to an earlier step without losing the selected setup. Skipping a trade is a valid ending. Do not force a trade to complete the journey.

| Step | Primary visual | Supporting information | Next decision |
|---|---|---|---|
| Discover | Compact opportunity queue with small price previews and state labels | Instrument, timeframe, setup family, age, missing trigger, data freshness | Inspect or watch a candidate |
| Understand | One price chart with selected setup geometry and numbered events | One evidence drawer; optional higher-timeframe context; explicit conflicts | Keep, wait or reject the hypothesis |
| Plan | Entry/stop/target bracket and proportional reward/risk distances | Costs, nearest obstacle, position size, event exposure, invalidation | Save a conditional plan or skip |
| Practice | Chart, current orders/position and only changed setup conditions | Replay clock, fill assumptions and account state | Place/manage a simulated order deliberately |
| Review | Decision-to-outcome timeline, fills and plan-versus-result | Rule adherence, costs, missed/skipped setups and comparable history | Learn and return to discovery |

Keep research/optimization in a separate workspace. It must not occupy the trading chart or change rules silently. A persistent small strip shows replay/live mode, as-of timestamp, source health and scan progress. Never visually confuse historical replay with live market data.

Default desktop composition: compact discovery list, dominant selected chart, single contextual drawer. On narrow displays, use sequential full-width views rather than squeezing three columns. One primary action per step. Essential information cannot depend on hover or color alone. Secondary analysis remains collapsed, but material conflicts and unavailable data remain visible.

Visual choices:

- Price levels, gaps and invalidation belong on the chart, with short labels and a selected-only overlay policy.
- Setup development belongs in a discrete state timeline, not a percentage progress bar: three of four conditions is not a 75% success chance.
- Risk/reward belongs in a price bracket with distances and cost assumptions. A larger green area is not a probability.
- Event timing belongs on a session timeline. Past events in replay cannot expose revised releases or future actual values.
- Currency relative strength can use ranked bars with a fixed lookback and stated basket coverage; it is not money-flow measurement.
- Historical outcomes belong in distributions with sample size and uncertainty, not a lone win-rate gauge. Keep these in Review/Research.
- Data health belongs in a compact labelled status; detailed gap intervals expand on request.
- Use text for exact conditions, failure reasons, source/version and unavailable explanations. Do not turn every sentence into an icon.

The conversation mockup uses fictional values and local navigation only. It illustrates layout, not actual detection, probability or order execution.

## Additional setup discovery and analysis

Prioritize broader coverage of clearly defined situations over more simultaneous indicators. Each addition requires its own rule fixtures and comparison against the existing baseline.

| Candidate capability | Output | Prerequisite / reason |
|---|---|---|
| Approaching-level watch | Distance to a previously confirmed level in pips and ATR; approaching/touched state | Allows preparation before a complete setup. Never treats approach as an entry. |
| Volatility contraction → expansion | Compression band and breakout pending/confirmed state | Fixed rolling window/percentile and completed candles; a distinct consolidation setup to test. |
| Trend pullback continuation | Prior trend, pullback region, structural hold and reclaim trigger | Explicit trend rule; complements the planned reversal and horizontal breakout families. |
| Failed-breakout reclaim | Original boundary break followed by timely return and a separate reversal trigger | Preserve original failed setup; never retrospectively relabel it as a successful opposite trade. |
| Session/prior-period extremes | Session range and previous day/week high/low interactions | Correct calendar, DST, period completeness and causal availability. |
| Relative currency strength | Candidate pairs with contrasting trailing standardized returns | Synchronized multi-pair data, basket coverage and duplicate exposure checks. Normalize pair direction and avoid counting inverse pairs twice. |
| Opportunity lifecycle alerts | New candidate, trigger met, invalidated, expired, material conflict | Deduplication and user-selected watchlists. One event per meaningful transition. |
| Historical analog explorer | Comparable prior setups, including failures, with their later outcome distribution | Retrieve using features known at candidate time; exclude overlapping/self/future matches. Similar appearance does not establish predictive similarity. |

Start with approaching-level watches and lifecycle alerts around the planned combos. Add new setup families individually after functional acceptance. Relative strength and analog research depend on substantially broader data than the current fixture.

Do not add forex volume profile, footprint or order-flow confirmation without appropriate data. Quote/tick activity, exchange futures volume and actual traded spot volume are different sources and must be labelled accordingly.

## Repository shortlist

Approximate star counts displayed on GitHub when checked 17 November 2026; counts change. This was a README/capability/license review, not a complete source audit, installation or benchmark. Popularity is a discovery signal, not evidence of trading accuracy. Pin a release and test Python/native dependencies and license suitability before adoption.

| Repository | Stars | Role and recommendation |
|---|---:|---|
| [TradingView Lightweight Charts](https://github.com/tradingview/lightweight-charts) | 17.9k | Already used. Extend selected overlays, chart interaction and synchronized panes; no replacement needed. Apache-2.0, with attribution requirements described in the README. |
| [TA-Lib Python](https://github.com/TA-Lib/ta-lib-python) | 12.4k | Candidate for selected additional calculation primitives and comparison fixtures. BSD-2-Clause wrapper. Do not replace canonical RSI/ATR without checking seeds, warmup and missing-value behavior. |
| [VectorBT](https://github.com/polakowo/vectorbt) | 9.9k | Research candidate for vectorized signal comparisons and parameter sensitivity. Retain the existing event simulator as execution authority. Its [current license](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md) is Apache 2.0 with Commons Clause, not plain Apache; product integration requires review. Community and PRO capabilities differ. |
| [Freqtrade](https://github.com/freqtrade/freqtrade) | 57.0k | Reference for scanning/pair-list workflows, dry-run and lookahead/recursive analysis. Crypto-oriented, not a ready forex scanner. GPLv3 source: avoid casually copying modules into a differently licensed product. |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | 31.6k | Reference or isolated future benchmark for deterministic event processing and multi-instrument simulation. LGPL-3.0; current README describes a v2 transition. Replacing our simulator would be a separate migration, not an additive scanner feature. |
| [Microsoft Qlib](https://github.com/microsoft/qlib) | 50.3k | Later research candidate for feature/model/evaluation workflows. MIT. Equity-oriented examples/data need adaptation for forex; it cannot supply a proven setup probability out of the box. |

Our scanner should orchestrate our own versioned setup rules. None of these repositories establishes that our three combos will work, and importing another complete platform would create duplicate clocks, data models and execution assumptions.

## Processing architecture

Retain React/FastAPI and the existing event model. Add complexity only after a measured bottleneck or durability requirement justifies it.

Proposed path: **timestamped candles → shared feature calculations → setup state machines → eligibility checks → saved setup events → scanner/chart/journal**.

### Concurrent work without inconsistent results

- Parallelize independent symbol/timeframe scans and research jobs; keep chronological state transitions ordered within each stream. Account mutation and replay-clock commits retain one authoritative writer.
- Prioritize interactive chart/replay work over watchlist scans; put large research jobs in a separate lower-priority queue. Bound worker count, queue length and memory. Expose cancelled/failed jobs rather than silently returning neutral analysis.
- Start with asynchronous I/O and a bounded process pool for CPU work. [Python executors](https://docs.python.org/3/library/concurrent.futures.html) support process/thread task execution. A durable job table must handle restart recovery if work is promised to survive restart; a process pool alone is not a durable queue.
- Add a dedicated worker service and [Celery task queue](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) only if durable retries or multi-process/multi-host scheduling are needed. Broker selection and operational burden are a separate decision.
- Jobs need cancellation, timeouts, bounded retries, idempotent commits and a run ID. UI responses include symbol/timeframe/dataset/as-of/version; reject obsolete responses after selection or clock changes.
- Incremental calculation/checkpoints must match full-prefix results before becoming the default. Cache keys include dataset identity, symbol, timeframe/calendar, as-of time, rule version and parameters. No cache hit may bring future data into replay.

### Remembering state

- Keep market evidence, setup transitions, user decisions and rule/model versions as structured durable records. Model chat memory is not an event store.
- Maintain a compact current-state projection for display plus append-only transitions for audit. Preserve old snapshots and provide deterministic rebuilds.
- SQLite remains appropriate for the current local transactional state; serialize writes and measure lock contention. Consider PostgreSQL only when multi-user/concurrent-write needs justify migration.
- For larger research history, evaluate Parquet partitions with [DuckDB queries](https://duckdb.org/docs/stable/data/parquet/overview). This is an analytical store, not a substitute for the transactional account ledger. Use an explicit read path/catalog to avoid contradictory authoritative candle stores.
- Track queue delay, scan latency, missing inputs, cache correctness, duplicate events, worker failures and UI staleness. Measure end-to-end costs before assuming Rust, distributed compute or a GPU is needed.

### Statistics and probabilities

Keep three distinct outputs:

1. **Readiness:** whether observable rule conditions are satisfied.
2. **Quality checks:** freshness, room, costs, conflicts and data completeness; an explained checklist.
3. **Outcome estimate:** an empirically evaluated conditional probability with a specified outcome, horizon and execution policy.

A probability needs a target such as “target touched before stop within N completed bars after a qualifying entry,” with explicit timeout/unfilled/ambiguous cases. This is not automatically the probability of a net-profitable trade.

Begin with all-candidate counts and outcome distributions. Report sample size, time span, costs and uncertainty. Correlated/overlapping events are not independent observations; use time blocks and preserve overlap exclusions. Later consider shrinkage toward a broader baseline for sparse groups, with stated assumptions; never disguise a prior as new evidence.

For learned estimates, fit transformations on training history only; use chronological evaluation, prevent label-window overlap across boundaries, keep calibration and final evaluation separate, log all trials and compare with simple base rates. [Calibration documentation](https://scikit-learn.org/stable/modules/calibration.html) explains reliability curves and why probability scores require evaluation. Assess reliability diagrams alongside Brier/log-loss and outcome performance; one score alone does not establish calibration.

Display a range and sample context when supported. Otherwise show “insufficient evidence.” Monitor regime-specific deterioration and suspend estimates outside supported conditions. Do not multiply probabilities from correlated price indicators or label a weighted checklist as a win probability.

### AI assistance

An optional assistant may explain stored evidence, retrieve saved cases and help summarize research. Calculations, rule transitions, risk constraints and probability estimates must come from versioned code/data. AI-generated strategies remain research drafts. An LLM must not invent missing candles, silently change rules, or supply an untested numerical chance of success. Multiple AI agents are not required for reliable runtime concurrency.

## Fit with the roadmap

P16 remains next. In P17, settle the journey and information hierarchy alongside rule specifications. P18 should establish stream identity, durable state and stale-result protection. P20/P22/P24/P26 implement the visual journey incrementally, not four disconnected indicator dashboards. P27 supplies decision memory and P28 measures usability, latency and regressions.

Scanner expansion, new setup families, research storage and probability evaluation need separately bounded phases after their dependencies are ready. This document proposes that direction without silently enlarging the currently authorized implementation scope.

Usability acceptance should ask whether a trader can identify: the selected scenario, known facts, missing trigger, invalidation, data age and next action. Include keyboard navigation, narrow screens, conflicting evidence and the decision to skip. Functional acceptance and financial-performance evidence remain separate gates.

## External proposal review

[External proposals review](EXTERNAL_PROPOSALS_REVIEW.md) consolidates the three supplied PDFs against the code. It adds targeted performance/recovery acceptance details and adoption gates; existing feature ownership and phase boundaries remain unchanged.
