# Bounded real-data acceptance source

Acquired 13 November 2026: Dukascopy EUR/USD **bid** H1 observations for January–March 2024, using the public historical endpoint. This is provider history, not synthetic data, not a consolidated market price, and not an executable bid/ask spread model.

- Coverage actually received: 2024-01-01 22:00 UTC through 2024-04-01 00:00 UTC (exclusive); 1,539 observed hourly bars.
- Source URLs and SHA-256 hashes: real-data-p09.json. Raw files remain in the outer workspace `work/eurusd-2024-0{1,2,3}.json`.
- Normalized CSV: `.data/p09/eurusd-2024-q1-bid-h1.csv`. Immutable imported dataset is listed in Saved dataset as “Dukascopy EUR/USD BID H1 · 2024 Q1 · observed bars”.
- Calendar: New York 17:00 FX sessions, including DST. 623 closed hourly slots; zero missing scheduled bars between the first/last observations. No coverage before/after those edges is assumed. Holidays/maintenance are not independently modelled.
- Decimal price-unit accumulation and cumulative time deltas decode the provider response. Every output hour is present in the response; unlike the reference client's optional normalization, this script never inserts flat candles into gaps. Volume is deliberately omitted because this integration does not validate its units.
- No provider delivery timestamps are present for historical bars. Availability assumes completion of the supplied candle. This validates prefix/replay logic, not historical feed delivery latency.
- The UI continues to mark an imported file as provenance unverified; downloaded-source evidence and hashes are documented here rather than silently upgrading arbitrary user-upload trust.

Primary references: [Dukascopy historical export](https://wiki.dukascopy.com/en/development/data-export/), and the [client author's URL generator](https://github.com/Leo4815162342/dukascopy-node/blob/master/src/url-generator/index.ts), [response decoder](https://github.com/Leo4815162342/dukascopy-node/blob/master/src/data-normaliser/index.ts) and [instrument metadata](https://github.com/Leo4815162342/dukascopy-node/blob/master/src/utils/instrument-meta-data/generated/instrument-meta-data.json). EUR/USD's current API code is EUR-USD. The legacy BI5 endpoint failed; the current JSON endpoint succeeded with HTTP 200.

## Reproduce locally

Download the three monthly JSON responses to a local directory, with a bounded timeout. Example for January (replace final month with 2 and 3 for February/March):

```bash
curl --fail --location --max-time 25 -A 'Mozilla/5.0' \
  -H 'Referer: https://widgets.dukascopy.com/en/historical-data-export' \
  'https://jetta.dukascopy.com/v1/candles/hour/EUR-USD/BID/2024/1' \
  -o january.json
.venv/bin/python scripts/accept_real_history.py january.json february.json march.json
```

The acceptance script validates exact months, ordered unique aligned times, OHLC integrity and session hours; imports through the application API; analyzes H1/H4/D1; compares repeat responses; mutates future prices beyond a replay prefix; checks invalid CSV rejection; and regenerates the local evidence report. It does not access the network itself. Raw/normalized market files and SQLite databases are excluded from the source ZIP. Re-downloads can differ if the provider revises history; compare the recorded hashes.

The observations produced 500 visible H1 bars (the existing display bound), 384 H4 bars, 64 complete daily candles and 12 completed weekly candles. Daily bias is mixed; weekly bias is unavailable because 50 weekly candles are required. No external sentiment archive was supplied.
