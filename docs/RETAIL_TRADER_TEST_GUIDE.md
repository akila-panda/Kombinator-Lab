# Confluence — Mac setup, trader journey and testing guide

Updated 18 November 2026. For the current local beta candidate, not the completed future roadmap.

**Start here:** build → open the app → import minute data → complete the guided practice → test save/recovery → report issues.

P16 final acceptance is still in progress. You can test the local system now. This guide does not declare the external beta release complete. It describes the current controls, including their limitations.

## 1. What you are testing

Confluence has two workspaces:

| Workspace | Use it for |
|---|---|
| **Analysis** | Inspect historical charts, technical findings, indicators, daily/weekly scenarios and optional imported positioning snapshots. |
| **Trade simulator · replay** | Select a historical date, reveal minute candles, practice paper orders, manage a USD simulated account, save sessions and review decisions. |

The four source applications have already been combined. **Run only this project.** You do not need to run the four original repositories, MT5 or a broker account.

This version supports historical analysis and simulated practice. It does not send real orders or fetch live market prices. Use it to examine a hypothesis, practice following your rules and review your decisions. It does not establish that a setup will be profitable.

## 2. Prepare your Mac

### Verified environment

- macOS on Intel/x86_64.
- Python **3.14.3**.
- Node.js **22.21.1**, npm **10.9.4**.
- Chrome was used for browser acceptance.

Apple Silicon Macs have not yet been verified. Record whether yours has an Intel processor or an Apple chip in Apple menu → About This Mac. If you use another environment, report it with any failure; do not assume it was tested.

Open Terminal and check:

```bash
uname -m
python3 --version
node --version
npm --version
```

`x86_64` usually indicates an Intel execution environment; `arm64` indicates native Apple Silicon. An Apple Silicon Mac running translated tools can report x86_64, so also check About This Mac.

If Python or Node is missing, install the recorded versions from their official distributions or your existing version manager. Official download entry points: [Python](https://www.python.org/downloads/) and [Node.js](https://nodejs.org/en/download). You do not need a global FastAPI, pandas or React installation. Setup creates project-local dependencies.

The setup script's minimum-version checks are broader than the tested environment. Passing those checks is not proof that every pinned dependency supports your Python/architecture combination.

### Locate the actual project folder

On the development laptop, the project is here:

```bash
cd "/Users/akilaranasinghe/Documents/Codex/2026-11-09/can/outputs/combined-analysis"
```

On another laptop, extract the project into a new folder. Type `cd ` in Terminal, drag that extracted folder from Finder into Terminal, then press Return. Do not reuse the development laptop's absolute path.

Confirm you are in the right folder:

```bash
pwd
ls README.md setup.sh start.sh verify.sh
```

All four files should be present. A folder containing only the four original ZIPs is not the combined application.

Keep each release in its own folder. Do not copy `.venv` or `frontend/node_modules` between laptops; rebuild them. Do not overwrite your previous release or its saved data.

## 3. Build and verify

Run these separately so you can identify the step that fails:

```bash
chmod +x setup.sh start.sh verify.sh
./setup.sh
./verify.sh
```

`setup.sh` installs the pinned Python dependencies into `.venv`, installs frontend packages with `npm ci`, and builds the interface. Internet access is needed for package downloads. The first run can take several minutes.

`verify.sh` checks dependencies, runs the Python tests, rebuilds the frontend and starts a temporary server for an HTTP smoke test. That temporary test server stops automatically; it does not replace your preview server.

Expected outcome: no failed tests, successful TypeScript/Vite build and an HTTP smoke-passed message. The last recorded main-suite run had **222 passing tests**; use the actual result you see rather than treating that historical count as your result. Save the terminal error if any step fails.

If Python 3.14 is installed under a separate command, select it explicitly before creating the environment:

```bash
PYTHON_BIN=python3.14 ./setup.sh
```

That command requires `python3.14` to exist. Changing `PYTHON_BIN` does not replace an already-created `.venv`. If the environment was made with the wrong interpreter, use a fresh extracted project folder rather than deleting anything containing practice data.

## 4. Start and stop

First check whether the existing preview already opens at:

**http://127.0.0.1:8766/**

If it opens, you may use that instance. To start your own instance from the project directory:

```bash
PORT=8766 ./start.sh
```

Leave Terminal running and open the address above in Chrome. You should see **Analysis** and **Trade simulator · replay** at the top. No login is required.

If port 8766 is occupied by another instance you do not intend to use, choose another port:

```bash
PORT=8767 ./start.sh
```

Then open **http://127.0.0.1:8767/**. Do not stop an unidentified process to free a port. `./start.sh` without `PORT` uses 8765.

Save a checkpoint before stopping. To stop only the instance you started, press **Control+C** in its Terminal. Do not stop another development preview. To restart later, return to the same project folder and run the start command again.

The `127.0.0.1` address works only on that laptop. It is not a shareable investor link; do not expose this unauthenticated local server to the internet.

## 5. Load data before practicing

### Understand the default screen

Analysis starts with clearly labelled **synthetic hourly demo data**. It is useful for learning controls but is not historical market data. The synthetic hourly demo does not supply a minute trading-replay dataset.

The current developer installation has:

| Dataset | Coverage | Suitable use |
|---|---|---|
| EUR/USD BID minute sample | January 2–8, 2024; 7,170 observed minutes | Guided simulator test and short practice sessions |
| EUR/USD BID hourly sample | Q1 2024; 1,539 observed bars | Historical technical-analysis exploration |

Coverage ends at the displayed exclusive end timestamp. The minute sample's terminal time is January 9, 2024 at 00:00 UTC. Neither dataset guarantees enough history for every daily/weekly calculation.

### On the current development laptop

If the minute dataset appears in the simulator dropdown, use it directly.

If it needs importing, the existing local CSV is:

```text
/Users/akilaranasinghe/Documents/Codex/2026-11-09/can/outputs/combined-analysis/.data/p10/eurusd-2024-01-02-08-bid-m1.csv
```

In Finder's file chooser, **Command+Shift+G** lets you enter the full path, including the hidden `.data` folder.

### On a fresh laptop or source-package installation

**The source archive does not include market data or saved sessions.** Bring a historical CSV you are entitled to use. For your own test, arrange access to the existing sample through a permitted route; do not assume it is included or automatically redistributable to other testers.

In **Analysis**:

1. Select the correct **Pair**.
2. Expand **Import historical CSV**.
3. Choose the CSV and the correct base interval (**Minute** for simulator data).
4. Set the source's calendar, timestamp units and timezone accurately.
5. Import, then inspect the coverage, row count, gaps and source label.
6. Reopen **Trade simulator · replay**. If a newly imported dataset does not appear, save any active practice first, reload the page and reopen the simulator; its list is loaded when that view mounts.

For the exact local EUR/USD minute sample use:

| Setting | Value |
|---|---|
| Pair | EUR/USD |
| Base interval | Minute |
| Calendar | New York 17:00 FX sessions |
| Input timezone | UTC |
| Numeric timestamp unit | Unix seconds |
| Volume | Unknown/not supplied |

Use the actual source settings for other data. The simulator currently interprets input prices as **bid OHLC** and adds its configured spread; do not import midpoint/ask prices and silently treat them as bid data.

CSV requirements:

```csv
time,open,high,low,close
2024-01-02T00:00:00Z,1.1000,1.1002,1.0998,1.1001
2024-01-02T00:01:00Z,1.1001,1.1003,1.1000,1.1002
```

These two rows are invented format examples, not a usable market-history dataset. Required columns are `time,open,high,low,close`; volume is optional. Timestamps identify candle opens. Rows must be chronological, unique and valid completed minute/hour candles. Import limits are 250,000 rows and 32 MiB; those are validation limits, not a performance guarantee at maximum size.

## 6. Features available now

| Feature | Where/how to use it | Important boundary |
|---|---|---|
| EUR/USD, GBP/USD, USD/JPY | Pair selector | Each needs its own imported history; selecting a pair does not download data. |
| 1h, 4h, daily analysis | Analysis timeframe selector | Incomplete aggregates are excluded; sufficient completed bars are required. |
| Swing structure, supply/demand and S/R | Chart overlays and evidence list | Snapshot annotations may revise. |
| BOS/CHoCH, FVGs and order blocks | Overlay controls and finding selection | These are existing findings, not the future combo workflows. |
| EMA20/EMA50 and RSI14/divergence | Analysis chart and RSI pane | Indicator agreement is not a success probability. |
| Daily/weekly scenarios | Summary plus **Rules & evidence** | Requires 50 completed bars for each horizon and applicable evidence. |
| Causal historical events | **Historical events available at replay clock** | Confirmation availability differs from the earlier candle where a shape is drawn. |
| Historical cutoff slider | Analysis | Separate from the trading simulator clock. |
| Optional positioning archive | Import dated OANDA-format JSON | Offline, unverified source; unavailable when absent, stale or future-dated. |
| Date-based minute replay | Trade simulator | Only imported dates; no reconstructed intraminute ticks. |
| 15m/1h replay charts | Simulator's two panes | Gold candles are forming from revealed minutes only. |
| Play/pause and stepping | Simulator controls | Requested speed is a ceiling; processing can be slower. |
| Market/limit/stop paper entries | Paper order ticket | Base-currency units, not lots; orders execute in later observed minutes. |
| SL/TP, cancellation, partial/full closes | Ticket, Orders and Positions | No current UI for dragging or amending an existing position's SL/TP. |
| USD balance/equity/P&L/costs/margin | Simulated account | Financing and automatic liquidation are excluded. |
| Checkpoints, notes and JSON export | Saved sessions & journal | Unsaved edits are lost on reload; export is not an implemented restore-import UI. |
| Practice branches | Select checkpoint with no active session | Creates a new branch, not an overwrite of the parent. |
| Blind prediction challenge | Training mode before starting | Local learning controls, not tamper-proof examinations. |
| Read-only review summary | Review checkpoint | Drawdown is realized-balance drawdown, not intraminute equity drawdown. |

**Not available yet:** live feeds/orders, automated opportunity scanner or alerts, the three planned combo indicators, calibrated probabilities, personal-playbook builder, prospective observation and the later research/training additions. The proposed Discover → Understand → Plan → Practice → Review navigation is a future product design; today you use the two workspaces above.

## 7. First guided practice: approximately 15–25 minutes

Use the exact local minute sample and default settings for the stated example. This is a functional test, not a recommendation to buy EUR/USD.

### A. Start a session

1. Open **Trade simulator · replay**.
2. Leave **Training mode = Practice**.
3. Select EUR/USD and the Jan 2–8 minute dataset.
4. Enter **2024-01-05T12:07** in the UTC date field.
5. Keep defaults: initial balance 10,000 USD; leverage 30; commission per 100k 3.5; slippage 0 pips; spread 1 pip.
6. Select **Go to date**.

All displayed replay dates are UTC. Do not enter Sri Lanka local time into a field labelled UTC. The example is 17:37 Sri Lanka time, but enter **12:07**.

Expected: paused at 12:07, 15m/1h charts, a USD simulated account and available hourly analysis through 12:00. Daily/weekly analysis may correctly report insufficient history. Account mark may show no revealed quote at the initial session boundary until you step.

### B. Inspect before acting

Read **Completed-candle analysis** and expand **Snapshot evidence (retrospective)** if useful. Write a short hypothesis in **Prediction**, then press **Record prediction**. Example practice wording:

> I am waiting for a completed-candle confirmation. If the relevant level fails, I will abandon this idea. No entry until my stated condition occurs.

The app records your text; it does not automatically execute it or assess whether your trading rule has an edge. In Practice mode the prediction is optional; Blind mode uses it to unlock analysis at that clock.

### C. Submit one paper order

1. Stay paused.
2. In **Paper order ticket**, choose Buy, Market, 1,000 units.
3. For this exact mechanical test leave SL/TP empty; test protected entries separately below.
4. Select **Submit paper order**.
5. Check the order/event list. Submitting at the current clock does not create a historical instant fill.
6. Select **Next minute**.

For the exact sample/defaults, the observed acceptance result at **12:08 UTC** was:

| Item | Expected |
|---|---|
| Entry | 1.09188 |
| Open size | 1,000 units |
| Balance after entry commission | $9,999.96 |
| Entry commission | $0.04 |
| Equity at that mark | $9,999.76 |

Differences need investigation if dataset, clock, settings and commands are identical. Do not compare these values with a different provider or spread model.

### D. Save before doing anything else

1. Enter a distinctive **Checkpoint name**, such as `My beta test — first entry`.
2. Press **Save checkpoint** and wait for the success message.
3. Note the order ID displayed in Orders; do not assume every order will be `order-1`.
4. Add an entry note using that exact ID, choose Entry, write your reason, and press **Add note**.
5. **Save checkpoint again.** Adding a note only changes local page state until saved.

Every save creates a separate checkpoint. It is not continuous autosave.

### E. Manage and close

1. Under the open position, change **Close units** to 400.
2. Select **Partial close**, then **Next minute**.
3. Confirm 600 units remain and the ledger shows the close/fee.
4. Select **Close all**, then **Next minute**.
5. Confirm remaining units are zero. Save a new checkpoint named `My beta test — closed`.

A close is queued for a later observed minute; clicking alone does not necessarily close immediately. Costs are applied by the simulation. Do not interpret gross realized P&L as net profit without commissions.

## 8. A retail trader's repeatable journey

### Prepare

Choose one pair, one period and one rule you want to practice. Check source, coverage, missing bars and costs. Start with a short session. More orders are not a better test.

### Understand the market context

For exploratory analysis, use **Analysis**:

1. Select your real **Saved dataset** and timeframe.
2. Read structure and available daily/weekly scenarios.
3. Start with a few overlays, such as structure and S/R. Add other layers only to answer a question.
4. Select a finding to inspect its explanation, price geometry and evidence.
5. Open the causal event list and check when a finding became available.
6. Use **Fit history** if the chart range is confusing; price and RSI share the time axis.

Ask: what is observed, what is provisional, what is missing, and what would invalidate my hypothesis? A level or divergence alone does not constitute a complete trade plan.

**Avoid looking ahead:** the Analysis workspace is not automatically synchronized to the trading replay. It may display the whole dataset or a different cutoff. For blind practice, stay in the simulator and use its clock-bounded analysis. If you deliberately consult Analysis, manually match its cutoff and verify its displayed as-of time is no later than your practice clock. If you cannot establish that, do not use it to make the practice decision. Viewing later bars invalidates the blindness of that exercise.

### Plan

Write the entry condition, invalidation, intended exit and size before placing a simulated order. Put this in Prediction or your notes; the advanced visual plan/playbook tools are not built yet.

Set optional stop-loss and take-profit as **absolute prices**, not pip distances. For a buy, the intended stop is below the entry and target above; a sell reverses that. The engine validates brackets against the actual fill, so a gap can invalidate a seemingly sensible bracket. Inspect the rejection reason rather than assuming the order was accepted.

Choose size deliberately. The field accepts base-currency units, not broker lots. Margin availability is a platform constraint, not a suggested risk budget. There is no automatic risk-percentage sizing assistant in this beta.

### Practice

Reveal candles with **Next minute** or select 15 minutes/1 hour and use **Next candle**. Use Play for continuous progression, then Pause to place/manage orders. Avoid changing your rule after seeing the outcome. Record wait/skip decisions as well as entries.

A jump over a closed or missing period is expected; the app does not fabricate candles. The chart and account should show the same clock. If they disagree, pause and report it.

### Review

Save, leave the active session, and use **Review checkpoint**. Compare your original reason with what you actually did. Separate a sensible decision that lost from a rule violation that happened to win. Record one concrete lesson and a question for the next practice session.

This is how the current system supports trading development: historical context → explicit hypothesis → simulated execution → recorded decision → review. It is not a live signal service.

## 9. Save, resume, branch and blind challenge

### Resume after refresh/restart

1. Save and wait for confirmation.
2. Refresh the page or restart your own server.
3. Open the simulator, select **Saved checkpoint**, then **Resume checkpoint**.
4. Verify clock, balance, positions and notes. No extra order or commission should appear from resuming.

If already in a session, save first, select **New session**, and confirm **Discard session** only after the save succeeds. This discards the active in-page session, not an already saved checkpoint. Use **Keep session** to cancel the reset.

### Review without changing history

With no active session, select a checkpoint and choose **Review checkpoint**. Trading, stepping and saving should be disabled. The summary includes closed trades, wins/losses/breakeven, net results, open/pending counts and ambiguous events.

One fully closed entry lot counts as one trade; partial closes are grouped. Realized-balance drawdown is different from maximum floating-equity loss. An unfinished session should not be mistaken for a completed performance record.

### Try an alternative with a practice branch

1. Save the original Practice session.
2. Use New session to leave it.
3. Select its checkpoint.
4. Enter **Practice branch date UTC** within that saved session's start/end range.
5. Select **Create practice branch**.

The new branch recomputes state through that clock. Later commands are removed; commands at the chosen boundary are retained, including a queued close if applicable. The parent checkpoint stays unchanged. This is not a rewind slider inside an active session.

### Blind challenge

Start a new session and choose **Blind challenge** before Go to date. At each new clock, analysis remains hidden until you record a Prediction. Advance forward and save your predictions.

Blind checkpoints cannot be branched. Dates remain visible. Other workspaces/exports are accessible locally, so this is a voluntary learning exercise, not competition-grade anti-cheat protection.

## 10. Test checklist

Record Pass / Fail / Not tested, the dataset, clock and settings. Preserve a checkpoint before deliberately testing reload/reset. Use separate practice sessions for error cases.

| Test | Action | Expected outcome |
|---|---|---|
| Startup | Build, verify and start | App loads; no failed automated checks. |
| Data honesty | Open default Analysis | Synthetic prices clearly labelled. |
| Import | Import valid minute CSV | Correct pair, interval, coverage and gap count. |
| Missing history | Select a pair without minute data | Clear unavailable-data message; no old pair chart reused. |
| Outside coverage | Try 2022 with the January 2024 sample | Date rejected; no invented candles. |
| Clock | Start at Jan 5, 12:07 | Chart/account clocks agree; hourly analysis is through 12:00. |
| Minute step | Next minute | Reveals next observed minute; no future candles. |
| Candle step | Choose 15m, then Next candle | Advances to selected boundary with appropriate forming/completed state. |
| Play/pause | Play, then Pause | Clock stops; order entry is usable only while paused/not loading. |
| Market order | Follow guided example | Later-minute fill, cost recorded once. |
| Limit/stop controls | Select each type, enter a valid trigger | Trigger required; order state and any rejection are explained. |
| Pending cancellation | Place a distant valid pending order; cancel while paused before stepping | Cancelled order does not later fill. |
| Protective exits | In a separate session submit a valid bracket; advance until crossed | Exit event states reason, price, costs and ambiguity when applicable. |
| Partial/full close | Follow 400/600 example | Remaining units and account reconcile; no duplicated closes. |
| Invalid input | Try zero units or reversed bracket prices | Visible rejection; no unintended fill/fee. |
| Insufficient margin | On a disposable session request a size exceeding its account capacity | Rejection explained; no entry commission for a rejected fill. |
| Notes | Add note, save, reload/resume | Note linked to the correct order survives. |
| Save/recovery | Save, refresh, resume | Same account/clock/ledger; no extra fill. |
| Export | Export saved journal & ledger (JSON) | Readable checkpoint JSON downloads; no claim of an import-restore feature. |
| Branch | Branch a saved Practice checkpoint | New record, original unchanged, future commands absent. |
| Blind | Advance without recording prediction | Analysis hidden until prediction recorded for that clock. |
| Read-only review | Review checkpoint | Cannot trade, step or overwrite saved results. |
| Closed market | New session at Jan 6, 12:00 UTC | Closed-market state; Next minute skips to next recorded close. |
| End of history | New session at Jan 9, 00:00 UTC on the exact sample | End state; no new fills possible; pending cancellations remain supported. |
| Analysis controls | Toggle overlays, select evidence, change timeframe | Relevant geometry/evidence updates; unavailable data stays explicit. |
| Laptop usability | Resize browser; use Tab/Shift+Tab | Controls readable/reachable; report clipped fields or confusing focus. |

Do not force every trigger test to finish in a fixed number of bars. If price never reaches the level, pending is correct. For both SL and TP reached in one minute, the conservative policy may choose stop-first; the OHLC data cannot reveal an exact tick path.

## 11. Troubleshooting

| Symptom | What to check |
|---|---|
| `command not found` | Install/activate the required Python or Node version; reopen Terminal and check versions. |
| `Permission denied` on a shell script | From the project folder run the chmod command in section 3. |
| Package/build error | Save the first substantive error and versions; use a fresh project folder if the venv interpreter is wrong. Do not change pinned dependencies randomly. |
| Browser cannot connect | Confirm start command is still running and URL port matches Terminal. |
| Address already in use | Use the existing intended instance or another unused port. |
| No minute datasets | Import minute history; hourly Analysis data cannot substitute. Reload after saving if the list is stale. |
| Date/cost fields disabled | Session settings lock after start. Save, then New session to change them. |
| Trade buttons disabled | Pause playback; wait for loading; check review mode/end-of-data. |
| Analysis unavailable | Need 60 complete hourly bars in simulator; 50 complete horizon bars for daily/weekly bias. Missing minutes can exclude aggregates. |
| A close did not execute yet | Advance to a later observed minute; inspect pending commands/event ledger. |
| Resume disabled | Leave the active session with New session after saving, then choose a checkpoint. |
| Incompatible calculation version | Old backend version differs. Use Review/export; keep the old release and its data to resume. Do not manually edit stored hashes. |
| Journal save fails | Use an order ID actually present in this session; read the exact error. |
| Chart lines not visible | Level may lie outside current price range; adjust chart scale. |
| App seems slow | Use the short sample first, reduce playback speed, record dataset size/clock/task. Requested playback rate is not guaranteed throughput. |

Current limits include 200 trading commands per session and bounded note/prediction lists. Saving does not reset the command count. Start a genuinely new session when needed; keep the old checkpoint for review.

## 12. Protect your practice and report feedback

Data lives in the project's `.data` folder by default. Deleting/replacing it can remove datasets and sessions. Keep the old project version plus its data when upgrading. Save important checkpoints and export them, but remember JSON export alone has no user-facing restore-import workflow.

For a simple local backup, stop the server you own and copy the entire `.data` directory with the matching project version. Do not take an arbitrary live SQLite file copy while writes are occurring.

Use [BETA_FEEDBACK_TEMPLATE.md](BETA_FEEDBACK_TEMPLATE.md). For each issue include:

- Mac model/chip, macOS, browser, Python and Node versions.
- Release/package name, dataset fingerprint, pair and UTC clock.
- Steps, expected result, actual result and whether it repeats.
- Optional redacted screenshot/export; avoid private journal content and credentials.

Also record usability feedback: what you could not find, what a label seemed to mean, when you needed help, and whether you understood why a trade was accepted/rejected. Profitable practice trades do not by themselves mean the app is correct, and losing trades do not by themselves mean it is broken.

Your testing results will inform P16-B acceptance and subsequent UI priorities. **This document is a guide, not evidence that those manual tests passed.**
