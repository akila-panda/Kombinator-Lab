# P02 acceptance — canonical contracts and instrument rules

Date: 10 November 2026
Status: COMPLETE (P02-A and P02-B). Wait for user instruction before P03.

## Implemented

- `backend/contracts.py`: version 1.0.0 instrument, source, candle, snapshot, evidence, finding, overlay, assessment and sentiment models; explicit units, states and cross-reference validation.
- Three-symbol instrument registry with Decimal pip/tick metadata and declared local-default provenance.
- Minute through weekly candle schema, completed/forming states, UTC boundaries, source and volume metadata. The actual analyzer remains completed-hourly only.
- `backend/requests.py`: strict input boundary preserving the documented UI shape; rejects mismatched symbol/timeframe, invalid numeric/time inputs, malformed imported books and claimed verified upload provenance.
- `backend/contract_adapter.py`: actual outputs from all four systems validated into an additive `contract` envelope; missing timing is explicitly provisional. Underlying application functions are not wholesale migrated in this phase.
- Evidence/overlay links, timing and lifecycle checks; versioned module assessments; unavailable/insufficient-history states cannot carry invented neutral scores.
- Imported book retrieval-time availability when supplied, without claiming unknown historical delivery time is verified.
- `GET /api/contracts`, generated JSON schemas and validated synthetic examples. UI requests now declare demo/upload provenance; legacy display fields are preserved.
- Contract and migration documentation identifying P03/P04/P05/P06/P07 responsibilities.

## Verification run

`./verify.sh` passed end to end in the P01 isolated environment:

- **66 Python tests passed**, including the 16 prior integration cases and 50 new contract cases.
- Python dependency consistency passed.
- TypeScript check and Vite production build passed.
- Real local HTTP server startup, health, frontend assets and four-module analysis passed; temporary server shut down.
- Schema exports match model definitions; synthetic examples validate, including available imported book outputs.
- Git whitespace check passed before checkpointing.

Coverage includes minute/forming schema validation, instrument rules, invalid OHLC/NaN/infinity, timestamp precision/alignment, reference integrity, symbol/context mismatch, future evidence, premature confirmation, lifecycle rules, overlay geometry, unavailable-state semantics, book percentages/timezones/retrieval timing, metadata trust, numeric fingerprint equivalence, API compatibility and distinction between input errors (422) and invalid adapter output (500).

## Explicit limits / decisions

- Metadata defaults are not verified broker specifications. Prices are preserved, not silently rounded to tick size.
- Fixed UTC calendar semantics are declared; session/DST correctness is P03 work.
- Unknown volume is represented as null/unknown in the canonical envelope. Existing numeric legacy calculations are unchanged.
- Current snapshot IDs fingerprint consumed inputs only; finding IDs are snapshot-scoped. Durable cross-snapshot lifecycle identities and historical revisions are P05 work.
- Provisional structure/zone findings have no invented confirmation time. Divergence retains its detector confirmation timestamp but is not an immutable event history.
- No storage, minute feed, simulator, full bias engine or live provider was added.
- Input tightening is documented: unknown fields and timezone-naive books now fail explicitly. The supplied book format is a supported subset, not arbitrary provider JSON.
- New browser visual checks were not run: layout is unchanged, with the only frontend source change adding provenance to API requests. TypeScript/build and HTTP/API compatibility were verified.
- Existing non-failing Starlette TestClient/httpx deprecation warning remains. Licence-notice follow-up remains as documented in P01.

## Handoff

Completion checkpoint: local Git tag `p02-complete`.
Next phase: P03, historical data store and timeframe service. It has NOT started. First inspect the canonical contracts and current `frame`/`aggregate` path, then implement P03-A only after user authorization.
