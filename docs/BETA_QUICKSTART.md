# Beta 0.1 candidate — assisted local practice guide

18 November 2026. Internal release candidate, not yet cleared for external redistribution. See BETA_RELEASE_PLAN.md for open delivery gates. No real-money orders are sent.

For the full walkthrough, see [the retail trader testing guide](RETAIL_TRADER_TEST_GUIDE.md).

## Setup

Use the recorded macOS x86_64 / Python 3.14.3 / Node 22.21.1 environment. Other platforms need verification. Extract into a new directory; do not overwrite an older release or its .data directory. With the prerequisites installed, run `./setup.sh`, then `./verify.sh`, then `PORT=8766 ./start.sh`. Open http://127.0.0.1:8766/. Use another unused local port if necessary. Never terminate an unidentified process.

The archive contains no user database, journal or market data. Import your permitted completed-minute OHLC CSV through Analysis → Import historical CSV, select the symbol/calendar/timezone/timestamp units accurately, and check coverage/gaps. The default synthetic hourly analysis demo is not a minute trading dataset. Do not call synthetic prices real history.

## Known example on the developer's existing real dataset

1. Open Trade simulator · replay, select Practice and the Dukascopy EUR/USD BID M1 dataset for Jan 2–8 2024.
2. Set start to `2024-01-05T12:07` UTC. Keep the default USD 10,000 account and stated costs. Select Go to date.
3. Inspect the 15m/1h charts and completed-hour analysis. Analysis is available through 12:00; forming bars are excluded.
4. Submit a 1,000-unit paper market buy, then Next minute. Expected entry is 1.09188 at 12:08, balance 9999.96 after entry commission, and 1,000 units open. These values depend on the exact dataset/profile.
5. Name and Save checkpoint. Reload, reopen simulator, select that checkpoint and Resume. The same position/account/clock should return without another fill.
6. Pause to manage the position; close commands execute on a later observed minute. Save again after decisions.
7. Use New session before Review checkpoint or creating a Practice branch. Old checkpoints remain unchanged. Blind challenge requires a recorded prediction before analysis is revealed.

This local dataset is not included in the candidate archive. A different dataset needs its own example expectations. Dates outside coverage are rejected. For reports, include release ID, dataset fingerprint, clock, steps and expected/actual behavior. Redact personal journal text before sharing.

## Limits and update policy

This is minute-close replay, not reconstructed ticks. Fixed spread/slippage are assumptions. Financing and automatic margin liquidation are excluded. Both stop and target within a bar can be ambiguous. No trading-edge claims apply. The short minute sample cannot warm up 50 daily/weekly candles. Unsaved changes are lost on reload.

Keep releases and data directories separate. Backend calculation changes can prevent resuming older checkpoints; old evidence remains reviewable/exportable. Keep the old version to continue old practice. No automatic migration or cloud sync is provided.
