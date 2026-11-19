# Canonical contracts — version 1.3.0 (P06)

Authoritative implementation: `backend/contracts.py`. Input compatibility boundary: `backend/requests.py`. Current adapter bridge: `backend/contract_adapter.py`.

Schemas and examples are exported by `python scripts/export_contracts.py` using the project virtual environment. `GET /api/contracts` exposes the same schemas and instrument registry. Tests check published schema drift. JSON Schema describes structural requirements; Pydantic validators additionally enforce cross-field timing, lifecycle and reference constraints.

## Units and conventions

| Value | Convention |
|---|---|
| Timestamps | Integer UTC Unix **seconds**, whole-second precision; no millisecond inference in canonical contracts |
| Candle interval | Open-inclusive, close-exclusive; `close_time` is scheduled end, not a final tick timestamp |
| Candle observation | `observed_at` is when the candle state is available under the declared data model; must be within snapshot clock |
| Prices | Finite positive quote-currency units per one base-currency unit; raw values are not rounded to display precision |
| Pip/tick metadata | Decimal values serialized as decimal strings; pip must be an integer multiple of tick |
| Instrument precision | Display/instrument default, not permission to silently round source data |
| Volume | Nonnegative finite value with explicit units, or null/unknown; missing values are not measured zero |
| Score | External sentiment score is a heuristic in [-1, 1], not a probability |
| Direction | Bullish/bearish/neutral/mixed; null when not assessed, rather than inventing neutral |

Supported registry: EUR/USD and GBP/USD use pip 0.0001, tick 0.00001 and precision 5; USD/JPY uses pip 0.01, tick 0.001 and precision 3. These are **local defaults**, not verified specifications for any broker. Instruments include base/quote currencies, pricing metadata source and base-unit quantity convention. Account money and contract-size/execution rules belong to later simulator phases.

P03 version 1.1.0 adds `calendar` to candles and supports `fixed-utc-v1`, `utc-weekdays-v1` and `fx-ny-17-v1` in candles/snapshots. The default remains fixed UTC. Supported intervals are `1m`, `5m`, `15m`, `1h`, `4h`, `d1`, `w1`. Close times must match the selected calendar. See [calendar and storage semantics](../HISTORICAL_DATA.md). Literal-version 1.0.0 clients must migrate; regenerated schemas are authoritative.

## Models

### DataSource and CanonicalCandle

A source identifies synthetic, uploaded, provider or unknown input and declared volume units. The current API does not allow a caller to assert independently verified provenance. A source declaration is not proof of provenance.

Each candle carries ID, instrument, source, timeframe, open/close/observation times, state, OHLC, volume type and quality flags. OHLC geometry, duration/alignment and finite positive values are checked. Completed candles cannot be observed before close; forming candles must be observed after open and before scheduled close.

`examples.json` contains both completed and forming **minute** examples. These are schema examples, not a newly implemented minute feed.

### MarketSnapshot

Identifies the input source, symbol, requested and base timeframe, clock, input coverage, count and calendar. The compatibility adapter fingerprints only the consumed prefix and normalized numeric inputs. Future candles do not alter a historical snapshot ID. A snapshot ID identifies market inputs, not a permanent finding/event.

`input_end` is the exclusive coverage end. Output candles cannot exceed coverage, source context or available input count. A forming candle may have a scheduled close after the clock, but its observed portion may not extend beyond input coverage.

Current uploaded history assumes completed candles became available at their close; provider delivery latency is not established. The compatibility adapter reports source uncertainty and does not claim archived arrival-time accuracy.

### Evidence, Finding and Overlay

Evidence has a source, symbol, occurrence and availability time. Candle evidence references an existing canonical candle and must agree with its context/timing. Calculation evidence explains derived inputs; observation evidence identifies an external book observation.

Findings require snapshot/symbol/timeframe, module, source version, calculation version, prices, nonempty evidence references, explanation, invalidation condition and timing note. Lifecycle rules:

- Provisional: confirmation is absent.
- Confirmed: confirmation must not precede occurrence or evidence availability.
- Invalidated/expired: require prior confirmation and the matching transition timestamp.
- No lifecycle event or evidence availability may exceed the snapshot clock.

Empty, missing and duplicate evidence references fail validation. Snapshot-derived structure/zone findings remain provisional because their historical confirmation has not been established. Divergence records preserve the detector's known confirmation candle, but this does not make them immutable historical records. Current invalidation conditions explicitly say that lifecycle tracking is not implemented.

Overlays reference a finding and contain one marker/level point, two chronological line points, or valid zone geometry. Backend zone geometry is included for STRUCT supply/demand and FX Desk FVG/order blocks, and price-line geometry is included for divergence. The current frontend still uses legacy fields; P07 will consume these overlays.

### Assessment

Carries versioned module output, numeric metrics, evidence and optional direction. Available output requires evidence. Unavailable/insufficient-history output requires explanation and cannot carry scores, evidence or a neutral-direction substitute. Available empty metrics can mean “no pattern/level detected”; it is distinct from unavailable data.

P02 validates actual outputs from all four systems: structure/momentum; RSI/S/R/candle patterns; EMA alignment; daily pivots. It does not pretend that the original applications are fully migrated to shared services.

### SentimentResult and SentimentObservation

Each book observation declares its source, observation time, optional retrieval time, availability basis, status and score. Available observations require matching evidence. Retrieval cannot precede observation; when supplied, it governs availability at the replay clock. Without retrieval metadata, availability is explicitly `observation_time_only`, not independently verified historical delivery.

The current bridge retains the existing 24-hour freshness rule. Future, unretrieved-at-clock, stale or unavailable books carry no score/evidence. Source-specific freshness policy and an archive/provider service are P06 work.

## API compatibility and errors

`POST /api/analyze` retains the existing UI fields and adds `contract`, a validated AnalysisEnvelope. Existing `candles`, `findings`, `indicators`, `sentiment`, bias and chart fields remain present.

Optional input additions:

- `data_source`: source ID/kind/description and declared volume type. Legacy callers default to unknown source, not synthetic or verified.
- `base_timeframe`: currently only `1h` is accepted.
- Candle `symbol` and `timeframe`: optional; if supplied, must match the request.
- Candle `state`: only completed input is currently accepted.
- Imported book `retrieved_at`: optional timezone-aware ISO timestamp.

The UI now explicitly labels demo versus uploaded input. The legacy array endpoint accepts **60–12,000 completed hourly candles**. P03 dataset imports separately accept up to 250,000 completed minute/hour rows; minute input is aggregated before the selected-timeframe analysis. Forming candles remain schema-only. Raw candle open times are capped one hour before the canonical timestamp ceiling so their close remains representable.

Input validation now rejects unknown fields, bool timestamps/prices, mixed symbols/timeframes, claimed verified provenance, known volume units with missing values, timezone-naive book times, empty book data and percentages outside [0,100]. Book numeric strings remain supported. Book ISO offsets are normalized to UTC; whole-second precision is required. Supported book JSON is the documented wrapper, not an unrestricted native provider response.

- Invalid caller data → HTTP 422.
- Invalid internally generated contract output → HTTP 500 with an explicit boundary-error message, not a fabricated neutral result or a misleading client-error response.
- Unavailable sentiment/history → an explicit data state where supported, not a fabricated score.

## Migration sequence and intentional limits

1. P02 supplies strict contracts and an additive compatibility envelope. Legacy UI and function inputs remain operational.
2. P03 completed persistent datasets, source fingerprints, minute ingestion and session-aware aggregation; dataset-ID analysis now uses this service.
3. P04 routes module calculations through canonical services and removes active duplicate indicator paths.
4. P05 implements durable finding identities, availability events and invalidation histories. Current IDs are **snapshot scoped**, not stable cross-snapshot lifecycle IDs.
5. P06 implements fuller provider normalization/freshness/coverage. Current sentiment is uploaded snapshots only.
6. P07 consumes canonical findings/overlays in the UI.

P03 implements local candle storage and paginated queries. A simulator, live feeds, complete bias rules, provider delivery verification remain later work. P05 adds the separate durable historical event journal. The contract envelope is intentionally more verbose than the legacy response.

## Example files

- `candle.schema.json`: standalone candle schema, including minute/forming states.
- `analysis-envelope.schema.json`: canonical output schema and nested definitions.
- `analysis-request.schema.json`: currently accepted HTTP input schema.
- `instruments.json`: local registry metadata.
- `examples.json`: validated synthetic minute candles and a small real-pipeline envelope containing all four modules plus two invented book observations. **No prices or book values in this file are actual market observations.**

P03 update: completed minute/hour dataset ingestion, persistence and calendar aggregation are implemented. The legacy hourly array endpoint remains available. P05 subsequently adds a separate event lifecycle; provider feeds and simulator work remain deferred.

P05: `retrospective_findings_only: true` explicitly classifies this envelope’s snapshot annotations, all provisional. Historical confirmations/transitions are in the separate validated event journal, not these overlays. See [event schema and lifecycle policy](../HISTORICAL_EVENTS.md). Event schema is exported as `historical-event.schema.json`; calculation version p05-causal-v1.

P06: available historical sentiment now requires explicit retrieval-time availability. Missing retrieval remains representable only as unavailable. Requests support a pinned archive ID, mutually exclusive with inline snapshots. Exported `sentiment-archive.schema.json` describes archive input; see SENTIMENT_SOURCES.md in the parent docs directory.
