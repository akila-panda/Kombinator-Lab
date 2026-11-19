# P10 historical replay

Completed 13 November 2026. Open **Trade simulator · replay**, select EUR/USD and the Dukascopy minute dataset, enter a UTC date and press **Go to date**. Try `2024-01-05T12:07` for warmed hourly analysis and two forming candles.

## Data and reproduction

The bounded dataset contains 7,170 observed EUR/USD BID minutes from 2 January 2024 00:00 through 9 January 2024 00:00 UTC (end exclusive). There are 30 missing scheduled minutes under the NY17 calendar. No 2022 data is included. Prices are bid OHLC, not ticks or executable bid/ask quotes. Volume is unknown and omitted. Exact source URLs, SHA-256 hashes, coverage and gap metadata are in minute-data-p10.json. Raw data remains local and is excluded from the source ZIP. Provider downloads may subsequently change.

Download each of the seven `sources[].url` entries in minute-data-p10.json to a local directory, named `2024-01-2.json` through `2024-01-8.json`. The official Dukascopy endpoint requires a browser user agent and historical-export referer; for example:

```sh
curl --fail --max-time 25 -A 'Mozilla/5.0' -H 'Referer: https://widgets.dukascopy.com/en/historical-data-export' 'https://jetta.dukascopy.com/v1/candles/minute/EUR-USD/BID/2024/1/2' -o /tmp/2024-01-2.json
# Repeat for days 3 through 8, including empty weekend responses.
.venv/bin/python scripts/import_replay_minutes.py /tmp
```

The importer validates minute alignment, converts only observed bars and imports through the existing immutable dataset store. See REAL_DATA_P09.md for provider context and decoding provenance. Imported-source trust remains unverified; acquired bytes are separately hashed.

## Clock API and timing

`POST /api/replay/state` accepts `dataset_id`, integer UTC Unix-seconds `clock`, `action` (seek/minute/candle), and `timeframe` (15m/1h for candle stepping). Only minute-aligned clocks within dataset start/end are accepted; the exclusive coverage end is accepted as the terminal clock.

The server calculates deterministic snapshots. Wall time never advances it; the client schedules requests at a maximum of 1, 4 or 10 minutes per second and waits for each response. Pause cancels pending work and rejects stale responses. Changing dataset, pair, date or workspace stops playback. This phase has no persisted session; order-ledger authority is a P11 concern.

Seek preserves the requested clock, including closed markets. Next minute advances to the next recorded minute close, skipping closed/missing intervals explicitly. Next candle advances to the next selected UTC boundary, even when no observations exist. At dataset end playback stops and steps are disabled.

Both chart panes share one time axis and one server clock. Only minutes whose close is at or before that clock enter either pane. Gold forming candles aggregate revealed OHLC only; incomplete forming buckets are labelled. Missing minutes are never interpolated. Completed higher-timeframe buckets require all scheduled minutes; incomplete past buckets are excluded and counted. The latest 400 complete bars per pane are displayed.

Hourly analysis starts after 60 complete hours and is evaluated only through the last complete hourly close. A bounded 16-entry cache reuses immutable completed snapshots. Daily/weekly bias remains explicitly unavailable when its independent 50-bar requirement is unmet. Snapshot evidence retains retrospective/provisional labels. No unseen prices enter analysis; coverage metadata can describe the entire dataset.

## Limits

This is minute-close replay, not movement within a minute. There are no paper orders, fills, spreads, account balances or persisted training sessions yet. Playback rate is a ceiling, not a performance guarantee. The NY17 calendar does not encode every holiday or maintenance closure. Only the imported pair/dates are available. P11 adds the order engine after authorization.
