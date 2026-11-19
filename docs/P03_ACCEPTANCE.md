# P03 acceptance — historical data store and timeframe service

Completed 10 November 2026. P03-A and P03-B complete; **stop before P04**.

## Delivered

- Immutable SQLite datasets with metadata/provenance, normalized and raw fingerprints, idempotent imports and atomic writes; storage version 1.
- Validated minute/hour CSV import with bounded size, duplicate/order/OHLC checks, timezone normalization and DST ambiguity rejection.
- Paginated base/aggregate range APIs, replay clock exclusion, separate warmup and explicit insufficient-history reporting.
- Explicit continuous UTC, synthetic UTC-weekday and NY 17:00 calendars; missing input is distinguished from scheduled closures. Incomplete/missing aggregates never appear as completed candles.
- Dataset-ID analysis and saved-dataset UI with import settings/summary. The four-module hourly preview uses the new service. Legacy array API remains available.
- Contract 1.1.0 and regenerated schemas/examples, including dataset analysis requests. No new dependencies.

## Verification

`./verify.sh` passed dependency consistency, 91 tests, TypeScript/Vite production build, and real loopback HTTP startup/assets/legacy analysis/CSV import/metadata/range/dataset analysis checks. Three additional calendar/volume cases were subsequently added; final full suite: **94 passed**. These additions did not change implementation or build output.

Coverage includes deterministic minute→hour OHLCV; missing/unfinished groups; NY daily and 4h UTC shifts; Friday-close weekly bars; spring/fall 47/49-hour closures; naive DST ambiguity; malformed/duplicate/out-of-order inputs; provenance/idempotence; persistence after database reopen; failed-import atomicity; query pagination/clock/warmup; minute-fed analysis; and NY 1h/4h/daily canonical envelopes. Existing prefix-causality regressions pass. This is controlled-fixture coverage, not validation against a real broker dataset or full-size performance certification.

Chrome UI: stored 10,000-row synthetic demo and metadata rendered; hourly and daily charts rendered; import controls inspected; replay changed from 10,000 to 9,999 and clock changed to 2025-08-05 15:00 UTC. No browser console errors were reported in the final check. Screenshot: `../p03-dataset-preview.png` in the outer outputs directory.

**Browser upload limitation:** file chooser automation was blocked by the Chrome extension's disabled “Allow access to file URLs” permission. Permission was not changed. Browser file selection/import completion is unverified; raw CSV import was exercised through TestClient and real HTTP. This is a UI test limitation, not a known API import failure.

Retained environment warning: Starlette TestClient's httpx deprecation. No suppression or dependency changes.

## Handoff

- Schema 1.1.0; SQLite user_version 1; calendar IDs and API documented in HISTORICAL_DATA.md.
- Persisted local EUR/USD synthetic dataset ID: `17f19f973566610e53a16bebcd327e2ee00eb6f63e7398d2d1baa93eb407ea1b` (10,000 bars, no missing scheduled slots, 3,984 closed hourly slots). Local DB is excluded from source delivery; reset demo recreates it deterministically.
- No real historical prices acquired; selecting a 2022 date is not yet supported without importing that coverage and completing simulator phases.
- Holiday/maintenance calendars, revised/provisional finding lifecycle, actual provider latency, canonical module consolidation, full bias, and simulator remain later phases.
- Temporary P03 preview on 8766 and HTTP smoke server stopped. Earlier 8765 process untouched.
- Next: P04-A, only after explicit user “Proceed”. Checkpoint tag: `p03-complete`.
