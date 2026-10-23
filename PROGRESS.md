# Progress log

One entry per iteration: date, item id, change, evidence, numbers.

## 2026-10-23 — 0.1 Root .gitignore; untrack generated artifacts

- Added root `.gitignore` covering Python caches, `node_modules/`, `dist/`, `.env`, OS files, and test/coverage output.
- Removed from the Git index (working-tree files kept): `frontend/node_modules/` (2,389 files), `.DS_Store`, `backend/__pycache__/main.cpython-313.pyc`.
- Evidence: `git ls-files` 2,466 → 75 tracked files; `git status --short` no longer lists `node_modules`, `.DS_Store`, or `__pycache__`; the files still exist on disk; `git check-ignore -v` reports the new rules.
- Commit: `0.1: add root gitignore and untrack generated artifacts`.
