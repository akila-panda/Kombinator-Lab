# P05 historical finding events

## Two distinct outputs

`contract.findings` and the existing chart overlays are **retrospective snapshot annotations**, now explicitly marked `retrospective_findings_only: true` in contract 1.2.0. Every compatibility finding is provisional; its origin timestamp does not mean it was available then. Snapshot RSI divergence is also excluded from historical confirmation because its prior calculation used a moving 500-bar seed. The chart and evidence heading state this limitation.

`historical` is the separate causal output, version **p05-causal-v1**. It evaluates all completed target bars in chronological order, using actual calendar close times. Indicators start from the first available dataset bar, so later movement of a visible chart window cannot revise historical RSI/ATR values. Only confirmed records at the requested clock appear in `available_findings`. That name denotes known historical facts, not an active entry recommendation. BOS/CHoCH facts remain confirmed historical records; levels/zones/divergences can become invalidated or expire.

The API summary returns at most 100 retained confirmed findings and 100 recent transition events, with full counts and an explicit truncation flag. The UI shows the latest 10 retained confirmed records, with separate origin and confirmation times. Provisional, invalidated and expired histories remain accessible in the journal API. Legacy array requests replay deterministically but do not persist a journal; stored dataset analysis persists events.

## Event model and transitions

Exported schema: `contracts/historical-event.schema.json`, also `/api/contracts` → `historical_event`. Each immutable event contains deterministic event/finding IDs, source ID, symbol, timeframe, calendar, calculation version, occurrence and availability timestamps, state, direction, prices, reason, optional structure label/replacement reference, and complete closed-candle OHLC evidence.

IDs hash version + source identity + symbol/timeframe/calendar + finding kind + origin candle values (+ related level when needed). They do not include the current replay clock, full future dataset content or a changing snapshot ID. Dataset identity itself is immutable; importing modified data creates a separate source/dataset, not a revision of the old journal.

- **Occurrence → provisional:** a candidate is observable, but not necessarily usable as a confirmed finding. Availability is never backdated to an earlier origin.
- **Confirmation → confirmed:** the required closed-candle evidence exists. First event and confirmation can share a clock for a pattern detected only once its complete evidence exists.
- **Invalidation → invalidated:** a candidate fails its right-side test, or a later close breaks a confirmed level/zone/divergence extreme. A rejected provisional candidate has no confirmation time.
- **Expiration → expired:** an unbroken confirmed pivot level, FVG, order block or divergence expires after 160 later completed target bars. This is an explicit versioned retention policy, not a market law. Break facts do not expire.
- **Revision:** records a first zone touch or a newly confirmed same-side pivot becoming the structure reference. It retains the prior geometry, confirmation event and state (including terminal state). A revision never silently overwrites or resurrects the old finding.

State at time T is a projection of events with `available_at <= T`. Event evidence must contain valid positive finite OHLC geometry with candle close at or before availability. State changes and reasons are separate immutable records; querying an earlier clock filters later transitions out.

## Causal detector rules / repairs

| Finding | Causal policy | Repair relative to snapshot behavior |
|---|---|---|
| Pivot / HH HL LH LL EQH EQL | Strict 3-left, 3-right high/low. Candidate at origin close; confirm at third right candle close. Ties defeat the strict candidate. Labels compare previously confirmed same-side pivot. | No alternating-zigzag replacement of a previously confirmed extremum; new reference is a revision event. |
| BOS / CHoCH | Evaluate already confirmed, unbroken levels before admitting this bar's newly confirmed pivots. Trend uses latest known high/low labels (HH+HL bullish, LH+LL bearish, otherwise neutral). Opposing break is CHoCH; same/neutral is BOS. | No current full-window trend applied retrospectively to old breaks. BOS buffer uses max(instrument pip, 0.05×ATR at the break candle); CHoCH has no ATR buffer. No rescanning past breaks with later ATR. |
| FVG | Three-candle gap, middle body ≥0.5×previous ATR and width ≥0.15×ATR. Confirm at third close; origin is first candle. | No historical availability at the origin. Subsequent tests/invalidations are retained, not silently dropped or reordered by current distance. |
| Order block | Opposite candle preceding body displacement ≥1.3×previous ATR; opposite range ≥0.3×ATR. Confirm at displacement close. | Explicit availability rather than origin; no arbitrary wait for an additional candle or current-distance filtering. |
| RSI divergence | Adjacent confirmed same-side pivots 4–80 target bars apart; lower low with higher RSI / higher high with lower RSI. Confirm when second pivot confirms. | Uses full-prefix Wilder RSI, fixed chronological pivots and actual close-time evidence, not a moving 500-bar RSI seed. |

Missing scheduled bars stay flagged by P03; no candles are fabricated. Confirmation, TTL and indicator warmup count **observed completed target bars**, so a data gap can delay confirmation. The model does not claim continuous coverage, delivery-time accuracy or broker tick-level execution. Price evidence records supplied historical candles, not independently verified market observations.

## Explicit exclusions

Legacy alternating zigzag, current snapshot supply/demand clustering/freshness/quality, retrospective S/R clusters, candle-pattern panels and snapshot BOS/CHoCH/FX zone overlays are not causal journal signals. Their normalized snapshot outputs remain for research, visibly separated from historical events. Momentum/regime and daily/weekly bias remain current-clock assessments, not historical event series. P05 does not claim to repair every upstream algorithm or introduce a simulator/order engine.

## Persistence and queries

SQLite schema **v2** adds `finding_events` and `event_runs` to P03's database; v1 upgrades non-destructively without rewriting datasets. Older dataset metadata may still record the storage version at import; `PRAGMA user_version` is the current database schema. Original source ZIP and source delivery exclude `.data/`.

Dataset analysis appends events transactionally and saves a count/fingerprint for the computed clock. Existing event IDs must have exactly matching serialized payloads; replay conflicts abort with HTTP 500 `event_journal_conflict` rather than overwrite. Original source records are immutable. Run and event version keys permit a future calculation-version migration without editing an old journal. No retention/deletion action is implemented.

`GET /api/datasets/{id}/events?interval=1h&as_of=<UTC-seconds>&after=-1&limit=100`

- `after` is the exclusive journal position returned by `next_after`; limit 1–1,000.
- Only events available by `as_of` are returned, in deterministic emission order. Computed-through metadata is capped at the requested clock so later analysis does not alter an earlier available response.
- `status` is unavailable before coverage exists, before dataset coverage starts, or beyond the last computed clock. Do not treat a partial journal as proof that no events occurred. Run dataset analysis at the desired cutoff first.
- A later analysis does not rewrite earlier saved events; earlier-clock analysis and pagination are reproducible after reopening the database.
- Replay currently recomputes the complete available target prefix before validating/appending. It is bounded by the P03 input limit, but full-size latency and disk-growth benchmarks are not claimed. Incremental replay/cache optimization remains future work; no silent history truncation occurs in calculation or storage.

## Verification and next boundary

Fixtures test every prefix against full replay, third-right-close availability, defeated candidates, break detection before later volatility changes, expiration evidence, FVG/OB confirmation/invalidation, RSI divergence confirmation, calendar close times, append-only/idempotent storage, earlier-clock reads after later runs, schema validation, v1 migration and API separation. Existing future-prefix regressions remain active.

P06 is next: external sentiment provider/archive boundaries. No external source was fetched or account connected during P05.
