# P07 acceptance — unified analysis UI

Completed 13 November 2026. Packets P07-A and P07-B complete; P08 not started.

## Implemented

- Backend-owned S/R, structure/break, supply/demand, FVG and order-block geometry with canonical finding IDs; active client-side detection removed from the renderer.
- One native chart time scale for price and RSI; matching divergence endpoints and evidence, selected range focus, visibility controls and source/timing labels.
- Saved sentiment archive selector, small CSV/JSON paste alternatives, stale-response protection and responsive layout.

## Verification

- `./verify.sh`: dependency consistency, 149 tests passed (58.85 seconds; one existing Starlette TestClient deprecation warning), TypeScript/Vite build and real HTTP smoke passed.
- CSS stacking correction made after that run; production build passed again, then visible annotations and selection were verified in browser.
- Desktop: selected bullish divergence highlighted both price and RSI endpoints with identical x coordinates and matching canonical ID. Divergence toggle removed all RSI overlay groups. Daily timeframe cleared the selection/current results before recalculation.
- Daily FVG selection mapped to a backend region rectangle and selected ID; FVG toggle removed its rendered group. Fit history worked.
- Narrow layout: 390×844 viewport, document scroll width equalled client width (390); filters and Fit history usable. Temporary viewport reset during verification, then reapplied for the last narrow check before interruption.
- Imported synthetic 100-hour CSV through paste and native file chooser. Imported dated book JSON through paste, selected archive appeared and scored. Moving cutoff from 100 to 60 excluded books recorded after the replay clock.
- Browser console error inspection returned no errors at the import/replay checkpoint.
- Native JSON chooser and an order-block-bearing browser fixture were not separately tested. Generic backend zone mapping is covered by contract checks; no claim of exhaustive visual coverage.

Screenshots: `screenshots/p07-desktop.png` (selected divergence), `screenshots/p07-narrow.png` (narrow controls/layout). These are synthetic data, not market observations. The later daily FVG screenshot was inspected in-tool but not saved.

## Handoff

Read ANALYSIS_UI.md and DEVELOPMENT_STATUS.md. Full bias rules remain P08. Do not begin the simulator until P09 passes. The P07 temporary preview is stopped. Source archive excludes local test datasets and sentiment archives.
