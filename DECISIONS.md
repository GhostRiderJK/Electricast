# Decisions log

One line per ambiguous choice; the more conservative option wins.

- 0.1: `data/` is deliberately **not** ignored — the 39 raw apartment CSVs are tracked project inputs and the rules forbid deleting them. `.gitignore` only covers generated artifacts and secrets.
- 0.1: `.env.example` stays un-ignored (`!.env.example`) so configuration can be documented without tracking real secrets.
- 0.2: `torch` is pinned as `2.14.1` without the local `+cpu` suffix; wheel variants are platform-specific and the plain pin resolves to the installed version on this host.
- 0.2: Docker base is the exact `python:3.12.10-slim` tag to match local Python 3.12.10. The image was not built because no Python image was cached and network use is limited to pip/npm.
