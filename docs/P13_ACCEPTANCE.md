# P13 trading workspace acceptance

P13-A/B complete, 16 November 2026. P14 not started.

Replay.tsx now atomically publishes chart and account snapshots at one clock. TradePanel.tsx adds market/limit/stop tickets, SL/TP, pending cancellation, positions, manual/partial closes, account values, rejection reasons and chronological event history. Native chart lines show pending triggers, entry, SL and TP. Simulation label and cost exclusions remain visible. Session settings lock at start; explicit New session confirmation resets history. Analysis navigation pauses and retains the session. Page reload loses the session (P14 persistence remains deferred).

Verification: ./verify.sh passed 220 tests in 35.64s, dependency consistency, TypeScript/Vite build and HTTP smoke. Final reset/overlay CSS adjustments were built successfully afterwards. Backend unchanged. Browser verified dated real history, pending limit cancellation, next-minute market entry, 400/600 partial/full close, stop-loss exit, margin rejection, synchronized pause, retention across Analysis navigation, reset keep/discard and chart entry line. A native confirmation was replaced with in-page confirmation; final discard verified by keyboard. Sticky label pointer interception was fixed with pointer-events:none and rebuilt; the final pointer-specific CSS change was not separately browser retested. No console errors in final browser check. Screenshot: screenshots/p13-trading.png.

Observed real scenario: buy 1000 at 1.09188; partial close 400 at 1.09167 and remaining 600 at 1.09164; resulting balance 9999.71. Subsequent stop exit reduced balance to 9999.53. Oversized entry rejected for margin without charges. Paused chart/account clock both stayed at 2024-01-05 12:13 UTC.

Preview restored on port 8766 with current APIs and left running (tool session 75834). No new dependencies. At most 200 commands per unsaved session. Financing/automatic liquidation excluded. Data coverage remains Jan 2–8 2024. Next: P14 save/resume and journal only after explicit Proceed.
