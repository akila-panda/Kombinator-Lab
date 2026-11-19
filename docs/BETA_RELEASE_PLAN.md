# Staged beta release and trader feedback

18 November 2026. First useful beta: **after P16 acceptance and the pilot distribution gates below**, not after P46. A private, assisted local pilot is the shortest delivery path. This is not a public hosted launch.

## Release train

| Release | Earliest gate | What traders receive |
|---|---|---|
| Beta 0.1 — practice | P16 plus distribution/onboarding gates | Historical replay, paper market/limit/stop orders, protective exits, partial closes, account, existing analysis, checkpoints/journal, blind practice and review |
| Beta 0.2 — structure workspace | P20 and regression acceptance | Shared level map and evidence inspection |
| Beta 0.3 — first combo | P22 and regression acceptance | Sweep/shift/retracement workflow |
| Beta 0.4 — breakout | P24 and regression acceptance | Breakout/retest workflow |
| Beta 0.5 — momentum | P26 and regression acceptance | Momentum-at-structure workflow |
| Beta 0.6 — integrated analysis | P28 | All three workflows, setup-linked review and integrated release |
| Later releases | Completed P29–P46 capability gates | Evidence/realism/training improvements incrementally; do not wait for the entire roadmap |

Intermediate releases require complete backend/UI pairs and simulator regression. An unfinished phase is not shipped just to meet a date. No calendar deadline is promised without measuring remaining release work.

## Beta 0.1 audience and boundaries

Start with a proposed cohort of 3–5 retail traders on a verified platform, assisted onboarding, and a short structured trial. Expand only after setup/recovery issues are resolved. The current verified environment is macOS x86_64 with Python 3.14.3 and Node 22.21.1. Windows/Apple Silicon support is not established by a version check in setup.sh.

The known real minute fixture is EUR/USD BID, January 2–8 2024, 7,170 observed bars. This supports a functional pilot, not sustained skill training or performance claims. The source ZIP excludes data. Before unsupervised delivery, supply a permitted practice-data path: licensed distributable data or tester-owned CSV imported using documented settings. Broader multi-week practice coverage is a beta enhancement/data task, not a reason to wait for more indicators. 2022 replay is unavailable without suitable 2022 history.

No live orders, broker credentials, validated win probabilities, new combo indicators or hosted accounts. Existing chart snapshots can be retrospective; causal event evidence is separately labelled. Fixed spread/slippage, commissions, conservative ambiguous-bar policy, and omitted financing/automatic liquidation must remain visible. Short minute coverage cannot provide full daily/weekly warmup.

## Gates before handing a package to external testers

- P16 deterministic/error/restore/browser acceptance and supported-size measurements.
- Fresh extraction/install/start on the supported tester platform; someone follows the guide without developer knowledge. Current-environment verification is not a fresh-install test.
- Resolve incomplete upstream authorship/license notices documented in docs/PROVENANCE.md before redistribution. Do not assume a private beta removes this unresolved requirement. New Pine sources are not part of Beta 0.1.
- Confirm permitted delivery/access of the chosen market data. Existing local files are not automatically redistributable.
- One known practice example, visible limitations and feedback instructions.
- Pin release checksum/version and keep a dedicated beta data directory. No exposing the local API to the public internet as a shortcut to hosting.

## Protect beta users while developing

Keep released source/package immutable; continue development separately. Beta fixes should be narrowly scoped and regression-tested. Give testers release notes and a rollback package. Do not update their backend silently: the current calculation hash changes with backend Python source and older checkpoints may become review/export-only. Finish/export sessions before upgrades; keep the old release plus its data for resuming old sessions. Back up SQLite with the application stopped or a consistent SQLite backup method, not an arbitrary live file copy.

Feedback is triaged before each phase: data loss/accounting/causality defects block release; workflow blockers come next; repeated confusion informs the next UI phase; feature requests enter a separate backlog. No automatic additions to the active phase. Publish what changed in response to feedback.

## Lightweight feedback loop

Use a shared agreed collection channel or manually collected forms initially; no analytics service is necessary. No messages or uploads are sent automatically. Ask permission before collecting sessions/screenshots containing private notes.

Use [the feedback template](BETA_FEEDBACK_TEMPLATE.md). For each report record: release ID, OS/browser, dataset fingerprint and coverage (not necessarily the dataset), replay clock, task attempted, expected/observed behavior, reproducible steps, severity, optional redacted screenshot/export, and permission to use the attachment. Deduplicate reports; record owner, reproduction result, fix version and tester confirmation.

Trial tasks: start a replay, inspect evidence, enter/manage a simulated order, save/reload/resume, record a prediction, review the decision and report one confusing moment. Track setup success, task completion, time to first completed practice session, restore failures and misunderstanding of simulation limits. P&L and trade volume are not beta product-success metrics. Observe both beginners and experienced users; do not generalize from a tiny cohort.

## Current readiness

P16-A backend acceptance passed on 18 November. P16-B browser/release work is recorded in P16_ACCEPTANCE.md. External beta is not yet cleared: fresh-platform onboarding, source notices and practice-data delivery remain gates. Internal/local preview is usable now at port 8766 when running. Next development action remains the unfinished P16 work, not P17.
