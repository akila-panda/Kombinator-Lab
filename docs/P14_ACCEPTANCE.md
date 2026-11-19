# P14 saved sessions and journal

P14-A/B complete, 16 November 2026. P15 not started.

Storage: .data/sessions.sqlite3, schema version 1. Each Save checkpoint writes a new immutable UUID record atomically: label, creation time, dataset fingerprint, request/settings/start/clock/commands, execution version, contract version, backend calculation-source hash, complete account/ledger, replay analysis snapshot and order-linked entry/exit/review notes. No overwrite/delete API. List shows latest 100 checkpoints. Notes limited to 200, 4,000 characters each; order references are validated.

POST /api/sessions saves server-recomputed evidence. GET /api/sessions/{id} validates versions, dataset availability and exact recalculated account/replay equality before resume. Unknown dataset is rejected, incompatible calculation returns 409. GET /api/sessions/{id}/export downloads the original complete JSON, including incompatible checkpoints for review. Backend source hash is deliberately conservative: any backend Python change requires treating old checkpoints as review-only unless a future explicit migration is implemented. No silent migration.

UI: save named checkpoints, select/resume while no active session, append entry/exit/review notes and export JSON. Resume is paused. Existing trading tables and snapshot evidence provide review. Notes/advances since last Save checkpoint are unsaved; there is no autosave. New session discards only active in-memory work, leaving saved checkpoints intact. Checkpoint snapshots represent analysis at the saved clock, not an invented per-trade analysis history.

Verification: 221 tests passed in 35.81s, dependency check, TypeScript/Vite build and existing HTTP smoke. New persistence test opens a fresh store instance, restores exact account/replay, checks export ledger, rejects unknown note targets and incompatible execution version while preserving export. TestClient additionally restored/exported the real browser checkpoint, comparing full JSON and download headers. Browser saved a filled EUR/USD trade plus note, reloaded, resumed at 2024-01-05 12:08 with balance 9999.96, and retained the note and position. Screenshot screenshots/p14-journal.png. No duplicate fill on resume.

Preview 8766 running with session APIs (tool session 30354). SQLite/raw market data excluded from source package. Next P15 only after explicit Proceed.
