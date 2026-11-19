# Beyond the completed roadmap: product research

17 November 2026. Assumption for this assessment: all capabilities in DEVELOPMENT_PLAN.md, including proposed engineering and discovery extensions, work as specified. This is a hypothetical gap analysis, not a statement that development is complete. No implementation phases or dependencies are authorized by this report.

## Assessment

A complete roadmap provides a capable analysis/replay product. It does not establish profitable rules, realistic fills under every feed, or improved trader decisions. The next investment should connect evidence quality, execution realism and measured learning. “10/10” is a product ambition, not a defensible accuracy or return score.

Research covered official broker/data documentation, central-bank market research, statistical research, competing product documentation, accessibility standards and experimental evidence about trading-app design. Competitor claims describe offered features, not independently measured effectiveness. No product accounts were purchased, competitors benchmarked, vendor feeds acquired or strategy performance tested.

## What is already assumed complete

Do not propose these again as new modules: three combo workflows and shared level map; visual journey; scanner/watch/alerts; regime, freshness, room and cost context; currency strength/exposure; analogs and evaluated outcome estimates; journal/training; replay; bounded processing; provenance/recovery; experiment ledger and conditional analytical storage.

## Priority 1: trust the evidence and the simulation

### 1. Dataset suitability and cross-feed sensitivity

**New increment:** a dataset capability contract plus a test showing whether a setup survives a change of feed or candle convention. This extends ordinary missing-data checks.

Store provider, instrument definition, bid/ask/mid basis, observed versus synthesized prices, timestamp precision, sampling, session cut, timezone, completeness, revision and permitted use. Derive explicit capabilities: minute-pattern analysis, bid/ask simulation, intrabar reconstruction or unsupported. Never infer tick completeness from the word live.

Where two licensed sources overlap, compare the same versioned setup on each, normalizing time conventions first. Display differing confirmations and trigger times rather than averaging feeds into invented candles. Distinguish provider differences from data errors. Report coverage limits when only one feed exists.

**UI:** compact “Data suitable for…” label and an expandable comparison; price discrepancies drawn only on request.

**Gate:** deterministic differences with known timestamp/price-basis fixtures; unsupported simulation modes cannot silently run. No universal agreement threshold: evaluate sensitivity relative to the setup's actual price distances.

**Evidence:** BIS describes fragmented FX execution [S1]. OANDA documents separate bid/ask/mid candles and defines its volume field as a count of created prices [S2]. Its pricing stream sends at most four updates per second per instrument, not every generated price [S3]. These are provider-specific facts, not claims about all vendors.

### 2. Execution realism and stress laboratory

**New increment:** compare the same frozen decisions under multiple execution assumptions. Existing fixed spread/slippage and cost checks are the baseline, not another implementation.

Add observed historical bid/ask when available; versioned broker/instrument profiles; financing with effective-dated rates; order timing and gap behavior; and explicitly hypothetical stress scenarios for wider spreads, delay and worse fills. Do not invent historical financing or queue priority. Minute OHLC cannot establish the order of both stop and target touches: retain ambiguity and show policy sensitivity.

**UI:** one outcome comparison in Review: baseline, observed-cost replay where supported, and adverse scenarios. Show which trades changed and why, not just an equity curve.

**Gate:** side-correct fills, account conversion, gaps, overnight boundaries and accounting parity; seeded stochastic scenarios reproducible. “Observed” and “assumed” must remain distinguishable. Partial-fill models require relevant data; quote update counts are not available traded size.

**Evidence:** QuantConnect separates fill models (price/quantity, spread) from slippage [S4]. Borrow the separation, not its engine or an uncalibrated market-impact model.

### 3. Setup evidence dossier and promotion policy

**New increment:** make research evidence control which setup versions are recommended. An experiment ledger stores trials; this adds decision rules for promoting, restricting and retiring them.

Each setup version gets a compact dossier: fixed definition, data coverage, baseline, incremental contribution of each filter, held-out results, cost sensitivity, parameter stability and conditions where evidence is weak. Compare a base setup against one added condition at a time. Record reduced opportunity count and uncertainty, not only improved win rate. Cluster overlapping opportunities so indicator variants are not treated as independent observations.

States: experimental → evaluated for specified conditions → prospective observation → restricted/retired. None means guaranteed profitable. Changes create new versions; do not rewrite old results or repeatedly reuse the final evaluation set.

**UI:** evidence tab attached to the existing setup drawer; normal trading view shows only evidence status and material limitations.

**Gate:** preregister comparison/outcome definitions, preserve all trials, test on untouched chronological data, require adequate coverage for the stated scope. Deflated Sharpe or other multiple-testing diagnostics belong in research when their assumptions fit, not in a universal quality badge. Correlated features complicate naive importance rankings.

**Evidence:** Bailey/López de Prado explain how selection across many trials inflates apparent performance [S5]. Scikit-learn demonstrates that correlated features can obscure permutation importance [S6]. These support cautious evaluation, not a claim that our combinations work.

### 4. Prospective observation mode

**New increment:** freeze a setup version and record new opportunities before their outcomes occur, without sending broker orders. Historical replay alone cannot provide this operational evidence.

Save every eligible candidate, including ignored/expired ones, with source health, evidence known then, alert-delivery time and hypothetical fill assumptions. Compare the prospective distribution with the historical evaluation; distinguish data drift, changed costs and changed setup outcomes. Require mature outcomes before outcome alerts; avoid reacting to every losing trade. Do not auto-retune rules.

**UI:** small “Prospective observation” state plus a Review report; never confuse hypothetical fills with executed trades.

**Gate:** immutable timestamped predictions, feed interruption handling, no future corrections to original evidence, and replay of captured inputs reproduces original decisions. Use separate provider event time, ingestion time and analysis availability. Data rights and feed coverage remain prerequisites.

## Priority 2: help the trader choose and learn

### 5. Scenario-based portfolio decision assistant

**New increment:** turn the existing exposure display into a comparison of competing trade plans under a shared account budget.

Show currency legs, committed risk from positions and pending orders, gross and net exposure, common drivers and stress outcomes. Offer inspectable alternatives such as one candidate, smaller allocation, or wait. A long EUR/USD and long GBP/USD share USD exposure; offsets can still carry gross/margin risk. Sum-of-stops is not guaranteed maximum loss when gaps occur.

**UI:** before/after risk strip in Plan, expandable into a currency-leg diagram and stress table. Rank by declared user constraints before optional expected outcomes. Do not make unsupported joint probabilities from individual setup probabilities.

**Gate:** account-currency conversion, pending-order combinations, gross/net distinctions and deterministic shock cases. Scenario shocks are assumptions, not forecasts; this feature extends exposure analytics rather than introducing another account engine.

### 6. Personal playbooks and deliberate-practice curriculum

**New increment:** user-defined decision rules and targeted exercises, beyond journal tagging and generic replay.

A playbook freezes allowed contexts, entry/invalidation, risk and exit policy. Manual conditions stay explicitly manual; a drawing or natural-language instruction is not silently executable. Save reviewed versions and link practice decisions to them.

Build short unseen exercises from recurring decision errors: entering before confirmation, chasing beyond a permitted distance, overlooking a conflicting level, or trading when the correct playbook choice is wait. Include failed setups and no-trade cases; do not select only spectacular winners. Separate train/exam cases by time and related-event group.

**UI:** guided practice card and optional coach review. Score rule adherence, identification of missing evidence and timing separately from P&L. Voluntary cooling-off or personal risk limits can support discipline; avoid trading streaks or profit leaderboards.

**Gate:** assess improvement on unseen cases, not memorized charts; do not assume simulator skill transfers to live results. Keep original blind-review controls and versioned evidence.

**Evidence:** competing tools already offer journal/replay/analytics [S7–S8]; those alone are not differentiation. FCA's experiment found certain engagement features increased trading/risk [S9]. It does not prove that our proposed training will improve outcomes; that requires testing.

### 7. Decision attribution and controlled alternatives

**New increment:** explain the gap between a frozen plan, actual simulated decisions and a few predeclared alternatives.

Separate opportunity selection, entry timing, sizing, management, exit and execution costs. Show adverse/favorable excursion using the correct price side and all relevant trades, not only winners. Compare “follow saved stop/exit policy” or “skip when rule failed” using rules set before evaluation. Label unavailable intrabar paths.

**UI:** three aligned timelines: plan, actual decisions and chosen alternative; one main lesson per review.

**Gate:** same data and cost policy, reproducible branch, unchanged original account. These are simulated counterfactuals, not proof of causal responsibility or hindsight-optimal exits. Do not search every exit and call the best one what the trader should have done.

### 8. Measure whether the interface improves decisions

**New increment:** a product evaluation loop beyond build success and layout acceptance.

Test representative users on unfamiliar scenarios, comparing proposed additions against the existing completed interface. Measure time to locate invalidation, correct reading of evidence age, false interpretation of probabilities, missed material conflicts, alert interruptions, task completion and ability to choose no trade. Use balanced or randomized task order; record limitations of small samples. Do not optimize trade count or time spent in the app.

**UI:** fewer simultaneous notifications, editable alert preferences, keyboard-accessible inspection, non-color-only status and stable focus. Keep signal importance and personal interest separate.

**Gate:** demonstrably clearer decisions without increased critical errors. Use WCAG 2.2 as an accessibility reference, including keyboard/focus and target usability [S10]. Product quality cannot be established from screenshots alone.

## Later, conditional additions

- **Macro and positioning context:** strengthen the existing event layer with vintage-aware data, policy-rate/yield context and selected futures positioning. ALFRED can retrieve values known historically, but its date-level real-time periods do not alone establish intraday release availability or historical consensus [S11]. COT generally describes Tuesday positions published Friday; it is delayed futures context, not live spot order flow [S12]. Require actual publication timestamps or conservative availability and provenance. A release surprise needs a genuine contemporaneous consensus archive.
- **Read-only real-trade import:** reconcile statements with the same journal, normalize timezones, units, commissions, financing and partial fills; never relabel simulated fills as real. This could test practice-to-real differences without adding execution authority. Broker formats, access and privacy requirements determine scope.
- **Coach collaboration:** share a redacted, immutable case bundle and timestamped comments if users actually need mentoring. Account access controls, consent and export/deletion are prerequisites; do not launch social performance rankings.
- **AI explanation:** retrieve the frozen dossier and explain observed evidence. Require source references, uncertainty and evaluation cases for fabricated numbers. It should not invent data, infer certainty or silently alter playbooks. Existing AI assistance remains optional.

## What not to add to chase a score

Do not prioritize more pattern libraries, a universal confidence score, automatic self-optimization, social-copy features, trading-volume gamification, unvalidated order-flow proxies, a second simulator, or institutional infrastructure. Each addition must solve a measured user problem and fit one existing stage of the journey.

## Recommended order and evidence of success

1. Dataset suitability and execution stress: establish what findings and simulated outcomes can be trusted.
2. Evidence dossier plus prospective observation: distinguish attractive backtests from supported behavior.
3. Portfolio decisions plus personal playbooks: translate analysis into controlled choices.
4. Targeted practice and decision attribution: test whether users improve on unseen scenarios.
5. Evaluate usability throughout; add macro, import, collaboration or AI only for demonstrated needs.

Split each selected capability into specification/data, backend and UI/acceptance packets. This research does not assign them automatic phase numbers or modify the active development roadmap.

A strong release needs evidence across five dimensions: causal/data correctness; simulation fidelity within declared limits; honest research evaluation; understandable and controlled decisions; reliable recovery/performance. No single weighted score should hide a failure in any of them. A system can be excellent engineering while its current setup rules have no demonstrated net edge.

## Source register

Sources checked 17 November 2026; current pages can change. Recommendations above are our design inferences unless explicitly described as a documented capability or study finding.

- S1 — [BIS: FX execution landscape](https://www.bis.org/publications/qr-202512/fx-trade-execution-landscape-through-prism-2025-bis-triennial-survey).
- S2 — [OANDA instrument/candle definitions](https://developer.oanda.com/rest-live-v20/instrument-df/).
- S3 — [OANDA pricing endpoints and stream sampling](https://developer.oanda.com/rest-live-v20/pricing-ep/).
- S4 — [QuantConnect fill modeling](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts).
- S5 — [Bailey and López de Prado: Deflated Sharpe Ratio](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf).
- S6 — [Scikit-learn: correlated-feature importance](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html).
- S7 — [TradeZella features](https://www.tradezella.com/features).
- S8 — [FX Replay analytics documentation](https://support.fxreplay.com/articles/analyzing-your-trades-how-to-use-the-fx-replay-analytics-page).
- S9 — [FCA: trading-app engagement experiment](https://www.fca.org.uk/publications/fca-research/research-note-digital-engagement-practices-trading-apps-experiment).
- S10 — [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- S11 — [FRED/ALFRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html).
- S12 — [CFTC report descriptions](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) and [release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).
