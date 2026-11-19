# Unified analysis UI (P07)

The active renderer is `frontend/src/components/AnalysisChart.tsx`. It consumes canonical contract findings and overlay geometry; it performs no structure, zone or divergence detection. The previous TradingChart component remains as inactive upstream reference code.

Price and RSI are panes of one Lightweight Charts instance and share its native time scale. Contract 1.4.0 adds an overlay pane discriminator (default price); RSI lines accept values from 0 through 100 while price geometry remains positive. Backend S/R clusters now have findings and level overlays; divergence findings share price/RSI geometry and evidence IDs.

Category buttons toggle structure, supply/demand, S/R, BOS/CHoCH, FVG, order blocks and divergence; EMA has a separate control. Selecting a finding in the list or chart enables its category, highlights its geometry yellow and focuses its time span. S/R selection fits the entire snapshot. Fit history restores the full chart range. Evidence details show canonical IDs, source/calculation versions and availability times.

Dataset, pair, timeframe and replay changes clear the old result; aborted analysis responses cannot overwrite a newer selection. Confirmed historical events remain separate from retrospective snapshot annotations. Snapshot computations retain p05-snapshot-v1 because detection semantics have not changed.

CSV file upload and optional small-text CSV import share the same validated endpoint. JSON file/paste imports create a pinned local archive; saved archives can be selected by pair. No live provider is connected. Paste is intended for small fixtures, with the existing server/client upload limits still enforced.

Known limits: dense overlays should be filtered on small screens; chart annotations remain retrospective, not tradable causal signals. Browser verification covered CSV file chooser and JSON paste, not the native JSON chooser. No automated cross-browser suite or large-data rendering benchmark was added. Source inventories from earlier phases remain historical provenance, not current file hashes.
