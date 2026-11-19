# P12 acceptance — exits and account realism

P12-A/B complete, 16 November 2026. Policy `p12-account-v1`; checkpoint `p12-complete`. P13 has not started.

## Implemented

- Separate POST /api/paper/account-replay with USD account settings, SL/TP on entries, manual/full/partial closes and remaining position quantities. P11 entry-only API and tests preserved.
- Gross realized/unrealized P&L, balance, equity, used/free margin, commission totals and marked-at time. USD conversion for EUR/USD, GBP/USD and USD/JPY; Decimal price precision and cents rounding.
- Configurable fixed synthetic spread, commission and deterministic adverse slippage. Entry margin checks include costs and spread/slippage loss; insufficient margin rejects without charging. Financing and automatic liquidation are explicitly excluded in every response. Negative free margin is flagged.
- Protective gap exits use observed executable opens. Both SL/TP touched: conservative stop first with ambiguity evidence. Intrabar entry TP-only touch is deferred; stop touch assumes adverse ordering and is flagged. No fabricated tick path.
- No fill in an already-revealed candle; no fills during absent minutes. Queued close, stale mark, end-of-data, invalid bracket, invalid close and competing order policies are documented in PAPER_ACCOUNT.md.

## Verification

Final ./verify.sh passed: **220 tests in 32.34 seconds**, dependency consistency, TypeScript/Vite build and real temporary HTTP smoke including account open/close/cost reconciliation. One pre-existing Starlette TestClient deprecation warning.

26 new accounting cases cover hand-calculated long/short and partial closes, costs, no double counting, SL/TP ambiguity, gap prices, limit constraints, same-bar entry/exit handling, margin admission/calls, JPY conversions, stale gaps, future mutation, prefix/repeatability and API validation. All prior 194 tests passed.

scripts/accept_paper_account.py passed on real P10 minute history: 10,000-unit buy, 4,000/6,000 manual closes, synthetic spread/slippage and commissions; balance/equity reconcile and repeated output is identical. Exact evidence in paper-account-p12.json. The hand-calculated 100,000-unit example in PAPER_ACCOUNT.md matches test results.

No frontend source/dependency changes. Browser re-testing was not required for this backend phase. Git whitespace check passed. Source ZIP verified and excludes local data/environments.

## Handoff and limits

The port 8766 preview was left untouched; it predates new routes and will load them on its next restart. HTTP acceptance used its own temporary server, stopped automatically.

P13 will add order controls and account UI. P14 persistence/journal and P15 training remain deferred. No funded-account guarantee, broker execution, tick reconstruction, live/historical variable spread, liquidity, financing, or automatic liquidation. Brackets cannot yet be amended; no netting of opposing lots. Server recomputes stateless sessions from at most 200 commands. Settings are fixed per run. Next: P13 only after explicit Proceed.
