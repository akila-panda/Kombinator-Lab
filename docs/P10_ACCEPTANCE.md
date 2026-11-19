# P10 acceptance — minute replay clock

P10-A/B complete, 13 November 2026. P11 has not started.

- Imported 7,170 real EUR/USD BID minute bars, January 2–8 2024; 30 scheduled gaps retained. Exact bytes/URLs and quality in minute-data-p10.json.
- Added pair/dataset/UTC date selection, play/pause, maximum speed, minute and candle steps, terminal state and explicit empty/closed/gap states.
- Shared 15m/hourly panes build forming candles only from revealed minutes. Completed-only analysis requires 60 full hours. No invented tick path or paper fills.
- Six replay tests cover pause/repeatability, boundaries, outside coverage, end, future-price mutation, incomplete candles, missing-minute and weekend jumps, and API validation. Existing decoder tests also pass.
- Full `./verify.sh`: dependency consistency, **169 tests passed in 61.03 seconds**, TypeScript/Vite build and real HTTP smoke passed. One existing Starlette TestClient deprecation warning. After fixing browser date entry, the frontend build passed again; backend remained unchanged.
- Browser: 2022 date explicitly rejected; 2024-01-05 12:07 showed 73 complete hours, both forming bars with 7/7 minutes, and analysis through 12:00. Next minute moved to 12:08; next 15m candle to 12:15. Playback advanced to 12:24; pause held that clock across subsequent checks.
- Browser: Saturday January 6 noon displayed closed market; next minute jumped to Sunday January 7 22:05 (the next observed close). January 9 00:00 disabled play/step. GBP/USD showed no history and cleared stale charts. No console errors observed. At 620px viewport there was no horizontal overflow. Screenshot: screenshots/p10-replay.png.

Preview server on port 8766 intentionally remains running at the user's request. Source package excludes datasets and environments. Data semantics/reproduction/API are documented in REPLAY_CLOCK.md. No claim of 2022 coverage, tick fidelity or trading performance. Next phase: P11, only after explicit Proceed.
