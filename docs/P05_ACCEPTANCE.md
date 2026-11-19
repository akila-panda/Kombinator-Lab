# P05 acceptance — historical finding lifecycle and causality

Completed 11 November 2026. P05-A and P05-B complete; **stop before P06**.

## Delivered

- Integration-owned `p05-causal-v1` chronological event engine, separate from legacy retrospective overlays. Strict pivot confirmation, causal structure references/breaks, FVG/OB availability and full-prefix RSI divergence.
- Deterministic IDs, immutable occurrence/confirmation/invalidation/expiration/revision records, closed OHLC evidence, source/timeframe/calendar/version context and clock-specific state projection.
- Append-only SQLite journal with clock fingerprints, idempotent writes, conflict rejection, pagination, earlier-clock metadata stability and non-destructive v1→v2 database migration.
- Contract 1.2.0 explicitly marks snapshot findings retrospective; no compatibility annotation masquerades as confirmed historical history. Published event schema and explicit journal-integrity API errors.
- UI distinguishes retrospective chart/evidence from confirmed historical records and displays origin separately from confirmation time.
- Event model, repaired rules, retention policy and excluded retrospective outputs documented in HISTORICAL_EVENTS.md. No new dependencies or provider downloads.

## Verification

Final `./verify.sh`: **130 tests passed**, dependency consistency passed, TypeScript/Vite production build passed, real HTTP startup/assets/legacy analysis/CSV import/metadata/range/dataset-ID analysis/event-journal checks passed. The existing Starlette TestClient httpx deprecation remains the only test warning.

13 lifecycle cases add event-by-event prefix equivalence, third-right-close confirmation, provisional rejection, causal breaks unaffected by later volatility, expiration evidence, FVG/OB confirmation/invalidation, full-prefix RSI divergence, calendar close times, persistence/reopen/idempotence, unchanged earlier-clock replies after later analysis, conflict rejection/errors, schema evidence validation, v1 migration and API separation. All earlier adapter, contract, dataset/calendar and prefix tests remain active.

Browser QA on the 10,000-hour synthetic EUR/USD dataset: chart rendered, retrospective labels visible, historical panel rendered with distinct origin/confirmation times, and replay from 10,000 to 9,999 reached 2025-08-05 15:00 UTC. No errors in the final browser console check. A final UI guard clears prior results immediately when pair/timeframe/cutoff changes, preventing stale later-clock history during recalculation; the production build passed again after this guard. Screenshot: outer outputs/p05-history-preview.png. Browser file upload was not retried; P03's extension permission limitation remains unrelated to this phase.

## Limits and handoff

The journal is a causal reconstruction from supplied closed history, not verified provider delivery or a profitable strategy. Observed bars determine confirmation/expiry when data has gaps. The 160-bar expiry is an explicit versioned policy. Retrospective supply/demand/S/R, alternating zigzag and other snapshot classifications are excluded as historical signals. Full-size replay latency/storage growth is not certified; replay recomputes the bounded prefix and persists all events, while API/UI summaries are explicitly limited.

SQLite v2; contract 1.2.0; event version p05-causal-v1; snapshot calculations p05-snapshot-v1; shared indicator definitions remain p04-indicators-v1. Original archives and selected upstream snapshot algorithms unchanged. No simulator implementation started.

P05 preview on port 8766 stopped; HTTP smoke server stops itself. Earlier 8765 process untouched. Source ZIP excludes local databases/environments/Git. Checkpoint: `p05-complete`.

Next: **P06-A external sentiment normalization/provider/archive boundaries**, only after explicit “Proceed”.
