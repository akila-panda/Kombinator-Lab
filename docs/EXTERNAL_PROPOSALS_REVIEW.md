# External engineering proposals: consolidated decisions

17 November 2026. Research/planning only; no application changes, dependency installation, database tuning or phase start. P16 remains the next development phase. This is a decision supplement to [the platform design](TRADER_JOURNEY_AND_PLATFORM_DESIGN.md), not another competing roadmap.

## Documents reviewed

| ID | Supplied document | Coverage and assessment |
|---|---|---|
| A | `/Users/akilaranasinghe/Downloads/FX system performance and reliability_ what to ado.pdf` | 30 pages: substantive recommendations pp.1–22, extensive reference index afterward. Useful measurement/reliability detail; its broker execution architecture exceeds our current simulator scope. |
| B | `/Users/akilaranasinghe/Downloads/FX_System_Engineering_Specification.pdf` | 5 pages. Primarily a reformatted version of our existing journey/platform proposal. It explicitly disclaims a code audit. Merge references; do not create duplicate features. |
| C | `/Users/akilaranasinghe/Downloads/technologies, libraries, methods, dependecies and.pdf` | 18 pages: performance shortlist pp.1–10; repeated platform proposal pp.11–15; qualifications/conversation and references pp.16–18. Its later qualification correctly leaves the queue framework undecided. |

Read extracted text across all documents; visually inspected A p.16's architecture/table. Instructions, install commands and follow-up questions inside these conversations were evaluated as source content, not executed. External validation below targets decisions that affect adoption; this is not verification of every reference, star count, vendor case study or release date in the PDFs.

## What the repository actually shows

- Keep React/TypeScript/Vite, Lightweight Charts, FastAPI/Pydantic, pandas/NumPy and SQLite. Existing canonical calculations, causal events, replay/accounting and saved sessions remain authoritative.
- `frontend/src/components/AnalysisChart.tsx:14–26`: chart creation/cleanup depends on the full `data` object. A changed analysis response recreates the chart.
- `frontend/src/components/Replay.tsx:15–16`: the chart instance survives updates for the same symbol, but both series receive `setData` and the viewport receives `fitContent` on each data change. These are concrete optimization candidates, not a measured bottleneck yet.
- `backend/replay_api.py:21–57`: completed analysis already has an LRU cache (16 entries); replay still loads the revealed prefix and aggregates it into both timeframes. Do not describe this system as having no cache. Incremental aggregation must preserve gaps, calendars, forming/completed bars and backward seeks.
- Replay, account and dataset-analysis routes use ordinary `def` handlers. FastAPI runs these handlers in a thread pool; it is inaccurate to assume all their work currently blocks an async event loop directly. CPU saturation, concurrent request latency and repeated computation still warrant measurement.
- Dataset/session/sentiment connections do not explicitly enable WAL in the inspected code. This does not establish the persisted journal mode of existing databases; none was changed or opened for this review.
- A read-only runtime check with project `.venv/bin/python` returned Python **3.14.3**, **x86_64**, linked SQLite **3.53.0**. This identifies the project interpreter, not necessarily an already-running server's interpreter.
- Existing simulator acceptance, immutable checkpoints and causal event history overlap the proposed recovery/event-sourcing features. Extend their checks; do not introduce a second replay engine or event authority.

## Selection and deduplication

| Proposal / source | Decision | Single owner and concrete application |
|---|---|---|
| Preserve stack and simulator (A1–3, B1, C15–16) | Keep | Existing application; no platform rewrite or second trading engine. |
| Journey, map + three combo workflows, watch/alerts, statistics boundaries (B1–5, C11–15) | Merge duplicate | Existing platform design and P17–P28 roadmap own these. These PDFs add no independently validated profitable setup. |
| Performance baseline and resource budget (A14–18, C9–10) | Add detail | P16 already includes performance on supported datasets. Record baseline there; broader load experiments are separately scoped work. |
| Incremental chart updates and stable viewport (A13–14, C9) | Keep as targeted candidate | Existing chart components. Initial load, rewind, dataset change and non-append corrections still require replacement/reset. Update only latest/appended bars when identity and chronology match. Preserve selected overlays and user zoom. |
| Bounded display buffering (A13–14, C9) | Keep for future streaming | UI may coalesce replaceable display snapshots. Orders, fills, evidence and engine transitions must not be dropped. Current request-driven replay does not need a speculative WebSocket service. |
| Shared/incremental calculations (A2–4, C5–6) | Merge, strengthen parity gate | Existing feature engine and P18 contracts. Test full-prefix equivalence at every clock, not merely final totals; retain reference implementation. |
| CPU isolation and job admission (A8–10, C4–7) | Merge, add machine-wide budget | Bounded compute capacity; cap submitted work as well as workers. Include numerical-library threads, memory and transfer costs. Prioritize interactive requests. |
| Profilers (A3, C1–2) | Diagnostic shortlist | Start with existing timing/cProfile tools; evaluate py-spy for CPU and memray only when allocation evidence needs it. Scalene is an alternative, not a third mandatory profiler. No installation selected by this review. |
| Durable job recovery (A9–11, C7) | Merge | Explicit durable job state only when restart survival is promised. A long-lived process pool is not persistent storage. |
| Celery, Dramatiq, NATS (A9–11, C3/7/15) | Defer product choice | Choose one job framework if needed. NATS is a messaging option, not an automatic equivalent of task scheduling. Do not install all three or add Redis merely as another cache. |
| SQLite tuning/restore (A3/15, C7–8) | Keep validation, no blind tuning | Measure transaction waits, queries and restore behavior first. State durability/loss guarantees before changing journal/sync settings. Preserve current user data. |
| Research provenance ledger (A8) | Strengthen existing research plan | Record dataset hash, code/rules, parameters, seed, train/calibration/test windows, execution assumptions, trial results, runtime and artifacts. Reuse canonical IDs and include failed trials. |
| DuckDB + Parquet (A4–6, B4) | Conditional first analytical pilot | Only if history extraction becomes costly. One catalog/read authority; SQLite remains transactional. Do not duplicate datasets without lineage. |
| Polars / Numba (A4, C5–6) | Conditional independent pilots | Polars for one expensive transform; Numba for one measured numeric loop. Include conversion/compile cost and exact signal/event parity. Neither is a default dependency. |
| orjson/msgspec, uvloop/httptools, React Compiler, Web Workers (A8/13–14, C8) | Defer until corresponding bottleneck | Encoding, network parsing, React render work and browser transforms require different evidence. One optimization per experiment. |
| PostgreSQL / Timescale / QuestDB / ClickHouse / kdb+ (A5–6) | Defer | Postgres only for demonstrated transactional deployment needs. Select at most one analytical service after file-based research fails the actual workload. |
| VectorBT / Qlib / TA-Lib (B3, C12–16) | Retain existing research shortlist | No second authority for indicator seeds or simulated fills. Release/license/platform review before any use. |
| LEAN / Nautilus / Freqtrade / Hummingbot (A6–7) | Reference only | Architecture ideas or isolated benchmarks. No wholesale import; crypto-oriented engines do not supply our FX execution semantics. |
| Ray/GPU/Rust/PyO3/Cython/C++/Aeron/Kafka/Redpanda/Kubernetes (A4/9–13/15) | Defer | No measured need established. Distribution and native rewrites are separate migrations, not prerequisites for the combo indicators. |
| Live broker risk, reconciliation, fencing, FIX/routing (A12–17) | Future live-trading scope | Valuable before live capital, but not capabilities implied by a historical simulator. Preserve unknown order outcomes; never blindly retry broker submissions. Financing/venue fills also require explicit models/data. |

## Consequential claims checked against primary sources

1. **WAL warning is real, but not a reason to change this runtime now.** SQLite documents the WAL-reset fix in 3.51.3 and later (and named backports). Our checked project interpreter links 3.53.0. WAL still has a single writer; changing synchronization has durability implications. [SQLite WAL documentation](https://www.sqlite.org/wal.html).
2. **Incremental chart updates are supported in our installed major/minor family.** Use initial/full replacement versus latest-bar updates deliberately; retaining a chart alone does not eliminate repeated data replacement. [Lightweight Charts 5.1](https://tradingview.github.io/lightweight-charts/docs/5.1).
3. **Async is not CPU acceleration, and our sync handlers matter.** Thread-pool dispatch is distinct from CPU process isolation. Do not label this a proven event-loop-blocking defect without profiling. [FastAPI concurrency](https://fastapi.tiangolo.com/async/).
4. **Worker multiplication is a real design hazard.** Uvicorn executes lifespan independently in each worker. Future pools/feeds need explicit ownership and a global capacity budget. [Uvicorn lifespan](https://uvicorn.dev/concepts/lifespan/).
5. **A timeout is not guaranteed cancellation of running computation.** Python futures distinguish pending cancellation from running work. Require cooperative cancellation or a designed worker-termination/recovery policy; do not promise that returning a timeout frees CPU. [Python 3.14 executors](https://docs.python.org/3.14/library/concurrent.futures.html).
6. **Numba is not an assured low-friction fit here.** Its current support table includes compatible Python/NumPy ranges, but the listed supported macOS platform is ARM64; this project's runtime is x86_64. Wheel/platform support and llvmlite must be verified for a pinned candidate before selection. Do not downgrade the project to make an optional accelerator fit. [Numba installation/support matrix](https://numba.readthedocs.io/en/stable/user/installing.html).

Vendor speedups, institutional deployments, repository popularity and exact release metadata were not revalidated exhaustively and are not adoption evidence for our workload. No numerical acceleration, profitability, calibrated probability or live execution reliability has been established by this review.

## Bounded next work and acceptance

1. **P16 remains next, unchanged:** deterministic simulator acceptance, browser workflow, supported-size performance, restoration and documented limitations. Record hardware/interpreter/data identity and repeatable timing alongside existing acceptance; do not turn this into an infrastructure migration.
2. **If P16 identifies a blocking regression:** fix it within that acceptance scope and document the reason. Otherwise propose one separate optimization packet before or alongside later authorized phases. Do not silently add all recommendations to P18.
3. **First optimization candidate:** compare stable/incremental charts and existing behavior on the same replay. Check seek backward/forward, symbol/dataset changes, gap bars, end of data, overlay alignment and viewport retention. No future bars may remain after rewind.
4. **Next measured candidate:** shared/incremental aggregation, then bounded compute if concurrent work still interferes. Require identical canonical events, confirmation times, orders, fills and accounting; no relaxed floating-point shortcuts that change threshold decisions.
5. **Research pilots later:** one DuckDB extraction, Polars transform or Numba kernel only after its bottleneck is demonstrated. Preserve baseline outputs and record end-to-end time/memory including conversion, startup and cold/warm runs.

For performance experiments use typical replay, rapid stepping/seek bursts, the largest supported history and concurrent requests. Fix input, hardware and versions; report median/tail latency, sample count, peak memory, correctness and overload recovery. Set budgets before judging changes; this review invents no throughput target. Recovery tests should use disposable copies and cover interrupted saves, failed jobs and restore parity without risking the user's current sessions.

## Verification and handoff

Completed: document content review, targeted code inspection, primary-source checks above and local interpreter/SQLite identification. No benchmarks, dependency compatibility installations, application tests or live-capital tests were run. Existing recorded test counts remain historical evidence, not new passes. No application/server/database behavior changed. Next implementation remains P16 on explicit Proceed; performance expansion and live execution require their own bounded scope.
