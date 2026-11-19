# Confluence — combined analysis preview

A local React + FastAPI application assembled from selected components of the four supplied repositories. Assembly preceded integration testing, as requested. This is an executable integration preview, not the complete trading-analysis product or an audited trading strategy.

## Development plan

Follow [the current development plan](docs/DEVELOPMENT_PLAN.md), [beta release plan](docs/BETA_RELEASE_PLAN.md), and [current status](docs/DEVELOPMENT_STATUS.md). Simulator features through P15 are implemented; P16 release acceptance is in progress. See the [beta candidate guide](docs/BETA_QUICKSTART.md).

## Personal testing guide

Start with [Mac setup, retail trader journey and test checklist](docs/RETAIL_TRADER_TEST_GUIDE.md). It covers the current beta features, data import, simulated orders, save/recovery and feedback.

## Run and verify

Verified P01 environment: macOS x86_64, Python 3.14.3, Node 22.21.1, npm 10.9.4. `.python-version` and `.nvmrc` record these versions. Setup accepts Python 3.11+ and Node 22.12+, but other versions/platforms have not been verified.

```bash
./setup.sh
./verify.sh
./start.sh
```

`setup.sh` creates an isolated project `.venv`, installs the exact Python dependency snapshot from `requirements.lock.txt`, installs frontend dependencies using `npm ci`, and builds the frontend. It can be rerun after a partial installation. `requirements.txt` lists direct dependencies; update and verify the lockfile whenever those change. The lock is a version snapshot tested on the environment above, not a cross-platform hash-locked dependency guarantee.

`verify.sh` runs dependency consistency, the Python integration tests, TypeScript/Vite build, and a real HTTP startup/assets/analysis smoke check on an automatically assigned loopback port. That temporary server shuts down afterward; it does not touch a preview already running on port 8765.

`start.sh` runs setup when needed, refreshes a stale frontend bundle, and serves at http://127.0.0.1:8765. Stop with Ctrl+C. Use `PORT=8766 ./start.sh` if the default port is already occupied; do not terminate an unidentified process. It binds only to loopback and needs no account or API keys. Set `PYTHON_BIN` for the interpreter to use when creating a new environment.

For frontend live reload run `npm run dev` in `frontend/` while the API runs on port 8765. Vite proxies `/api` to that port.

See [current P04 adapter coverage and indicator policies](docs/ANALYSIS_ADAPTERS.md), with historical source mapping in [the component map](docs/COMPONENT_MAP.md).

## Canonical contracts (P02–P03)

The analysis response now includes a validated `contract` envelope while preserving the existing dashboard fields. See [contract definitions, examples and migration notes](docs/contracts/README.md). Schemas and the instrument registry are also available at `/api/contracts`.

P03 accepts completed minute/hour CSV datasets and aggregates them for analysis. Forming candles remain schema-only. Imported book timestamps now require an explicit timezone, and per-candle symbol/timeframe metadata must match the request.

## Historical finding lifecycle (P05)

[The causal event journal](docs/HISTORICAL_EVENTS.md) records occurrence, confirmation, invalidation, expiration and revisions. Historical events are available only after their evidence closes. Dataset analysis saves an append-only journal; the UI separates those records from retrospective chart overlays. Contract 1.2.0 explicitly labels snapshot findings; SQLite v1 upgrades non-destructively to v2.

## External sentiment archives (P06)

[Sentiment source policy and API](docs/SENTIMENT_SOURCES.md): import one OANDA-format book or a JSON array; the UI saves and pins an immutable local archive. Historical scoring requires both observation and retrieval timestamps at or before replay, with a 24-hour age limit. Live access is explicitly unavailable; imported provenance is unverified.

## What is combined

| Origin | Connected contribution |
|---|---|
| STRUCT.ai | Original chart component; swing structure; supply/demand; BOS/CHoCH; momentum |
| FX Signal Desk | Indicators; support/resistance; FVGs; order blocks; candle patterns |
| Forex Scalper Agent V2 | Shared EMA20/EMA50 alignment, candle momentum and selected ATR volatility thresholds |
| ForexDashboard | Extracted classic pivot and order/position-book scoring functions behind an offline snapshot adapter |
| Integration code | Shared validated candle input, prefix replay, API, dashboard, corrected RSI, new chronological divergence detector, initial daily/weekly EMA bias |

The four original applications are not started together. Broker execution, original authentication/config files, executables, and unrelated application startup code are not included. Original ZIPs and extracted audit copies remain unchanged outside this deliverable.

## Use

- Default input is 10,000 deterministic synthetic hourly candles. It is clearly labelled **not market prices**. Pair selection changes its price scale, not a live market feed.
- EUR/USD, GBP/USD, and USD/JPY are supported. Choose 1h, 4h, or daily.
- Import completed minute/hour OHLC CSV data for the selected pair. It is persisted in local SQLite and can be reopened with Saved dataset. Pair changes and Reset demo do not delete imports. Verify the import summary and calendar before analysis.
- Move the replay slider to recalculate using only the selected prefix. The selected clock may be later than the last complete 4h/daily candle, because incomplete aggregates are excluded.
- Click backend evidence to focus and highlight its canonical geometry. Structure, supply/demand, BOS/CHoCH, S/R, FVG and order blocks have visibility controls; EMA20/50 is optional.
- Price and RSI share one native chart time scale, with corresponding divergence endpoints. See [P07 UI](docs/ANALYSIS_UI.md).
- Optional OANDA-format archive input activates the extracted ForexDashboard sentiment functions when timestamp evidence is eligible. It does not connect to an OANDA account or fetch live data.

## CSV input

UTF-8 CSV with one header row; quoted fields supported. Required columns are time, open, high, low, close; volume is optional:

```csv
time,open,high,low,close,volume
2025-01-02T00:00:00Z,1.0800,1.0810,1.0790,1.0805,100
2025-01-02T01:00:00Z,1.0805,1.0815,1.0795,1.0810,120
```

The two rows illustrate the schema only. Import up to 250,000 completed minute/hour candles (32 MiB). Analysis requires at least 60 complete target candles. Select the source calendar, base granularity, timezone for naive dates, and numeric timestamp unit. Timestamps identify candle opens; rows must be strictly increasing and unique with valid finite OHLC values.

See [historical storage, calendars, quality checks and API](docs/HISTORICAL_DATA.md). Missing or unfinished aggregates are excluded. NY 17:00 sessions follow DST; the synthetic demo uses UTC weekdays. Holidays and provider maintenance are not modeled. Local history is stored under `.data/`, excluded from the source ZIP.

## Optional book JSON

```json
{
  "instrument": "EUR_USD",
  "positionBook": {
    "time": "2025-08-05T15:00:00Z",
    "retrieved_at": "2025-08-05T15:01:00Z",
    "buckets": [
      {"price": "1.0570", "longCountPercent": "80", "shortCountPercent": "20"}
    ]
  },
  "orderBook": {
    "time": "2025-08-05T15:00:00Z",
    "retrieved_at": "2025-08-05T15:01:00Z",
    "price": "1.0570",
    "buckets": [
      {"price": "1.0570", "longCountPercent": "60", "shortCountPercent": "40"}
    ]
  }
}
```

This example is invented schema data, not a real OANDA observation. Either book is optional. The instrument must match; observation and explicit retrieval must both be no later than replay, and observation age must be at most 24 hours. Invalid/stale/future books are not converted into neutral sentiment. Position-book scoring is the upstream contrarian heuristic; order-book scoring is net orders within 50 pips. Scores are separate, not calibrated probabilities. Imported provenance is not independently verified.

## Verification

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

Current replay verification is recorded in [P10 acceptance](docs/P10_ACCEPTANCE.md); integrated analysis acceptance remains in [P09](docs/P09_ACCEPTANCE.md). Run `./verify.sh` for dependency consistency, the regression suite, TypeScript/Vite build and a temporary real HTTP startup/import/replay smoke test. Earlier phase reports retain their original test counts.

A bounded real Dukascopy EUR/USD bid H1 dataset passed import and H1/H4/D1 analysis. See [data provenance and reproduction](docs/REAL_DATA_P09.md). Start locally with `PORT=8766 ./start.sh`, select the saved Dukascopy dataset, then inspect canonical evidence. A fresh checkout requires reproducing the import; data is not bundled in the source ZIP.

## Deferred functionality and limits

- Minute replay/date selection, playback controls and forming candles are available in **Trade simulator · replay**. See [replay instructions](docs/REPLAY_CLOCK.md). Try EUR/USD at 2024-01-05 12:07 UTC.
- The [P11 paper-order engine/API](docs/PAPER_ORDERS.md) supports market/limit/stop entries and cancellation with a simulated fixed spread. Order controls are available in the Trade simulator workspace (P13).
- The [P12 USD account API](docs/PAPER_ACCOUNT.md) adds SL/TP, manual/partial closes, P&L, costs and margin checks. Financing and automatic liquidation are explicitly excluded.
- Trading controls, chart lines, positions, account summary and history are available in Trade simulator · replay. See [P13 acceptance](docs/P13_ACCEPTANCE.md). Use Save checkpoint to persist sessions and order-linked notes; resume and JSON export are available in the journal panel.
- Practice branches, blind prediction challenges and read-only summaries are available; see [P15 modes](docs/P15_ACCEPTANCE.md). Final simulator acceptance remains P16. See [P14 persistence](docs/P14_ACCEPTANCE.md).
- Live providers, news feeds, alerts, broad instrument coverage and broker execution are not implemented. Optional imported sentiment remains unavailable when absent, stale or future-dated.
- Snapshot structure/zones can revise; the separate P05 causal journal preserves historical availability. Do not treat plotted retrospective origins as tradable confirmation times.
- P08 daily/weekly bias uses explicit versioned research heuristics, not calibrated probabilities or validated trading performance. Fifty completed horizon bars and confirmed pivot evidence are required.
- Historical provider delivery latency, real tick paths, spread, slippage and holiday/maintenance calendars are not reconstructed by hourly candles.
- Source licensing/notice limitations in docs/PROVENANCE.md remain relevant before distribution beyond this local workspace. Full parity with every upstream screen/detector is not claimed.

See `docs/PROVENANCE.md` for source mapping and repair details and `docs/source-snapshots.json` for ZIP hashes.

Current UI verification: [P07 acceptance](docs/P07_ACCEPTANCE.md), 149 tests, production build and HTTP smoke passed; browser imports, evidence interaction and narrow layout checked. Earlier verification paragraphs describe their original checkpoints.

P08 replaces the EMA-only bias prototype with independent versioned daily/weekly scenarios. See [bias rules](docs/BIAS_RULES.md) and [P08 acceptance](docs/P08_ACCEPTANCE.md). Open Rules & evidence to inspect inputs and select horizon chart levels. Sentiment remains optional context with no technical vote.
