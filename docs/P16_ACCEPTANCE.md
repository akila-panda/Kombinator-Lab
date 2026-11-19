# P16 simulator acceptance — beta candidate

18 November 2026. **P16-A complete; P16-B partial. P16 is not complete and external beta distribution is not cleared.**

## Checks actually run

- `./verify.sh`: dependency consistency passed; 222 pytest tests passed in 54.82s; TypeScript/Vite production build passed. One upstream FastAPI/TestClient deprecation warning. Its final HTTP smoke initially failed because sandbox socket binding was denied, not an application assertion.
- `.venv/bin/python scripts/smoke_server.py` rerun with local socket permission: passed startup/assets, analysis, CSV/dataset/event/sentiment APIs and paper order/account HTTP checks.
- `.venv/bin/python scripts/accept_simulator_beta.py`: passed on a temporary store using the hash-verified 7,170-bar real minute CSV. Covers deterministic replay, causal evidence, weekend, end of data, out-of-coverage date, partial/full closes, fresh-store restore, unchanged branch parent and read-only review. No user's existing sessions modified by this script.
- Existing tests exercised stop/limit/market triggers, ambiguous stop-first exits, gap handling, margin rejection, future-data mutation, missing data, forming bars and training compatibility.
- Chrome browser: selected real minute data; started 2024-01-05 12:07 UTC; submitted 1,000-unit paper buy; stepped to 12:08; observed entry 1.09188, balance 9999.96, equity 9999.76, commission 0.04; saved `P16 beta acceptance 2026-11-18`; reloaded and resumed; same clock, position, account and single fill restored. Test checkpoint ID 454d58f3dedd4400a2c5eafcc48fc32f remains in local data, not the candidate archive.

Performance evidence: simulator-beta-p16.json records twelve direct `replay_state` timings on macOS 15.7.9 x86_64 / Python 3.14.3. Median 198.88ms; cold/max 605.05ms. This is a small sequential functional fixture, not HTTP p95, browser performance, concurrency, or the 250,000-row import ceiling. No broader size/scale claim.

## Release work prepared

BETA_RELEASE_PLAN.md defines the earliest beta and incremental delivery gates plus feedback triage. BETA_QUICKSTART.md provides an exact example and isolated-version update policy. README stale roadmap/order-UI statements corrected. DEVELOPMENT_PLAN.md v3.1 now distinguishes beta delivery from the long-term roadmap. Backend/frontend application behavior unchanged, so these documentation/script additions do not invalidate calculation hashes.

## Open P16-B / external pilot gates

1. Complete current-release browser coverage beyond the market/save/resume flow (all supported ticket paths, blind prediction/review/branch, error states and narrow layout). Prior P13/P15 checks are historical evidence, not all rerun today.
2. Validate fresh-extraction setup and data import on a declared tester platform. Fresh temporary extraction setup passed on this same Intel Mac: new isolated Python environment, pinned dependencies, npm ci and production build. Independent tester onboarding and other platforms have not been verified. Do not claim Windows or Apple Silicon support without a run.
3. Resolve incomplete STRUCT.ai and scalper source notices identified in PROVENANCE.md before external redistribution; a README MIT declaration is recorded but full notice resolution remains outstanding. No legal clearance claimed.
4. Establish permitted practice-data delivery. Current source archive excludes data; Jan 2–8 minute coverage is short and lacks higher-horizon warmup. Expanded coverage is a separate beta data task, not a prerequisite for internal functional tests.

The next Proceed resumes these gates in P16-B, not P17. Only mark P16 complete once its release checklist passes; external-distribution blockers stay visible even if internal acceptance succeeds.

## Preview

The previously recorded server was not running. Restarted local-only 127.0.0.1:8766, PID 55411 / execution session 71363, and verified browser operation. Left running. No unrelated processes stopped; no public hosting enabled.

Upstream source-page recheck (18 November): [STRUCT.ai](https://github.com/Kiyolegend/Sturct-ai) and [scalper](https://github.com/ayia/forex-scalper-agent-v2) still expose README MIT declarations in the checked pages; that did not resolve the recorded missing full notices for the supplied snapshots. No upstream content was executed.

Clean-extraction setup: `setup.sh` completed successfully in a new temporary directory using the existing Python 3.14.3 interpreter to create a new isolated venv. npm installed 73 packages; production bundle rebuilt (2.51s). Shell execute bits were restored after Python ZIP extraction. This verifies dependency installation on the current platform, not installation of Python/Node prerequisites by a nontechnical user.
