# P01 acceptance — reproducible baseline and source map

Date: 10 November 2026
Status: COMPLETE (P01-A and P01-B). Await user instruction before P02.

## Implemented

- Initialized a local-only Git repository. Pre-phase checkpoint: `ebe66a7`. No remote configured. P01 completion is identified by the `p01-complete` tag.
- Created `.venv` without system site packages. Recorded Python 3.14.3 and Node 22.21.1 in version files.
- Captured all 25 resolved Python packages in `requirements.lock.txt`; added the directly imported Pydantic package to the direct requirements.
- Added rerunnable `setup.sh`, `verify.sh` and a real-HTTP smoke script that chooses an unused loopback port and always shuts its server down.
- Fixed launcher behavior after interrupted dependency installation and when dependency inputs/frontend sources change. `PORT` can select another local port without disturbing existing previews.
- Mapped 18 imported source files and verified four extracted function/method bodies against supplied upstream copies. Recorded active calls, duplicate calculations, exclusions and unresolved licence-notice details.
- Updated setup instructions and phase handoff. Analysis algorithms and UI behavior were not changed in P01.

## Verification actually run

| Check | Outcome |
|---|---|
| Fresh virtual environment from direct pinned requirements | Installed successfully; system site packages disabled |
| Frontend clean `npm ci` from lockfile | Passed |
| `setup.sh` with captured dependency lock | Passed end to end; setup fingerprint written only after successful build |
| `verify.sh` | Passed end to end |
| Python dependency consistency | No broken requirements |
| Integration tests | 16 passed; no failures |
| TypeScript / Vite build | Passed; production output generated |
| Real HTTP smoke | Startup, health, index/assets and four-module POST analysis passed; temporary server stopped |
| Actual `PORT=0 ./start.sh` launcher | Started, health returned HTTP 200, then stopped cleanly |
| Source inventory | 18 mappings; unchanged copies match; four extracted ASTs match |
| Shell syntax / Git whitespace / setup fingerprint | Passed |

Verified environment: macOS x86_64; Python 3.14.3; Node 22.21.1; npm 10.9.4. Python lock snapshots versions on this environment; other platforms and Python versions were not tested.

## Findings and remaining limitations

- **Resolved baseline problem:** the earlier virtual environment inherited host packages. The project-local environment is isolated, and Python transitive versions are now recorded.
- **Resolved launcher problem:** an existing interpreter previously caused dependency installation to be skipped even after a partial setup. Setup now retries based on a completed-input fingerprint.
- **Non-blocking warning:** Starlette 1.10.0 warns that its TestClient's httpx path is deprecated. All test and live HTTP checks pass. This is recorded rather than suppressed or used to justify an unrelated dependency migration.
- STRUCT.ai and Scalper supplied only README MIT declarations, not standalone full licence files. Broader redistribution still requires notice/attribution follow-up; full dependency licence review is not complete.
- Duplicate EMA/ATR calculations, shadowed `pivot_idx`, historical-label revision, limited calendars, optional snapshot sentiment and EMA-only bias remain explicitly assigned to later phases. P01 does not claim to resolve them.
- No new browser visual QA, upstream full-suite run, live-provider check, simulator work or predictive-performance assessment was performed in this phase. The prior browser evidence remains dated 9 November.

## Next gate

P02-A defines canonical instrument/candle contracts. It has NOT started. Wait for the user's instruction to proceed.
