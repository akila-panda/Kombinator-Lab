# Product advancement roadmap

Version 1.0 · 17 November 2026 · P29–P46 all NOT STARTED.

## Authority and sequence

Extends [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) v3.0. It does not replace P16–P28 or start development. The next development action remains P16-A. [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) is the single live handoff record.

Basis: [post-completion research](POST_COMPLETION_PRODUCT_RESEARCH.md) and the subsequent honest design review. Research considered a hypothetical completed system; actual completion is not implied. No numeric design rating is proof of quality or profitability.

Default sequence: P28 → P29 through P46 in order. Additional prerequisites are identified below. When an external prerequisite is unavailable, record the blocker or explicitly agree a revised order; do not fabricate data or silently mark the phase complete. Relevant E packets may be scheduled separately when required. E06 must be complete before P33, or its equivalent existing ledger must be verified and recorded without implementing it twice.

One Proceed authorizes one phase. Reserve verification/handoff time and split a phase into named packets if necessary. Each phase ends with an acceptance artifact, exact next action and a pause. No phase is guaranteed to fit a fixed session length.

## Shared implementation boundaries

- Extend canonical data, setup, account, journal and replay contracts; do not create competing engines or clocks.
- New records carry dataset/provider identity, event and availability time, rule/model version and observed-versus-assumed status where applicable.
- Preserve old sessions and original evidence. Schema changes need explicit compatibility decisions and restore/export fixtures; no silent recalculation of old results.
- Keep the existing selected-chart-first journey. Secondary research/stress results belong in an expandable drawer or Review workspace.
- Default empty and unsupported states must be honest. Missing bid/ask, financing, timestamps, coverage or outcomes cannot be replaced with invented certainty.
- Backend gates use meaningful causal/accounting fixtures. UI gates include browser checks, keyboard/focus behavior, narrow layout, stale-response handling and production build.
- Tests on short fixtures establish functionality, not financial edge. Record measured limits and uncertainty; do not claim successful prospective evaluation before observation actually matures.

## Data and realism

### P29 — Dataset capability contracts

Deliver provider/instrument/price-basis, granularity, sampling, timezone/session convention, completeness, revision and permitted-use metadata. Derive supported operations from actual coverage; distinguish observed bid/ask from synthetic spread. Reuse existing provenance fields.

Gate: unsupported tick/intrabar or volume-dependent analysis is blocked or explicitly marked unsupported; import and restore preserve capabilities; tests distinguish missing data from unavailable capability. No second provider purchase is required merely to define contracts.

Boundary: no feed migration or wholesale historical download. Handoff the exact source requirements for P30/P31.

### P30 — Cross-feed comparison and suitability UI

Deliver a compact suitability label and optional setup comparison across overlapping licensed feeds. Normalize conventions before comparing; preserve source candles rather than averaging them. Show changed detection/confirmation times and coverage.

Gate: known differences reproduce; no-data/single-feed states work; at least one real overlapping-source example is required before claiming cross-feed validation. Synthetic fixtures only prove comparison logic. Source access/rights are a prerequisite for the real example.

### P31 — Execution profiles and stress calculation

Deliver versioned profiles on the existing simulator: observed spread where available, explicit hypothetical cost/delay scenarios, gap policy and effective-dated financing where sourced. Separate execution model from scenario inputs. Begin with one defined instrument/profile; split additional models into later packets.

Gate: side-correct fills, account-currency conversions, overnight boundaries, deterministic seeds where used, original baseline parity and unchanged saved sessions. Unknown intrabar order remains ambiguous. Unsupported partial fills/queue priority remain out of scope. Historical rates cannot be replaced by today's rates without an explicit hypothetical label.

### P32 — Execution stress comparison UI

Deliver baseline/observed-cost/adverse-scenario comparisons in Review with changed-trade explanations and assumption visibility.

Gate: identical frozen decisions across scenarios, reproducible results, no overwrite of original account and clear observed/assumed distinctions. A favorable scenario must not hide adverse or ambiguous results.

## Research evidence and prospective observation

### P33 — Evidence evaluation contracts

Prerequisite: E06 ledger or verified equivalent and appropriate data for any empirical claims.

Deliver a dossier per setup version: frozen rules, baseline, one-filter-at-a-time comparisons, coverage, opportunity counts, cost sensitivity, parameter stability and chronological evaluation splits. Account for overlapping events and preserve failed trials.

Gate: reproducible fixtures and experiment lineage; final evaluation is not reused as tuning data. Insufficient evidence is a valid result. Multiple-testing diagnostics require stated assumptions; correlated features cannot be treated as independent votes. This phase builds evaluation capability, not a guaranteed profitable strategy.

### P34 — Dossier UI and promotion policy

Deliver evidence status in the existing drawer: experimental, evaluated for stated conditions, prospective observation, restricted or retired. Promotion requires a predeclared evidence policy and deliberate review; changed rules create a new version.

Gate: sample/coverage limitations visible, unsupported probabilities suppressed, failed comparisons retained, old setup evidence reviewable. No automatic promotion because a backtest is positive; no universal win-probability badge.

### P35 — Prospective capture backend

Deliver read-only incoming-data observation with frozen setup versions, all eligible candidates, ingestion/detection/alert times and explicit hypothetical execution policy. Reuse scanner and event records. A suitable feed and usage rights are prerequisites; E04 is required only if measured workload needs it.

Gate: captured-input replay reproduces decisions, reconnect/duplicate/stale data cases handled, original evidence immutable, missing intervals visible, no broker orders. Test with captured fixtures before controlled real observation.

### P36 — Prospective monitoring and outcome review

Deliver clear observation mode and mature-outcome reports against the historical evaluation. Separate data shifts, execution-assumption changes and setup outcomes; record alerts without auto-retuning.

Gate: unfinished outcomes excluded from completed-outcome claims; every qualifying candidate accounted for; results labelled hypothetical. Functional acceptance can finish without a long observation history, but empirical validation remains pending until predeclared coverage criteria are met. Never shorten the observation gate merely to finish a session.

## Controlled planning and learning

### P37 — Portfolio scenario calculations

Extend current exposure analysis to compare selected plans, positions and pending orders under one account budget. Include gross/net currency legs, conversion and explicit shocks; no fabricated joint probabilities.

Gate: shared currency and offsetting-position fixtures, pending-order combinations, gross versus net risk and account totals agree with canonical accounting. Stop-based planned risk is not labelled a guaranteed loss ceiling. Shocks are scenarios, not forecasts.

### P38 — Portfolio comparison UI

Deliver before/after risk in Plan, an optional currency-leg diagram and alternatives such as selecting one candidate, reducing size or waiting. Respect declared user limits before any optional outcome ranking.

Gate: trader can identify shared exposure and assumptions; alternatives never mutate orders automatically. Keep chart and existing bracket as the primary planning interface.

### P39 — Versioned personal playbooks

Deliver explicit context, entry, invalidation, sizing and management rules linked to existing plans and journal. Distinguish manual checks from executable conditions. Reuse setup IDs and freeze versions at decision time.

Gate: old decisions retain original rules, incomplete playbooks cannot masquerade as executable strategies, edits are versioned, no natural-language instruction silently becomes code. Scope is structured configuration, not a general strategy programming language.

### P40 — Playbook workflow UI

Deliver create/review/select playbook flow with concise criteria and manual confirmations where needed. Optional personal limits must be explicit; avoid repeated confirmation for ordinary actions.

Gate: playbook matches recorded decision evidence, clear unmet conditions, deliberate skip path, restore/export parity and usable narrow-screen flow. No duplicate journal or planning workspace.

### P41 — Practice curriculum backend

Deliver short exercises from recurring decision errors, including failed setups and no-trade cases. Separate train/assessment cases by time and related-event group; retain original blind-mode safeguards.

Gate: unseen cases cannot leak future outcomes or teacher labels, sampling is not limited to winners, rule adherence and P&L are separate, reproducible exercise assignment and result records. Do not infer live skill from practice results.

### P42 — Targeted practice UI

Deliver a focused exercise, decision capture and post-decision explanation. Optional cooling-off/user limits support deliberate practice; do not reward trading volume, profit streaks or leaderboard position.

Gate: blind/review behavior, accessibility and clear feedback; evaluate on unseen cases. Functional acceptance and evidence of learning improvement are recorded separately. Lack of participant data means learning efficacy remains unverified.

### P43 — Attribution and controlled alternatives backend

Deliver decomposition of selection, timing, sizing, management and execution costs using frozen plans. Compare a small set of predeclared alternative policies through existing practice branches. Calculate adverse/favorable excursion with price-basis and ambiguity rules across relevant trades, not only winners.

Gate: unchanged original account, identical input/cost policy, reproducible alternatives, no hindsight-best-exit search and no unsupported causal blame. Mark interactions/residuals rather than forcing every difference into a supposedly independent cause.

### P44 — Decision review UI

Deliver aligned plan/actual/alternative timelines with one actionable observation at a time and access to exact evidence.

Gate: original and hypothetical paths distinguishable, no future advice shown during blind practice, cost/ambiguity context visible and no overlapping trades counted twice. Integrate with the existing journal.

## Product and release gates

### P45 — User evaluation and simplification

Deliver representative-user tasks on unfamiliar scenarios comparing the enhanced interface with the prior workflow. Measure identification of invalidation, missing triggers, evidence age, material conflicts, task completion and unnecessary interruptions. Use balanced task order and report sample limitations.

Gate: record observed results and resulting simplifications. Check keyboard/focus, non-color-only meaning and narrow-screen usability using WCAG 2.2 as a reference. Trade count and engagement time are not success metrics. Hide/remove additions that increase critical errors. If users are unavailable, mark user validation pending; an internal review is not a substitute.

### P46 — Integrated acceptance and release

Deliver end-to-end regression, version/restore/export evidence, operational measurements and a reproducible release with declared supported data/profile limits.

Gate: no future-data, accounting, preservation or recovery blocker; baseline comparisons pass; UI evidence agrees with underlying records; prospective/learning/profitability claims match actual evidence. Include failure cases and unsupported modes. A release may explicitly label experimental modules, but cannot claim a failed or unperformed gate passed.

Maintain local deployment scope. A cloud/commercial launch requires the separate security/distribution work below. Keep server availability and user data intact, then stop and wait.

## Conditional tracks — not hidden P29–P46 requirements

| Track | Bounded next step if selected | Required gate |
|---|---|---|
| Macro and positioning | Extend existing event layer with one vintage-aware source before adding more | Publication-time causality, historic revisions, genuine archived consensus for surprises; COT labelled delayed futures context, not spot order flow |
| Real-trade import | One read-only statement format, followed by reconciliation UI | Units/timezones/fees/financing/partial fills reconciled; secrets protected; imported execution distinguished from simulation |
| Coach collaboration | Redacted immutable case export first; shared access only if required | Explicit sharing, access control, comments tied to evidence, export/deletion behavior; no default public performance rankings |
| AI explanation | Grounded explanations of existing frozen records | Evidence citations and fabricated-number tests; no rule mutation or invented data; core product fully usable without AI |
| Shared/cloud distribution | Separate threat model and deployment design before hosting | Authentication, per-user authorization/isolation, credential handling, backup/restore, update integrity, privacy/retention and operational ownership tested; security review before exposing private data |

The macro and probability modules remain constrained by data and evidence. Add no new model merely to improve a subjective rating. Each conditional track needs its own small backend/UI/acceptance phases when selected.

## Handoff

For each phase record: objective, exact delivered behavior, changed files, actual checks, open gates/external dependencies, schema/calculation compatibility, server state, and first action on next Proceed. Cite its Pxx_ACCEPTANCE.md. Keep functional completion distinct from empirical evidence still being collected.
