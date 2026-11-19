# P06 external sentiment sources and historical availability

## Connected source and scope

The available source is a **user-imported OANDA-format position/order-book archive**. No OANDA/live market-data connector is available in this session, so no account connection, credential request or live download was attempted. The provider catalog explicitly reports live access unavailable. Imported files and retrieval timestamps are user assertions, not independently verified observations.

`SentimentProvider.select(symbol, as_of)` returns a `Selection` containing eligible books, source identity and an availability reason. `ArchiveProvider` implements local historical selection; `UnavailableProvider` represents absent live/archived access without fabricating scores. A future authorized source must meet the same clock/provenance boundary. No price-derived EMA, volatility or regime metric is treated as external positioning.

## Normalized input

One snapshot contains `instrument`, optional `positionBook` and optional `orderBook` (at least one). Instruments normalize case and slash/underscore forms to EUR_USD, GBP_USD or USD_JPY. Each book contains:

- `time`: observation timestamp with explicit timezone, normalized to UTC whole seconds.
- `retrieved_at`: historical retrieval timestamp, also explicit UTC/offset. It cannot precede observation. It can be absent on import for preservation, but that book is **ineligible for historical scoring**.
- `price`: optional positive finite current reference price; order scoring requires it and never fetches a live substitute.
- Optional positive finite `bucketWidth`; if supplied, adjacent price buckets must not overlap at this width.
- Nonempty `buckets` with unique positive finite prices and long/short percentages in 0–100. Combined percentages in one bucket cannot exceed 100 (small numeric tolerance). Numeric strings are accepted deliberately; booleans, duplicates, nonfinite values and ambiguous timestamps are rejected. Bucket order is normalized by price. Missing buckets are not fabricated and total coverage is not assumed to be 100%.

Archive imports allow up to 100 snapshots and 100,000 total buckets (each book also has a 10,000-bucket bound). UI file limit is 4 MB. Unknown fields are rejected; credentials do not belong in these files.

## Availability and freshness

Both observation and retrieval must be at or before the replay clock. Each imported book kind has a named 86,400-second maximum observation age, inclusive at exactly 24 hours. This is the versioned **application policy**, not a claim about OANDA's publication cadence or appropriate freshness for every strategy.

Selection is independent for position and order books: choose the latest observed eligible book, breaking ties by latest eligible retrieval. A future or late-retrieved newer book cannot hide an older eligible book. Missing retrieval, mismatched instrument, future observation/retrieval or excessive age yields unavailable when no eligible alternative exists. Selection never invents retrieval from observation or local import time.

At a given eligible observation/retrieval coordinate, conflicting payloads are rejected within an archive. A later retrieval can represent a separately timestamped revision. Missing price, zero position mass or no orders near the reference price produce explicit unavailable component results rather than neutral scores. Valid components remain independently available when another component is unavailable.

## Archive identity and persistence

Archives are immutable, addressed by SHA-256 of normalized snapshots plus the supplied label. Exact repeated imports return the same ID. The database stores local import time separately from claimed historical observation/retrieval; import time is never substituted for retrieval. `.data/sentiment.sqlite3` uses archive schema v1; existing history database/event schema v2 is unchanged. Neither database enters Git/source ZIP.

Analysis explicitly pins `archive_id`. A new or backfilled archive cannot silently change an analysis pinned to an older ID. Archived books for other pairs can coexist in one file; selection filters the pair. No global 'latest imported file' or live fallback is used. Inline `snapshot` remains compatible but follows the stricter retrieval/freshness rules. `snapshot` and `archive_id` are mutually exclusive.

The current UI imports one snapshot object or a JSON array, saves it locally and pins the returned ID for analysis. Clearing selection or changing pair/dataset does not delete the saved archive. Saved metadata can be listed through the API; a full saved-archive browsing UI belongs to P07. No browser file-upload completion is claimed in P06 because the extension's file-URL access remains disabled; the archive import and selection paths are verified through API tests and real HTTP.

## Scoring, attribution and contracts

Selected ForexDashboard functions retain their original scoring bodies: position book is a contrarian long-ratio heuristic using 0.65/0.35 thresholds; order book is normalized net long/short share within ±50 instrument pips. Both are bounded −1…1 heuristics, not probabilities or measured institutional behavior. No combined confidence score is invented.

Output identifies `archive:<id>` (or the explicitly supplied inline source), `p06-imported-books-v1`, source kind `user_upload`, and unverified provenance. Canonical evidence carries observation and retrieval times; availability uses retrieval time. Contract 1.3.0 rejects an **available** historical sentiment observation lacking retrieval-time evidence. Old observation-only imports can still be inspected but no longer score as historically available. Existing snapshot/chart/event versions are otherwise unchanged.

## API

| Endpoint | Behavior |
|---|---|
| `GET /api/sentiment/providers` | Available archive source, unavailable live source, policy/version |
| `POST /api/sentiment/archives` | `{label, snapshots: [...]}`; validates and saves immutably |
| `GET /api/sentiment/archives?limit=100&offset=0` | Paginated metadata, provenance and IDs |
| `GET /api/sentiment/archives/{id}` | Metadata; missing ID returns 404 |
| `GET /api/sentiment/archives/{id}/at?symbol=EUR%2FUSD&as_of=<UTC-seconds>` | Clock-bounded selection and scores/reasons |
| `POST /api/analyze` or `/api/datasets/analyze` with `archive_id` | Same selected books and evidence at the analysis clock |

Example synthetic input (not actual market observations):

```json
{
  "label": "synthetic example",
  "snapshots": [{
    "instrument": "EUR_USD",
    "positionBook": {
      "time": "2025-01-01T10:00:00Z",
      "retrieved_at": "2025-01-01T10:01:00Z",
      "buckets": [{"price": "1.08", "longCountPercent": "80", "shortCountPercent": "20"}]
    }
  }]
}
```

## Verification and next boundary

Tests cover symbol/timezone normalization, missing/future retrieval, exact freshness boundaries, per-kind selection, mismatched pairs, malformed percentages/buckets/width, duplicate corrections, zero mass/no nearby orders, JPY pip handling, persistence/idempotence, stable pinned results after new imports, canonical source/evidence, both analysis routes and archive HTTP routes. No real-provider accuracy, delivery timing or distribution-wide book coverage is asserted. P07 owns the fuller analysis UI; simulator work remains after integration acceptance.
