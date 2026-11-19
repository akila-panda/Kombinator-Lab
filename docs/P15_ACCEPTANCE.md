# P15 training modes

Completed 17 November 2026. P16 remains unstarted.

Practice: save a checkpoint, use New session, select the checkpoint and enter a Practice branch date UTC. Create practice branch recomputes account/chart state from only commands through that time and saves a new immutable record with parent_id. The original ledger is unchanged. Same-boundary commands are retained (including a queued close); future commands are removed. Branching requires a compatible calculation version and time within the saved session. Journal notes remain retrospective review material for retained order IDs.

Blind: select Blind challenge before starting. Date/configuration locks during the active run and only forward minute/candle steps are available. No future price candles are rendered. Analysis is hidden until a prediction is recorded for that clock. Predictions are stored in checkpoints/exports. Dates are shown (optional date hiding was not implemented). Backend refuses branching from blind checkpoints. Local controls are not tamper-proof; another practice session, raw APIs or exported snapshots can be inspected outside the challenge.

Review: select a checkpoint without an active session and choose Review checkpoint. Stored account, findings and journal load without recalculation; trade, close/cancel, clock advancement and save controls are disabled. Read-only review is available even for older incompatible calculation hashes. Original checkpoint records have no mutation route.

Summary version p15-summary-v1: a trade is a fully closed entry lot; partial closes group into that lot. Win/loss/breakeven uses net lot P&L after all commissions. Net realized includes all fees already paid, including entry commissions on open lots. Net equity change includes marked open positions. Maximum balance drawdown is peak-to-trough realized balance sampled after confirmed ledger events, not intraminute equity drawdown. Open positions, pending orders and ambiguous event counts explicitly identify unfinished/uncertain results. No return forecast or profitability claim.

Verification: 222 tests passed in 35.82 seconds, dependency consistency, TypeScript/Vite build and HTTP smoke passed. New integration test checks restored branch position/queued-close state, unchanged parent, blind branch rejection, read-only review and hand-calculated $0.82 net profit/$0.04 balance drawdown. Browser verified blind prediction gating, saved mode, read-only summary and disabled trading/stepping/save. Branch semantics tested through backend integration, not separately in browser. Screenshot screenshots/p15-review.jpg.

P14 compatibility remains intentionally strict: backend Python source changes invalidate resume, while export/review preserves old evidence. No silent migration. Preview port 8766 left running, PID 11319 / tool session 53039. Source ZIP excludes SQLite/raw market data. Next P16 only after explicit Proceed.
