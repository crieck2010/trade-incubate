# Changelog

## v0.1.0 — 2026-09-24

Initial release: the paper-trading incubation program (step 3 of the path
to live trading).

- `program.py`: 63-day stage machine (WARMUP 1–10, OBSERVATION 11–40,
  GRADUATION_REVIEW 41–63), graduation criteria, kill conditions, daily
  `evaluate()` verdicts.
- `drift.py`: model-drift detection vs ValidationReport expectations —
  Sharpe with Lo (2002) standard-error bands, win rate, payoff, drawdown,
  trade frequency; OK / WATCH / VIOLATION.
- `ledger.py`: append-only JSONL track-record store, independent of
  trade-paper's SQLite ledger.
- `digest.py`: 60-second phone-readable daily digest (plain data + text).
- `runner.py`: scheduled daily cycle — regime → signals → fractional-Kelly
  sizing (trade-risk) → approval queue → trade-paper FakeBroker;
  dry-run default.
- `adapters.py`: lazy, fail-soft bridges to trade-swing, trade-regime,
  trade-risk, trade-paper, trade-agents.
- `demo.py`: seeded 63-day arc — healthy, then planted degradation →
  WATCH → VIOLATION → program pauses.
- Full CLI, presets, docs (ARCHITECTURE, METHODOLOGY, INCUBATION runbook).
