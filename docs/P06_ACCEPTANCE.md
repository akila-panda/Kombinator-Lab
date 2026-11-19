# P06 acceptance — external sentiment normalization and source boundary

Completed 11 November 2026. P06-A and P06-B complete. **Stop before P07.**

## Delivered

- Normalized instrument aliases/UTC timestamps, explicit observation versus retrieval, validated percentages, unique bucket prices and optional bucket-width geometry.
- Immutable local imported-book archives, deterministic IDs, repeat-import idempotence, pagination and pinned archive selection on both analysis APIs.
- `SentimentProvider` interface, local `ArchiveProvider`, explicit `UnavailableProvider`, catalog and named per-book 24-hour application freshness policy.
- Per-kind historical selection excludes future/late-retrieved/stale/mismatched/missing-retrieval data; no fabricated source or neutral fallback. Available canonical sentiment requires retrieval-time evidence under contract 1.3.0.
- Selected ForexDashboard scoring bodies preserved. Imported source IDs/provenance retained; volatility and price-derived analysis remain separate from external positioning.
- Existing UI book import saves/pins a local archive and accepts one object or an array, with updated timestamp/provenance guidance. Full saved-archive browsing remains P07.

## Source availability

No OANDA/live market-data tool was available. No account, credentials or live downloads were used. The existing explicitly authorized imported-book capability is the connected local source; provider catalog reports live unavailable. This is the roadmap's unavailable-source fallback, not an unfinished live integration or a request for credentials. Supplied historical retrieval times remain user-asserted and unverified.

## Verification

`./verify.sh`: **147 tests passed**, dependency consistency passed, TypeScript/Vite production build passed, and real loopback HTTP checks passed including archive import, scoring at retrieval time and exclusion before retrieval. Full suite duration 29.87 seconds. Existing Starlette TestClient httpx deprecation remains. No dependency upgrade was made in response to npm's informational update notice.

17 new cases cover per-book clock selection/fallback, future and missing retrieval, exact age limits, source mismatch, persistence/idempotence, pinned history after new imports, malformed percentages/duplicates/overlapping widths/booleans/reverse timestamps/conflicting corrections, JPY normalization/pip scoring, zero mass and absent nearby orders, both analysis endpoints, source/evidence attribution and schema export. Existing lifecycle/adapter/calendar suites passed. Synthetic schema examples now include explicit retrieval times; preexisting sentiment fixtures were updated to satisfy the deliberate historical-availability tightening.

No new browser upload test was claimed: P03's extension file-URL permission limitation persists. Archive import/selection were verified by TestClient and real HTTP; the changed frontend built successfully. No persistent preview server was started; temporary smoke server stopped.

## Handoff

Contract 1.3.0; imported-book calculation p06-imported-books-v1; separate sentiment SQLite schema v1 in `.data/sentiment.sqlite3`. Existing history schema v2 and p05-causal-v1 event policy unchanged. Local data remains excluded from Git/source ZIP. Current operational details and examples: SENTIMENT_SOURCES.md.

Limitations: no live/provider-verified data, no claim of market-wide institutional positioning, and the 24-hour policy is an application rule rather than provider cadence. Browser file-selection completion remains unverified. No simulator work started.

Checkpoint `p06-complete`. Next **P07-A unified analysis UI**, only after explicit “Proceed”.
