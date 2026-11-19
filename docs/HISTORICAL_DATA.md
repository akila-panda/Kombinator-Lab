# Historical data service — P03

## Storage and identity

SQLite storage version **2** (P05 adds event tables; v1 upgrades non-destructively), `.data/history.sqlite3` by default; set `CONFLUENCE_DATA_DIR` to use another directory. Data stays on the local machine. `.data/` is excluded from Git and the source ZIP. Stop the application before copying the database for a consistent backup. No destructive migrations or delete endpoint are implemented. See HISTORICAL_EVENTS.md for the append-only finding journal.

Datasets are immutable. Metadata stores symbol, base granularity, input timezone, UTC coverage `[start,end)`, source label/kind, raw file SHA-256, normalized OHLCV SHA-256, calendar, units, import time and quality report. Dataset IDs hash content plus provenance/settings. Repeating the exact same import returns its existing ID; changing source labels or settings creates a distinct dataset even if normalized prices match. Imports are validated completely before one atomic transaction. This establishes file integrity, not the truth of market prices. Uploaded provenance is always unverified. Synthetic demo datasets have a distinct source kind.

CSV limits: 32 MiB and 250,000 completed minute or hourly candles per dataset. Strict ascending unique timestamps; positive finite prices; valid OHLC geometry; nonnegative volume. Standard quoted CSV and UTF-8 BOM are supported. Optional row metadata must agree with the import settings. Missing volume has unknown units. UI imports use unknown volume units; API callers can explicitly specify tick counts/base units/quote units only when every row has volume.

ISO timestamps with explicit offsets are normalized to UTC. Naive ISO timestamps use the selected IANA timezone (default UTC); nonexistent or ambiguous local times are rejected unless an offset is supplied. Numeric timestamps require an explicit seconds/milliseconds setting. Open times align to base minute/hour boundaries. Forming candles cannot be stored as completed history.

## Calendars

| ID | Daily boundary | Weekly boundary | Scheduled closures |
|---|---|---|---|
| `fixed-utc-v1` | 00:00 UTC | Monday 00:00 to next Monday | None (continuous input) |
| `utc-weekdays-v1` | 00:00 UTC | Monday 00:00 to Saturday 00:00 | Saturday/Sunday; synthetic fixture convention |
| `fx-ny-17-v1` | 17:00 America/New_York | Sunday 17:00 to Friday 17:00 local | Weekend only |

For NY sessions, four-hour candles anchor at local 17:00; daily/weekly boundaries use `zoneinfo` civil-time arithmetic, not fixed epoch-day modulo. UTC boundary shifts between 22:00 and 21:00 across DST. Weekend closure spans 47 hours in spring and 49 in autumn. The supported open FX sessions do not themselves cross the Sunday DST transition. Minute/hour bars are UTC-aligned. A week is considered complete at its scheduled Friday close, rather than waiting through the closed weekend.

[OANDA's official pricing endpoint](https://developer.oanda.com/rest-live-v20/pricing-ep/) documents a default daily alignment of 17:00 in America/New_York with UTC timestamps. This supports the daily convention, but our Sunday-open weekly label and weekend-only schedule are explicit local policies, **not** a promise to reproduce every OANDA instrument, weekly label, provider holiday, maintenance window or session. Choose a calendar that matches the source. Out-of-session CSV rows are rejected rather than silently discarded. No provider data was downloaded in P03.

Quality reports distinguish missing scheduled input slots from scheduled closures. Counts cover only internal gaps between the first and last supplied rows; there is no claim of coverage beyond those edges. At most 100 interval details of each type are retained; total counts are complete.

Aggregates are returned only after their scheduled close and only when all scheduled base candles are present. No forward-fill or fabricated prices. Missing or unfinished groups are excluded and counts reported; completely absent buckets are represented by the dataset gap report, not by synthetic aggregate rows. Returned bars have explicit close times. Unknown volume stays null at the API/contract boundary.

## API

Local OpenAPI is at `/docs`. All timestamps below are UTC Unix seconds; ranges include start and exclude end. No credentials required on this loopback-only development service.

| Request | Purpose |
|---|---|
| `GET /api/datasets?symbol=EUR%2FUSD&limit=100&offset=0` | List stored metadata; pagination |
| `POST /api/datasets/demo?symbol=EUR%2FUSD` | Idempotently store/retrieve synthetic fixture |
| `POST /api/datasets/import` | Raw CSV body; query settings `symbol`, `base_timeframe`, `calendar`, `source_label`, optional `input_timezone`, `timestamp_unit`, `volume_type` |
| `GET /api/datasets/calendars` | Calendar definitions |
| `GET /api/datasets/{id}` | Metadata and quality report |
| `GET /api/datasets/{id}/candles` | Base bars with optional `start`, `end`, `as_of`, `limit`, `warmup` |
| `GET /api/datasets/{id}/aggregate` | Target `interval`, required `as_of`, optional range/pagination/warmup |
| `POST /api/datasets/analyze` | `{ "dataset_id": "…", "interval": "1h", "cutoff": 200 }`, optional dated book `snapshot` |

Base/aggregate pages have up to 10,000 candles plus up to 10,000 separate prior warmup candles. `next_start` is the first omitted candle's open timestamp. Reuse the same range end and clock when paging. `warmup_sufficient` is false when fewer prior completed bars exist. For aggregation, the full available source prefix is grouped before the output range is filtered, preventing false partial groups at query boundaries. The 250,000-row dataset bound also bounds aggregation/analysis work; no caching/background jobs or large-dataset performance guarantee is claimed.

Analysis requires at least 60 completed **target** bars and evaluates detectors on the last 500 target bars; daily/weekly prototype bias uses the complete available prefix. UI replay requests transmit IDs and cutoffs, not history arrays. P05 also computes a full-prefix causal event journal, separate from those retrospective snapshot detectors. A realistic trading simulator remains later work. Legacy `/api/analyze` remains completed-hourly, fixed-UTC compatibility input.

Contract version **1.2.0** retains explicit candle calendars and accepts calendar-specific close times. Old callers omitting calendar get fixed UTC. Clients requiring literal 1.0.0 or 1.1.0 must update. P05 adds explicit retrospective-finding classification and a separate causal journal. Canonical output still coexists with legacy UI fields until P04/P07 migration.
