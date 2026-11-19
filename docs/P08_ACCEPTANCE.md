# P08 acceptance — explainable daily/weekly bias

Completed 13 November 2026. P08-A and P08-B complete. P09 not started.

## Delivery

- BIAS_RULES.md specifies p08-bias-v1: completed horizon bars, strict confirmed pivot structure, canonical EMA/RSI momentum, prior 20-bar reference range, active wick/body zone context, conflicts, missing history and invalidation.
- backend/bias.py evaluates daily and weekly independently. No sentiment score is converted into a technical vote or probability.
- Canonical assessments and source-labelled aggregated OHLC evidence accompany each horizon. Level findings connect rule cards to chart selection and exact prices; selection includes the level in autoscaling.
- UI exposes version, last completed horizon time, component explanations, change conditions, evidence references, selectable prices and horizon disagreement. Bias levels default hidden.

## Verification

- Final full test suite: **156 passed**, 49.23 seconds; one pre-existing Starlette TestClient deprecation warning.
- Seven bias tests cover rising/falling scenarios, flat neutrality, insufficient history/pivots, opposing horizon fixtures, context conflicts, absent/available sentiment invariance, future-bar mutation/prefix determinism, canonical references, zone confirmation/invalidation and unconfirmed pivot exclusion.
- Dependency consistency passed. TypeScript/Vite production build passed after the selected-price autoscale correction.
- Real HTTP smoke passed for startup/assets, legacy analysis, CSV import, metadata/range retrieval, stored analysis, event journal and sentiment replay availability. Initial sandbox loopback bind was denied; the same smoke passed with local network permission.
- Browser: demo daily/weekly bearish explanations contained exact pivot/EMA/RSI/range values. Selecting Daily prior range high 1.06420 enabled bias levels and highlighted the matching canonical finding at visible y=88.3. Replay to 60 hours cleared prior results and showed daily unavailable (2 completed bars) and weekly unavailable (0). Browser error log was empty.
- Screenshot: screenshots/p08-bias.png. Synthetic data only. No new upload or narrow-layout regression test in P08; P07 covers those workflows.
- Contract examples regenerated; git diff whitespace check passed. Contract shape remains 1.4.0, with new values in existing assessment/finding categories and versioned raw bias details.

## Limits / handoff

Rules are explicit research heuristics, not validated predictive performance. Strict pivot requirements can leave monotonic history unavailable. Gaps can leave old completed horizon observations; evaluated_at and dataset quality must be considered. No live provider or simulator added. Read DEVELOPMENT_STATUS.md, then perform P09 integrated acceptance only after the user proceeds. Temporary preview stopped; local fixture archives excluded from source ZIP.
