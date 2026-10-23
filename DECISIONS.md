# Decisions log

One line per ambiguous choice; the more conservative option wins.

- 0.1: `data/` is deliberately **not** ignored — the 39 raw apartment CSVs are tracked project inputs and the rules forbid deleting them. `.gitignore` only covers generated artifacts and secrets.
- 0.1: `.env.example` stays un-ignored (`!.env.example`) so configuration can be documented without tracking real secrets.
