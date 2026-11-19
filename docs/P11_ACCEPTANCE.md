# P11 acceptance — paper entry orders

P11-A/B complete, 16 November 2026. Engine version `p11-orders-v1`; checkpoint `p11-complete`. P12 has not started.

## Gate evidence

- Market buy/sell, limit/stop entries, base-unit positions, cancellation and submitted/accepted/rejected/cancelled/filled ledger events implemented independently of chart analysis.
- Server-owned immutable minute data supplies quotes. Explicit bid-input acknowledgement and fixed simulated spread; Decimal tick rounding and positive executable-price validation. See PAPER_ORDERS.md for lifecycle, fill table and API.
- No submission fills inside an already-revealed bar. Equal-boundary fills precede commands; missing/closed intervals produce no invented fills. Gap prices use the next observed open. End-of-data pending orders remain pending.
- 25 order tests cover all four pending-order directions, spread-aware triggers, favorable/adverse gaps, same-clock and empty-period cancellation, invalid sizes/prices, duplicate commands/orders, USD/JPY precision, zero-rounded quotes, future mutation, prefix/repeated-run consistency, and endpoint validation.
- Final `./verify.sh`: **194 tests passed in 38.15 seconds**, dependency consistency, TypeScript/Vite build and temporary real HTTP smoke (including paper execution) passed. One existing Starlette TestClient deprecation warning.
- `scripts/accept_paper_orders.py` passed against the local P10 EUR/USD minute dataset: two independent market entry lots, cancelled limit, no submission-clock fill and identical repeat response. Exact request scenario/results in paper-orders-p11.json.
- Git whitespace check passed. Frontend source is unchanged; browser re-testing was not needed for this API-only phase. HTTP verification exercised a separate temporary server.

## Operational limits

No order ticket UI yet (P13), no exits/accounting (P12), and no persisted session ledger (P14). Positions are independent entry lots, not netted or funded. Spread is synthetic and constant; no tick path, historical liquidity, partial fills or broker execution. Schema-invalid requests return 422; business-invalid orders are retained in the returned rejection ledger. Session state is rebuilt deterministically from at most 200 ordered commands.

The user's existing port 8766 preview remains running and was not restarted. It predates the new API; new backend routes load on its next restart. The source package includes P11 and excludes local datasets/environments. Next: P12 only after explicit Proceed.
