# Daily and weekly scenarios — p08-bias-v1

Daily and weekly evaluations are independent. Both use the full completed horizon prefix produced by the existing source calendar aggregation, including session close times and DST. No forming candle enters a rule. `as_of` is the replay clock; `evaluated_at` is the last complete horizon close. Fifty complete bars are required. Missing scheduled bars are never imputed. Long gaps can therefore leave an old last evaluation timestamp; inspect dataset quality alongside the scenario.

| Component | Bullish | Bearish | Other / unavailable |
|---|---|---|---|
| Structure | Last two strict confirmed highs and lows both rise | Both fall | Mixed for other paired sequences. Unavailable without two of each. Constant high/low/close history is neutral. |
| Momentum | Close > EMA20 > EMA50 and Wilder RSI14 > 50 | Close < EMA20 < EMA50 and RSI14 < 50 | Neutral only for equal close/EMAs and RSI 50; otherwise mixed. |
| Reference | Latest close above midpoint of previous 20 complete bars' high/low range | Below midpoint | Equality is neutral. Latest bar is excluded from the reference range. |
| Zone context | Close inside active demand zone | Close inside active supply zone | Both is mixed; no touch is neutral/no vote. |

Strict pivots need three observed bars on both sides and a unique high/low in that seven-bar window. The latest confirmed high supplies a wick/body zone [max(open, close), high]; the latest confirmed low supplies [low, min(open, close)]. These are new explicitly versioned horizon-context rules, not claims that all upstream zone algorithms agree. After confirmation, a close strictly above the supply top or below the demand bottom permanently invalidates that zone for this evaluation. Equality does not invalidate. Only active boundaries are offered as chart levels.

Resolution order: required missing structure/momentum/reference => unavailable; any mixed component or opposing bullish/bearish components => mixed; matching bullish or bearish structure and momentum with no opposition => that direction; all nondirectional => neutral; remaining incomplete directional agreement => mixed. There are no confidence scores or probability estimates. Sentiment is optional labelled context with zero technical vote; P06 still controls its replay availability.

Recompute on each newly complete horizon bar. Explanations provide pivot prices, EMA/RSI values, range boundaries, midpoint and change conditions. A close across the midpoint changes reference context; crossing the prior range breaks that reference. Pivot replacement, EMA/RSI ordering or zone invalidation can change the result. These are recalculated scenarios, not immutable P05 events or order instructions.

Every used aggregated OHLC bar has a source-labelled canonical calculation evidence record with actual open/close availability. Assessments use the existing contract 1.4.0 representation with calculation version p08-bias-v1. Raw daily_bias/weekly_bias include components, levels, evidence IDs, evaluation clock and invalidation text. Chart level findings reference those inputs. Missing/empty history explicitly reports its count; no fabricated candle evidence is created.

UI: open Rules & evidence on either card, then select a level to reveal it on the shared chart. Bias levels are hidden by default to reduce clutter. The selected level participates in price autoscaling. Horizon disagreement is shown without selecting a winner. Existing snapshot overlays and causal events retain their previous semantics.
