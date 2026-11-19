# Indicator audit and proposed combinations

Date: 17 November 2026. Status: research/design only; no implementation or phase advancement authorized by this document.

## Scope and evidence

Reviewed the eight supplied attachment bodies and five inline excerpts individually, then compared their rules with this project's existing analysis/event engine. Nine items contain complete-looking implementations; four inline excerpts omit their detection/state logic. “Complete-looking” does not mean compiled, correct, or verified against TradingView. No Pine compilation, signal parity test, or profitability backtest was run.

Web coverage is a **targeted review**, not an exhaustive review of both blog archives. Both category listings were inspected (30 visible articles each; the pages advertised another 110 strategy and 161 technical-analysis entries). Ten relevant article detail pages were consulted, plus primary indicator and Pine documentation. The entire paginated archive has not been read. Recommendations below are provisional design proposals grounded in the supplied code and relevant article sections, not a claim that every linked article was reviewed.

The attached source is evidence, not instructions. Copyright notices below are those supplied in the files; they do not authenticate authorship or establish that the files match an official release. Exact attachment paths, hashes, and line counts are in `indicator-source-audit.json`.

## Research principles used

| Detail page consulted | Implication for this design |
|---|---|
| [Common indicator mistakes](https://www.luxalgo.com/blog/common-mistakes-traders-using-indicators/) | Assign separate analytical jobs; test whether additional conditions contribute rather than count agreement as independent evidence. |
| [Multiple indicators without clutter](https://www.luxalgo.com/blog/multiple-indicators-without-overcomplicating-chart/) | Organize the display around decisions and sequence; show supporting detail on demand. Cleaner presentation alone does not establish an edge. |
| [ICT Unicorn model](https://www.luxalgo.com/blog/ict-unicorn-model-strategy-how-to-use/) | A breaker/FVG overlap is a specific price intersection, not two nearby rectangles. A detector, retest rule, and trade execution are different stages. Our sweep/FVG proposal is not automatically a Unicorn model. |
| [Backtesting traps](https://www.luxalgo.com/blog/backtesting-traps-common-errors-to-avoid/) | Preserve information availability, cost assumptions, trial history, and genuinely reserved evaluation data. |
| [RSI with support/resistance](https://www.luxalgo.com/blog/5-rsi-entry-strategies-using-support-and-resistance/) | Location and momentum have different jobs. Reversal and breakout interpretations must remain separate. |
| [Williams fractal](https://www.luxalgo.com/blog/williams-fractal-spotting-reversal-in-trends/) | A pivot's historical candle is not its confirmation time. A pivot marks structure rather than predicting reversal. |
| [Triangle patterns](https://www.luxalgo.com/blog/triangles-in-charts-sym-and-asym-patterns/) | Convergence supplies a setup boundary; breakout direction still needs an observable rule. A projected target is not promised performance. |
| [ICT order blocks](https://www.luxalgo.com/blog/ict-trader-concepts-order-blocks-unpacked/) | Different order-block and structure definitions are not interchangeable. Displacement, swing break, and zone return are distinct observations. |
| [Stochastic divergence](https://www.luxalgo.com/blog/ultimate-guide-to-stochastic-divergence-trading/) | Fix oscillator series and pivot pairing. Regular and hidden divergence belong to reversal and continuation hypotheses respectively. Confirmation rate is not trade win rate. |
| [Liquidity zones](https://www.luxalgo.com/blog/guide-to-using-luxalgo-for-liquidity-zones/) | Candle-derived liquidity is inferred, not measured resting orders. Missing volume must remain unavailable. |

These are sources for concepts and pitfalls, not empirical validation of the proposed combinations. The rules and architectural decisions below are our proposals or observations from the supplied code.

## Individual source audit

### A1 — Smart Money Concepts

Attachment `8d32df7f…`, 848 lines; supplied notice: LuxAlgo, CC BY-NC-SA 4.0.

- **Actual behavior:** internal and swing structure; BOS/CHoCH; order blocks; approximate equal highs/lows; FVGs; previous-period extremes; premium/discount and strong/weak extremes. Internal length is 5, swing length defaults to 50, equal-level confirmation to 3 with a 0.1×ATR200 tolerance.
- **Important implementation distinction:** `leg()` compares an extreme `size` bars ago with the subsequent window, and emits on a leg-state change (337–457). This is not the same detector as our strict symmetric 3/3 pivots. Structure breaks use close crossings and the previous direction state (551–612).
- **Order blocks:** selects parsed extrema between a pivot and break, with high-range bars' high/low values swapped for selection (315–323, 507–525). It is not simply “the last opposite candle,” which is closer to our existing rule. Wick/close invalidation is selectable (311–313, 481–500).
- **Timing risk:** FVG `request.security` uses `lookahead_on` with unshifted higher-timeframe high/low and acts on a new higher-timeframe bar (634–649). For a higher requested timeframe, historical final extremes can be available too early. Previous-period `[1]` high/low requests elsewhere are a different case; do not condemn every `lookahead_on` call indiscriminately.
- **Additional source findings:** bearish `fairValueGap.new(currentHigh,last2Low,…)` assigns a smaller value to `top` than `bottom`; later deletion compares high with that `top` (625–649). The optional confluence formula `math.min(close, open - low)` is suspicious as a lower-wick measure (556–557). Verify intended geometry/formula before porting. Forward removal from arrays also merits adjacent-invalidation fixtures.
- **Disposition:** extract selected context concepts only. Do not add this entire toolkit beside the existing structure/FVG/OB engines. Keep current definitions versioned and label any new LuxAlgo-derived variant explicitly.

### A2 — Significant Breakout Levels (FVG)

Attachment `16ccc2f4…`, 151 lines; supplied notice: **© Quant, MPL-2.0**, not © LuxAlgo.

- Tracks pivot highs/lows, default left/right 10/10; at most five unbroken levels **per side**, despite the general input wording.
- At bar `t`, examines bar `t−1`: its open must be strictly inside the level and close beyond it, body strictly greater than 0.5×ATR14 at `t−1`, and a directional three-bar FVG must exist at `t` (38–49, 93–139).
- Age limit defaults to 50 bars measured from the pivot's origin to the FVG-check bar, not from pivot confirmation. The third candle is required: the box starts at the breakout candle but the full setup is only known later.
- Any previous close beyond the level resolves/removes it even if body/FVG qualification fails. A gap-open already beyond the level does not pass its open-crossing rule. No minimum FVG size, later retest, trade invalidation, or entry expiry is implemented; box extension is just drawing length.
- **Disposition:** useful breakout-quality component. Preserve this exact sequence as one candidate variant; do not silently add our existing FVG size filter and call it identical.

### A3 — Support & Resistance Pro Toolkit

Attachment `e5e0bf63…`, 457 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Four alternative anchor methods: symmetric pivots, alternating Donchian extrema, a consecutive candle-direction counter named CSID, and percentage-reversal ZigZag (175–236). The CSID branch is not a conventional candle-open CISD confirmation test.
- Default Donchian sensitivity 10; zones use ATR200 with mean-range warmup fallback; depth 0.5 ATR and optional breakout buffer. Supports overlap merge/hide policies, touch/sweep/volume/duration filters, active limits, and close-based invalidation.
- **Confirmed defect:** `strength` is initialized to zero and never updated. Positive minimum-strength settings hide all levels; “S:0” is not a usable strength estimate (type 41, creation 267, filter 330).
- `entries` counts qualifying bars, not independent visits separated by leaving the zone. Volume adds the entire candle volume when its range intersects the zone, not actual volume traded at prices inside the zone (306–326). Missing volume can propagate `na` and prevent visibility even with a zero minimum.
- Overlap merging expands geometry but retains the original base/start/statistics. Duration starts at the old extreme, although the level was discovered later. Drawing history must not imply it was known then.
- **Disposition:** useful ideas for one canonical zone presentation/lifecycle. Do not expose its strength or traded-at-zone-volume labels unchanged. Start with one anchor definition, not four optimizable modes.

### A4 — RSI Divergence: Out-of-Sample Optimizer

Attachment `f0e819d8…`, 886 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Simulates RSI lengths 2–50 by default, picks the best in-sample metric, freezes a chosen length after the IS endpoint, and displays IS/OOS/forward results. It is an `indicator()` implementing its own simulation, not a Pine `strategy()`.
- **Pivot definition differs from ours:** finds strict pivots in RSI, then samples the price high/low at those oscillator pivots. Regular divergence only; default left/right 5/2 and maximum separation 60 (145–186). Our engine finds price pivots and samples RSI there.
- Its recursive RSI seeds from the first change (439–460), unlike our SMA-seeded Wilder warmup. Signals and parameter rankings need not match even at length 14.
- Entries use the signal close. ATR14 stop/target defaults 1.5/2.0; stop checked first if both extremes are touched; optional opposite-signal close; no same-bar reentry after exit (260–309).
- No spread, commission, slippage, gap-through-stop model, position sizing, or mark-to-market equity. Profit is summed percentage price changes; drawdown uses realized additive equity. Its “Sharpe” is mean trade return / trade-return deviation, without a time basis, annualization, or risk-free adjustment. It must not be presented as the same metric as our account simulator.
- IS/OOS ranges are not validated for chronology/overlap. Positions can cross boundaries, and results are assigned by entry period; IS statistics can therefore update after the chosen length has frozen. That requires an explicit boundary policy before comparing training and evaluation. The code does **not** inherently reoptimize on OOS results; the concerns are boundary handling, trial selection, and simulation assumptions.
- “Forward” means chart bars after `oos_end`, not necessarily a prospectively recorded live trial.
- **Disposition:** research-lab inspiration only. Reuse our execution accounting and retain a fixed RSI baseline; do not insert an optimized period as another live confirmation vote.

### A5 — Pure Price Action Liquidity Sweeps

Attachment `13f6dc17…`, 153 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Builds hierarchical swings from three-point extrema: short/intermediate/long select depths 1/2/3. Higher levels depend on subsequent lower-level swings, so confirmation delay is variable (46–89).
- Bearish sweep: high exceeds tracked high, close finishes below it. Bullish is the mirror. Only the first wick event per level is marked; a close through the level invalidates it. Levels age out after 2,000 bars (116–150).
- No ATR displacement, opposite-structure break, FVG, retest, profit target, or statistical liquidity measurement. Equal-price newly detected pivots can be suppressed by the price-change test.
- **Disposition:** strongest simple sweep-event candidate, but compare its hierarchical anchors with our existing confirmed pivots. Reusing our anchors is an intentional behavioral change, not a faithful port.

### A6 — ICT Macros

Attachment `40081718…`, 403 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Scheduled windows, range/midpoint drawings and advance alerts; classification into accumulation/manipulation/expansion from range excursions relative to pivots plus open/close location. Uses one-minute sub-bars, pivot length 13, wick/body choice.
- The classification runs at `mc.x2 + 1` (348–383): it is **post-window descriptive information**, not a direction forecast at the window's start.
- Manual London/New York DST booleans (10,27), fixed UTC offsets (152–157,203–205). Historical replay needs date-aware named timezones, not today's DST setting applied to years of data.
- London UI labels 02:33/04:03 differ from London-clock function arguments 07:33/09:03 (388–390); this must be reconciled rather than copied into a schedule. The `timeframe.multiplier <= 5` gate does not itself verify minutes. The alert call is outside the `_alert` conditional, which gates the advance drawing (250–254).
- Contains float-as-boolean constructs (`if ph`, `ph ?`) despite the v6 header. Static compatibility issue; not compiled here.
- **Disposition:** optional schedule/context strip and journal tag. Do not count a macro time as bullish/bearish evidence or expose final window classification early.

### A7 — Support and Resistance Signals MTF

Attachment `384feca5…`, 690 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Pivot zones; tests, role-flip retests, buffered breakouts, wick/volume rejections, and extension bands named manipulation zones. Detection length defaults to 15; zone width scales with recent range and price, not ATR. ATR17 is used for large wicks.
- **Not actual higher-timeframe candles:** `srLN := srLN * tf_m / ch_m` rescales the current-chart lookback (142–159). There is no higher-timeframe OHLC request. Fifteen hourly bars cannot be reproduced by a 60-bar pivot on a 15-minute chart.
- Breakout filter is a distance buffer beyond a zone, not proof that false breakouts were eliminated. Several labels are placed at the previous bar; some tests additionally require the current close (351–406). Store observed time separately from label location.
- Volume uses `nz(volume)`. When absent throughout the window, zero is at least 1.618×zero, so `isHV` can be true (168–171); never use this as activity confirmation in our volume-unavailable forex data.
- Rejection branches test wick and volume globally without explicitly requiring proximity to the displayed S/R zone (413–415,584–586). “Rejection” cannot be assumed to mean “rejection at this zone.” Numeric truth tests and integer/timeframe scaling also need v6 compatibility checking.
- **Disposition:** reuse the test/retest/role-flip vocabulary in a shared zone engine; use real completed timeframe aggregation. Do not add a separate overlapping S/R overlay or claim exact parity after that correction.

### A8 — Market Structure (Intrabar)

Attachment `458cfbac…`, 310 lines; LuxAlgo, CC BY-NC-SA 4.0.

- Requests lower-timeframe candles and pivots, draws their candles to the right of the main chart, and counts BOS/CHoCH. Default pivot length 5. Auto mode requests 15-second data for an hourly chart; 1-minute for a four-hour chart (163–176).
- Core drawing/structure loop runs only on `barstate.islast`, deletes earlier drawings on a new chart bar, and uses previous sub-bar close for break checks (199–279). This is a current-bar inspection widget, not an already complete historical event engine.
- **Data boundary:** our minute data can support minute-based inspection inside 15m/hourly bars, but cannot reproduce 15-second structure or reconstruct an unseen tick path. Running its logic over all replay minutes would also be a new event implementation, not merely copying the last-bar widget.
- **Disposition:** optional execution-detail view using actual available resolution, warmup, and gap status. No extra “vote” for the same BOS already counted on another view.

### I1 — Displacement Sweep Reversal with FVG

Inline excerpt; MPL-2.0 notice, no author shown. **Incomplete.**

- Supplied code calculates ATR14, significant directional bodies ≥0.8 ATR, three-bar FVGs with minimum width 0.15 ATR, and symmetric pivots with length 3.
- Inputs describe a 10-bar structure-break window and 20-bar entry window, but the supplied body ends after assigning `lastPivotHigh`. Sweep definition, swing-pair relationship, displacement-to-gap association, cancellation and entry state are absent.
- **Disposition:** conceptually relevant to the reversal workflow, but exact rules cannot be audited or ported from this excerpt. The proposed state machine below is ours, not a reconstruction of missing code.

### I2 — Ascending/descending/symmetrical Triangle

Inline excerpt; LuxAlgo, CC BY-NC-SA 4.0. **Incomplete.**

- Constants and settings: swing length 5, max scan 10 swings, ≥2 touches per boundary and ≥5 total, tolerance 0.3 ATR. Tooltips describe convergence and containment, but their implementation is absent.
- Cannot verify anchor fitting, flat-slope tolerance, touch independence, containment, apex expiry, breakout buffer, target measurement, or repaint behavior.
- **Disposition:** promising consolidation context for a separate triangle breakout subtype; obtain full code before approving detector behavior.

### I3 — Trendlines with Breaks

Inline, complete-looking; LuxAlgo, CC BY-NC-SA 4.0.

- Confirmed length-14 pivots initialize lines; slope is ATR/length, standard deviation/length, or a regression-derived expression, times a multiplier. The high line steps downward and low line upward. It is a **projected slope envelope**, not a line fitted through several respected touches.
- Break flags reset on a new corresponding pivot and fire on first close beyond adjusted line levels. Default backpainting shifts drawn geometry into earlier bars by the pivot length. Signals must retain their actual discovery time.
- Uses numeric pivots directly in boolean conditions despite `//@version=6`; source needs migration before a v6 compile can be expected. Removing pasted Markdown escapes is separate from fixing code semantics.
- **Disposition:** alternative breakout boundary method, not corroboration that a triangle boundary or liquidity trendline is valid. Keep as an experimental alternative; not needed in the first combo release.

### I4 — Trendline Liquidity

Inline excerpt; LuxAlgo, CC BY-NC-SA 4.0. **Incomplete.**

- Constants include active/breached/swept/confirmed/broken/expired states, max three active lines, 500-bar candidate TTL, 1,500-bar span. Inputs show swing length 10, minimum three touches, tolerance 0.25 ATR, ATR200.
- No candidate fitting, touch counting, state-transition conditions, band geometry, displacement test, or invalidation implementation supplied.
- **Disposition:** potential sloped-level provider for sweep versus breakout classification. Minimum-touch qualification time must precede use. Do not assume its lines equal I3's projected envelopes.

### I5 — Divergence Variants & Confirmation

Inline excerpt; LuxAlgo, CC BY-NC-SA 4.0. **Incomplete.**

- Constants name RSI/Stochastic/MACD/ROC, regular/hidden/exaggerated variants, and structure-break/oscillator-cross/strong-close/any confirmation modes. Multiple divergence starts at three chained swings.
- The [official description](https://www.luxalgo.com/library/indicator/divergence-variants-and-confirmation/) documents pending/confirmed/failed states and a confirmation window. That supports intended behavior, but does not establish that the missing supplied implementation matches it.
- Need the actual pivot pairing, equality tolerance, oscillator definitions, confirmation thresholds, chain deduplication and cancellation rules.
- **Disposition:** useful workflow model for extending our existing divergence; initially keep one oscillator and one price-confirmation rule. A multiple-swing chain is one evolving candidate, not three independent confirmations.

## Proposed combinations

Recommendation: **one shared context map and three selectable setup workflows**. Each answers a different question. Timing and intrabar detail are optional supporting views; parameter optimization belongs in research.

### C1 — Market Structure & Key Levels

**Question:** Where is price relative to known structure and the nearest relevant obstacles?

Components: selected A1 structure/equal-level/range concepts + A3 zone visibility and overlap handling + A7 test/retest/role-flip behavior, built on our canonical confirmed pivots and genuine completed-timeframe candles.

**Reason to combine:** structure describes direction and sequence; zones describe location; the interaction state describes what price did there. Combining presentation eliminates three overlapping sets of rectangles without pretending they supply three independent forecasts.

Display: context direction or mixed/unavailable, nearest support and resistance, source timeframe, distance, latest interaction, and confirmation time. Expand a level to inspect contributing anchors and their definitions. Premium/discount is only position within a specified range, never a valuation claim.

Rules: cluster nearby zones for display with an explicit tolerance, retain individual source geometries/IDs, and never merge distinct invalidation rules into one silent replacement. Rank by relevance and proximity, not an invented accuracy score. Opposing timeframe direction stays visible; it is not averaged away.

This is a context indicator, not an entry strategy. Start with existing causal definitions; do not promote retrospective snapshot clusters to historical trade evidence.

### C2 — Sweep → Structure Shift → Retracement

**Question:** Did a failed move beyond a known level develop into a confirmed reversal setup?

Components: C1 location + A5 sweep event + one opposing structure break + ATR displacement and directional FVG concept from I1. A6 is an optional time tag; A8 an optional detail pane. Neither is a mandatory signal.

**Reason to combine:** a sweep alone only shows rejection. A later opposing swing break changes the structural evidence. Displacement characterizes the reversal leg; the gap gives a specific area to watch on a later return. This is an ordered explanation, not a vote count.

Proposed bullish sequence, mirrored for bearish:

1. A confirmed, still-valid low/zone exists before the excursion. Freeze its ID and the opposing swing reference available at setup creation.
2. Price trades below it and a completed candle reclaims it: `sweep_observed`.
3. Within a fixed number of completed setup bars, a close breaks the frozen opposing swing with qualifying bullish displacement: `shift_confirmed`. Initially require a later bar than the sweep; same-bar ordering is not inferred from OHLC.
4. A bullish FVG associated with that same reversal leg becomes confirmed at its third candle close. `waiting_for_retracement` begins only when both shift and gap are known. A gap anywhere in the recent chart does not qualify.
5. A subsequent candle returns to that zone; a separately specified rejection/reclaim rule produces `entry_condition_met`. A resting-limit variant is a different strategy and must be compared separately.
6. Cancel on adverse structural/zone failure, expire after the declared window, or mark unavailable when required data are incomplete. Keep failures in the record. Do not silently move the sweep extreme or switch to another FVG after failure.

Initial research candidates may use I1's 10-bar shift and 20-bar entry windows and 0.8/0.15 ATR thresholds, but these are unvalidated inputs. Freeze which ATR observation is used. Our current FVG filter uses the middle candle's ATR and body threshold 0.5, so reusing it unchanged is a distinct variant.

Show one setup card: swept level, reclaimed at, break level, break confirmed at, gap bounds, remaining window, invalidation, next opposing obstacle, and the missing condition. Example: “Low reclaimed; structure shift confirmed; waiting for gap retracement.” No historical entry is placed at the earlier sweep low.

Fail/skip cases: no later shift, gap unrelated to the reversal, gap already invalidated before eligibility, insufficient warmup, a late retracement, or too little room to the next obstacle under the chosen trade rules.

### C3 — Breakout & Retest

**Question:** Has price left a defined boundary, and is the subsequent behavior consistent with the breakout hypothesis?

Core components: C1 level + A2 displacement/FVG-qualified breakout + A7 role-flip retest. Later optional **alternative setup types**: I2 triangle boundary or I4 qualified liquidity trendline. I3 is another alternative boundary method, not a prerequisite for the others.

**Reason to combine:** boundary supplies the level, displacement/gap describes the departure, retest supplies a later interaction at a fixed area. Requiring every boundary detector to agree would mostly duplicate price geometry and shrink the sample without a demonstrated benefit.

State sequence: `boundary_ready → breakout_pending_gap → breakout_confirmed → waiting_for_retest → retest_held`, with failed/expired states. Freeze the boundary definition and geometry at qualification. A2's breakout is only fully qualified when the third FVG candle closes; do not label it executable one candle earlier.

For the first variant, retest the broken horizontal zone from the new side and require a completed close back beyond its outer breakout edge. A later full close through the opposite edge fails the retest. Set a finite retest deadline and one opportunity per boundary event. A gap-zone entry is a separate variant, not interchangeably selected after seeing the chart.

Triangles remain direction-neutral until breakout. Freeze qualified boundaries, reject late breaks after the allowed apex horizon, and distinguish measured pattern target from nearby opposing resistance/support. Do not indefinitely redraw a failed triangle.

Display: boundary/type, breakout time and gap confirmation time, first eligible retest, held/failed/pending, invalidation and next obstacle. “Failed breakout” is a recorded outcome; it does not automatically become a reversal trade.

Trade-off: waiting for an FVG and retest can improve clarity but will miss some breakouts and change entry prices. Compare boundary-only, +displacement/FVG, and +retest variants with identical accounting.

### C4 — Momentum at Structure

**Question:** Is momentum weakening at a relevant level, and has price confirmed a change?

Components: C1 location + existing causal RSI divergence + I5's candidate/confirmation lifecycle. Use A4 only to inform separate research, not to continually choose the live oscillator period.

**Reason to combine:** divergence describes a disagreement between price and oscillator; a prior zone supplies location; an independently specified price event supplies timing. A divergence somewhere mid-range does not carry the same setup definition as one at a predefined boundary.

First version: fixed RSI14 and price-pivot anchoring consistent with our engine. At the second pivot's confirmation, check proximity to a zone that was already available; freeze the intervening opposite swing as the trigger. Wait for a completed break of that trigger after candidate availability. Expire after a declared window or invalidate on a fresh adverse price extreme. This conservative invalidation rule is our proposal, not a claimed exact I5 port.

Display: `regular divergence detected → price confirmation pending/confirmed/failed`; line endpoints, their confirmation times, RSI readings and trigger price. A confirmed divergence in today's engine means confirmed geometry, **not** confirmed price reversal; preserve both meanings explicitly in separate fields.

Later continuation mode: hidden divergence during a pullback in an independently defined trend, with a separate level-reclaim trigger. Do not blend regular and hidden into one bullish/bearish total. Exaggerated divergence needs a defined equal-price tolerance. Start with RSI only; adding MACD/Stochastic/ROC does not create independent evidence automatically.

Fail/skip cases: persistent trend carrying through repeated divergence, no relevant prior level, oscillator warmup missing, pivot pairing ambiguous, trigger already passed before candidate availability, or no price confirmation before expiry.

## Combinations to reject or defer

| Proposed stacking | Decision and reason |
|---|---|
| Entire SMC + both S/R suites | Reject: repeated structure/zone representations, incompatible definitions and excess chart clutter. |
| Three FVG detections as three confirmations | Reject: substantially the same three-bar price relationship with different filters. Attach one event and its qualifying conditions. |
| I3 projected trendline + I4 touch-fitted line + triangle as mandatory agreement | Reject: they define different boundaries; agreement is not evidence of three independent causes. Compare alternative setup definitions. |
| Regular + hidden divergence as one score | Reject: reversal and continuation hypotheses conflict. |
| Sweep + divergence as two separate trade opportunities on the same structure break | Deduplicate execution opportunity; show overlapping explanations and record both setup IDs without double-counting trades. |
| Macro time + final macro classification at window start | Reject: uses a later outcome as an earlier input. |
| Optimized RSI + four oscillator votes | Defer: parameter selection and correlated transforms add complexity; validate the fixed baseline first. |
| Intrabar BOS treated as tick-level proof | Reject with current minute data; expose actual resolution and missing coverage. |

## Connection to the current system

| Existing component | Proposed connection; no code changed |
|---|---|
| `backend/indicators.py` | Reuse canonical RSI/ATR/EMA; explicitly version any requested seed or threshold differences. Do not introduce independent smoothing implementations accidentally. |
| `backend/lifecycle.py` | Use completed-bar event evidence, `occurred_at`/`available_at`, deterministic IDs and append-only transitions. Add versioned setup state above primitive events; extend schema deliberately rather than interpreting the last 100 returned events as complete history. |
| `backend/analysis.py` / adapters | Keep legacy retrospective overlays separate from causal setup inputs. Reuse existing pivots, BOS/CHoCH, FVG and divergence where definitions fit. New detector names must distinguish changed rules. |
| `backend/bias.py` | Optional daily/weekly context from completed bars; unavailable history is not neutral. It does not currently supply a complete trend/range regime classifier. |
| Replay/data service | All higher-timeframe inputs must be closed and complete at the replay clock. Minute inspection uses only revealed minutes; never infer seconds. Historical DST comes from named timezones. |
| `AnalysisChart.tsx` | One shared level map plus selected setup geometry; detailed evidence on selection. Default to nearby active context and one selected scenario rather than all 13 overlays. |
| Paper account/journal/training | Preserve simulator execution assumptions and immutable versions. Link setup IDs to manually chosen practice trades; no new broker execution implied. Keep parameter studies separate from trader training. |

Current causal primitives already include strict 3/3 pivots, BOS/CHoCH, filtered FVGs, displacement-based order blocks and regular RSI divergence. The main missing value is **relationships and lifecycle between those primitives**, not thirteen new standalone calculations.

The current real minute fixture covers 7,170 EUR/USD BID minutes, January 2–8 2024, with 30 scheduled gaps. It is useful for functional replay checks, not enough to validate all combinations across market conditions. Volume and seconds data must not be invented. Short-window macros require an explicit completeness policy; missing minutes can affect extrema and classification.

## Validation required before a later build is called trustworthy

1. **Definition tests:** exact prices, equality cases, flat/zero ATR, warmup, gap width, pivot ties, zone edges, trigger ordering, duplicate signals, and timeout boundaries. Check oscillator-pivot versus price-pivot differences explicitly.
2. **Causality tests:** every truncated prefix agrees with the same prefix of a full run; mutating future candles cannot change earlier events. Pivot markers may be drawn at origin only with their later availability shown. No final HTF or macro-window values before close.
3. **State tests:** rejection without shift; shift without eligible gap; invalidated gap before retest; expired entry; repeated touches; opposite setups; failure retained; restart/idempotency and identical replay results.
4. **Data tests:** missing volume, missing minute bars, incomplete HTF candles, symbol/timeframe mismatch, history insufficient for ATR200, DST transitions and differing US/UK DST weeks.
5. **Parity scope:** compare audited source fixtures only for behavior claimed to be preserved. Corrected MTF aggregation, canonical RSI seeding, different pivot detection and causal timing intentionally change output; document those changes rather than advertise a 1:1 port.
6. **Combination value:** run ablations with the same data, risk rules and costs. Measure number of candidates, confirmation/expiry/failure rates, timing delay, missed moves, and duplicate opportunities. Only once entries/exits are defined, measure net expectancy, drawdown, turnover and return distribution. Do not substitute a pattern confirmation percentage for trade success.
7. **Selection discipline:** fixed baseline first; chronological development/evaluation with no boundary leakage; preserve rejected trials; sensitivity checks and prospective paper observation. Include failed patterns and realistic spread/slippage cases. No target win rate is promised.
8. **Trader clarity:** replay exercises should test whether users can identify the active scenario, missing condition and invalidation without opening every layer. This is a separate measurable goal from trading returns.

## Provenance and licensing boundary

Seven attachment headers and four inline LuxAlgo headers specify CC BY-NC-SA 4.0. A2 specifies MPL-2.0 and © Quant; I1 specifies MPL-2.0 without an author. Keep these separate.

The [CC license terms](https://creativecommons.org/licenses/by-nc-sa/4.0/) include attribution, noncommercial use and ShareAlike conditions. Do not assume a commercial trader-facing product has permission to incorporate these sources. Translation into Python does not by itself remove the source license question. Confirm the intended usage and applicable permission before implementing derived code. This is not a conclusion that private trading automatically meets or violates the noncommercial condition.

The [MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) describes file-level copyleft and distribution obligations; it is not equivalent to CC BY-NC-SA. Preserve source notices and track modifications. The [Pine v6 migration guide](https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/) confirms numeric values no longer implicitly act as booleans. [Higher-timeframe documentation](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) explains offset/availability handling; the supplied SMC FVG request needs specific correction.

## Proposed order if development is later authorized

1. Resolve source versions, the four incomplete excerpts and license applicability; agree on canonical rule differences and write causal fixtures. This is a small design/verification packet, not all indicators at once.
2. C1 context map and zone lifecycle; stop for review.
3. C2 sweep reversal workflow, with replay evidence; stop for review.
4. C3 horizontal breakout/retest workflow; stop for review. Triangle and sloped-line variants remain later additions requiring full-source review.
5. C4 fixed-RSI divergence confirmation; stop for review. Hidden divergence and optimization remain separate extensions.
6. Optional macro schedule/minute detail, then broader comparative evaluation on adequate data.

These are proposed packets, not changes to the accepted roadmap. P16 simulator acceptance remains not started. No application code, datasets, server processes, or saved sessions were changed for this audit.
