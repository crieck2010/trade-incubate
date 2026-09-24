# ARCHITECTURE — trade-incubate

The paper-trading incubation program: step 3 of the path to live trading.
It sits *above* trade-paper's execution layer and *below* the human.

```
trade-swing (strategy + ValidationReport)
      │  expectations
      ▼
┌─────────────┐   conviction   ┌──────────────┐
│ trade-regime │──────────────▶│  INCUBATE    │
└─────────────┘                │  program.py  │── evaluate() ──▶ verdict
      │  KellySizer            │  (stages,    │
┌─────────────┐                │   graduation,│
│ trade-risk  │──────────────▶│   kill cond.)│
└─────────────┘                └──────┬───────┘
      │ paper-only                    │ record_day()
┌─────────────┐                       ▼
│ trade-paper │                ┌──────────────┐
│ (FakeBroker)│◀───────────────│ runner.py    │── dry-run default
└─────────────┘   execute      │ (daily cycle)│
                               └──────┬───────┘
                                      │ drift.py compares
                                      ▼ track record vs
                               ValidationReport expectations
                                      │
                                      ▼
                               digest.py ──▶ the human (60s, on a phone)
                                      │
                               pm_brief ──▶ trade-agents (optional)
```

## Layering rules

- **Program over execution.** `program.py` never touches a broker. It
  consumes stats and emits verdicts. The runner is the only thing that
  wires verdicts to actions, and it defaults to dry-run.
- **Paper only, structurally.** `adapters.execute_paper` constructs
  `FakeBroker` and nothing else. There is no code path to a live broker
  in this repo — not a flag, not a TODO. Adding one would be a new
  module and a human decision, never a config flip.
- **Ledger independence.** The incubation ledger (JSONL: one line per
  day) is separate from trade-paper's SQLite audit ledger. The first is
  the *program* record (stages, conviction, drift); the second is the
  *execution* record (orders, fills). They reconcile by date.
- **Plain data everywhere.** Day records, verdicts, digests, drift
  reports are all JSON-serializable dicts with `schema_version: 1`.
- **Lazy siblings.** Every sibling import lives inside a function behind
  try/except ImportError. The package imports and tests clean with zero
  siblings installed; missing engines degrade to loud notes, never
  silent wrong answers.

## The daily cycle (runner.py)

```
advance day → conviction → expectations → signals → Kelly size
    → regime gate → approval queue → (dry-run | execute)
    → drift check → program.evaluate → ledger.record_day → digest
```

The regime gate: conviction below `regime_min_conviction` blocks *new
entries*; existing positions are managed, never force-closed by the
gate (exits are the strategy's job).

## Scaling

- `program.evaluate`, `drift.compare`, `digest.build_digest` are pure
  functions — trivially parallelizable, no shared state.
- The ledger is append-only JSONL: one file per strategy per quarter is
  the expected deployment (rotation documented in INCUBATION.md).
- The runner is single-process and single-strategy by design. Running
  N strategies means N program instances; they share nothing, which is
  the point — incubation verdicts must be independent per strategy.

## Threading

None. The runner is a scheduled single-threaded cycle (cron / scheduler
invokes `run_day` once per trading day). There is no background work,
no locks, no shared mutable state beyond the ledger file.
