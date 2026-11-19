# P12 USD paper account

Execution policy `p12-account-v1`. API: `POST /api/paper/account-replay`. The P11 `/api/paper/replay` endpoint retains its entry-only semantics and version. The account endpoint extends its request with an `account` object, optional `stop_loss`/`take_profit` on submit, and `action: "close"` targeting the entry `order_id`. P13 will add the trading workspace; this phase has no order UI changes.

## Settings and valuation

| Setting | Default | Meaning |
|---|---|---|
| initial_balance | 10000 | USD starting cash, rounded to cents; at least one cent |
| leverage | 30 | Integer 1–500; margin = USD notional / leverage |
| commission_per_100k | 3.5 | USD per 100,000 base units on each entry/exit fill; 0–1000 |
| slippage_pips | 0 | Fixed adverse slippage on market and stop fills, 0–100 pips |
| spread_pips | 1 | Existing top-level constant synthetic bid/ask spread, 0–100 pips |

Spread and slippage must be whole instrument ticks. Entry/exit prices use the P11 Decimal half-up tick policy. Commission and each realized/marked position P&L round to USD cents, half up. This can make many small partial fills cost slightly differently from one large fill. Fees are charged once per actual fill; rejected orders incur none. Slippage is adverse on both market entry and market exit, also on stops. Limits and take-profit exits receive no adverse slippage, preserving their price constraints; marketable/gapped limits may improve at the observed open.

Prices are bid candles plus a declared synthetic spread, not historical executable bid/ask. No liquidity/partial-fill model. “Partial close” means a user-requested smaller quantity filled in full.

Open long positions mark at bid close; shorts mark at ask close. The last observed closed minute supplies valuation; `mark_time` exposes stale marks across gaps/closed markets. Pending close orders do not affect cash until filled. No forced closure at dataset end.

- Gross quote P&L = (exit − entry) × units for longs; reverse for shorts.
- EUR/USD and GBP/USD P&L is already USD. USD/JPY P&L in JPY is divided by that fill's executable exit price, or the executable mark price for unrealized P&L. Conversion price is recorded on JPY exits. This is the explicit single-pair simulation convention, not a separately sourced conversion feed.
- USD notional for EUR/USD/GBP/USD = remaining units × bid valuation price. USD/JPY base units already represent USD notional.
- Balance = initial balance + realized gross USD P&L − all charged commissions.
- Equity = balance + unrealized USD P&L.
- Used margin = sum of each open lot's rounded USD notional / leverage.
- Free margin = equity − used margin.

Positions remain independent hedged lots; opposing positions do not net or offset margin. Realized P&L fields are **gross**; commission is separate. Unfilled future commissions/slippage are not deducted from unrealized P&L.

## Margin and deterministic ordering

Commands retain P11 minute alignment, chronological list ordering, uniqueness and coverage rules. Fill confirmation timestamps are at minute close; `bar_open_time` identifies pricing history. A close submitted at a boundary executes at the next observed minute open, never retroactively in the minute just revealed.

For each observed minute:

1. Apply commands known at its open (including commands placed during a gap).
2. Execute protective gap exits for existing positions at executable open; these take precedence over queued manual closes.
3. Execute queued manual closes at executable open, with adverse slippage.
4. Fill eligible open entries, then intrabar entries, preserving accepted order within each group. Check free margin including immediate spread/slippage loss and entry commission. Insufficient margin rejects the order at fill, with no position or commission.
5. Apply protective exits to remaining positions. Mark the account at that minute close.

Margin funding uses existing positions marked at the minute open. New entries use their own entry bid quote, preventing hypothetical favorable open marks from financing later entries. Unknown-time intrabar protective exits cannot free margin or profits for an earlier entry in the same minute. This conservative scheduling can reject an entry that a tick-based model might accept. Stable order, rather than a fabricated tick sequence, decides competing entries.

Open-position margin updates with the valuation price. Negative free margin sets `margin_call: true`. **Automatic liquidation is excluded**; the account may become negative after a gap. There is no broker-specific maintenance-margin/stop-out policy. **Financing/swaps are excluded**, explicitly in every response. No interest, weekend carry charge, liquidity or broker performance is implied.

## Exits, ambiguity and gaps

SL/TP prices normalize to instrument ticks. At entry fill, SL must be below a long/above a short and TP above a long/below a short. A gap that makes the bracket invalid rejects the entry; it does not silently move protection. Brackets are immutable for this phase; there is no amend command.

For existing positions, a gapped stop uses the worse observed executable open plus adverse slippage; a gapped take-profit uses the improved executable open. Newly opened market entries whose stop is already crossed by the opposite side of the spread close at the executable open.

For intrabar checks, long exits use bid high/low, short exits use synthetic ask high/low. A bar touching both SL and TP resolves **stop first** and records `ambiguous: true`. No finer-than-minute data is available in this dataset.

A new entry at the minute open may use that minute's entire range. For an entry triggered intrabar, high/low order is unknown: a touched stop is conservatively treated as occurring after entry and flagged ambiguous. A TP-only touch is deferred with `ambiguous_exit_deferred`, since it may have happened before entry. Both touched again resolve stop first. These are explicit conservative assumptions, not reconstructed tick paths.

Manual close: target `order_id`, optional positive integer `units`; omission closes the remaining position. A second pending close, unknown/closed position, excess quantity or unrelated fields produces `close_rejected`. The quantity is checked when submitted. If a protective gap exit closes the position before its queued manual close, the latter is rejected without another fill/charge. Partial closes reduce remaining units and margin; the remaining units retain their SL/TP. They can exit later in the same minute.

Missing minutes produce no fills; existing positions/orders carry forward. Every close event includes reason, quantity, price, gross P&L, commission, resulting balance, ambiguity flag and source bar time. Pending manual closes are returned at end-of-data rather than invented fills.

## Hand-calculated example

EUR/USD, default one-pip spread, commission $3.50/100k per side, zero slippage:

- Buy 100,000 at bid 1.10000 → entry ask 1.10010, commission $3.50.
- Close 40,000 at bid 1.10100 → gross $36.00, commission $1.40. Balance $10,031.10; remaining unrealized $54.00 at that mark; equity $10,085.10. Remaining margin at 30:1 = 60,000 × 1.101 / 30 = $2,202.00.
- Close remaining 60,000 at bid 1.10200 → gross $114.00, commission $2.10.
- Total gross P&L $150.00, total commission $7.00, final balance/equity $10,143.00, zero margin.

These values are executable test fixtures, alongside short, gap, ambiguity, JPY conversion and cost examples in tests/test_accounting.py.

## Request extension

Use the P11 dataset/start/clock/input_price_basis fields. Add, for example:

```json
{
  "account": {"initial_balance":10000,"leverage":30,"commission_per_100k":3.5,"slippage_pips":0.5},
  "commands": [
    {"command_id":"buy","order_id":"one","time":1704456420,"action":"submit","side":"buy","kind":"market","units":10000,"stop_loss":1.08,"take_profit":1.12},
    {"command_id":"partial","order_id":"one","time":1704456480,"action":"close","units":4000},
    {"command_id":"rest","order_id":"one","time":1704456540,"action":"close"}
  ]
}
```

At most 200 commands; replay is deterministic and stateless. Resubmit only commands through the desired clock. No ledger persistence yet (P14). Settings are fixed for the run; changing them creates a different simulation.

Reproduce the local real-data scenario with `.venv/bin/python scripts/accept_paper_account.py`; results are in paper-account-p12.json. The existing 8766 preview remains untouched and predates these routes; the new endpoint loads on its next restart. Temporary HTTP verification uses a separate server.
