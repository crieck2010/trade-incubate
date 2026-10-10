> [!IMPORTANT]
> **Consolidated into [TradeSuite](https://github.com/crieck2010/trade-suite)**  
> This engine has been consolidated into the unified [TradeSuite monorepo](https://github.com/crieck2010/trade-suite). Active development, bug fixes, releases, and unified testing now live in `trade-suite`. This repository is preserved as an archive.

# trade-incubate

The paper-trading incubation program: step 3 of the path to live trading.
A validated strategy earns a disciplined 63-trading-day (~one quarter)
paper run, and the program answers one question continuously — *"is the
strategy behaving like its backtest?"* — through stages, drift detection,
graduation criteria, and kill conditions.

This is the *program layer* above trade-paper's execution layer. Nothing
here trades live; execution routes exclusively through trade-paper's
paper-only guard (FakeBroker in dry-run, which is the default).

Part of the [trade-suite](https://github.com/crieck2010/trade-suite)
algorithmic trading system. It consumes the ValidationReport from
`trade-swing`, conviction from `trade-regime`, fractional-Kelly sizing
from `trade-risk`, execution from `trade-paper`, and briefs `trade-agents`.

## Install

```bash
pip install trade-incubate
# or from source
git clone https://github.com/crieck2010/trade-incubate
cd trade-incubate
pip install -e .
```

Requires Python 3.10+. No third-party dependencies — not even NumPy.

## Quick start

```python
from trade_incubate.demo import run_demo

arc = run_demo(seed=7)   # seeded 63-day quarter: healthy, then degrades
print(arc["paused"], arc["paused_day"])   # True 61 — drift kills it
print(arc["digest_text"])                  # the 60-second phone digest
```

Run one dry-run day of the scheduled cycle:

```python
from trade_incubate.runner import run_day, DayConfig
from trade_incubate.program import IncubationProgram
from trade_incubate.ledger import IncubationLedger

prog = IncubationProgram("swing-trend",
                         {"sharpe": 1.2, "max_drawdown": 0.06, "n_trades": 500})
day = run_day(prog, IncubationLedger(), DayConfig(dry_run=True))
print(day["stage"], day["drift"], day["dry_run"])
```

Drift-check any track record against backtest expectations:

```python
from trade_incubate.drift import compare

result = compare(
    {"sharpe": 1.2, "win_rate": 0.45, "payoff": 1.6,
     "max_drawdown": 0.06, "trades_per_day": 0.9},
    equity_curve, closed_trades)
print(result["verdict"])   # OK | WATCH | VIOLATION
```

CLI:

```bash
trade-incubate demo                    # the seeded 63-day arc
trade-incubate start --preset balanced # print a new program card
trade-incubate digest --ledger incubation.jsonl
trade-incubate drift --ledger incubation.jsonl
trade-incubate graduate --ledger incubation.jsonl
trade-incubate presets
```

See `examples/incubate_example.py` for the full walkthrough, and
`docs/INCUBATION.md` for the human runbook (what you do each day).

## The maths

**What you learn.** Whether a strategy's paper behavior still belongs to
the same distribution as its backtest — before real capital finds out
it doesn't. The quarter produces a verdict (graduate / keep watching /
paused), not just a P&L number.

**Why it matters.** Backtests are optimistic: costs are modeled,
slippage is guessed, and the parameters were chosen on the same data.
Paper trading is where the optimism meets friction. Without a formal
incubation, "it looked good in paper" is a feeling; with one, it's five
checked criteria and a drift detector with stated statistical bands.

**The maths.**

- *Sharpe bands.* The paper Sharpe is compared to the backtest Sharpe
  with its sampling standard error (Lo 2002):
  `SE = √((1 + S²/2)/N)`, annualized. Within 2 SE → OK, 2–3 SE →
  WATCH, beyond → VIOLATION. With N = 63 daily returns the band is
  roughly ±0.35 around a Sharpe of 1 — the detector is honest about
  how little 63 days prove.
- *Win-rate bands.* Binomial SE around the backtest rate:
  `√(p(1−p)/n)` on n closed trades.
- *Drawdown multiples.* Graduation needs paper DD ≤ 1.25× backtest DD;
  the kill fires above 1.5×. One-sided: a *smaller* paper drawdown is
  never drift.
- *Why 63 days and 20 trades.* 63 ≈ one quarter of trading days — long
  enough for evidence, short enough to cut a broken strategy loose.
  20 trades is the floor where the win-rate SE (`√(0.25/20)` ≈ 11%)
  is at least bounded; below it the bands say "can't tell yet."
- *Fractional Kelly.* `f = fraction · (p − (1−p)/payoff)`, capped
  (default half-Kelly, 25% cap). p and payoff come from the strategy's
  ValidationReport. Full Kelly assumes the edge estimates are exact;
  they never are, so we bet half. Non-positive edge → zero size.
- *Stage sizing.* Warmup (days 1–10) trades at half size: the first
  days of any deployment are when plumbing bugs, not the strategy,
  lose money.

**Honest limitations.** Paper fills aren't real fills — no market
impact, no partial fills, no 3 a.m. gap risk in the simulator. 63 days
is short and won't span a full market cycle. With few trades the drift
bands are wide by design, so early detection is weak — the detector
says "not enough data" instead of pretending. A graduated strategy can
still fail live; graduation means "earned consideration for capital,"
not "proven." The Kelly inputs are backtest estimates, hence
optimistic — the drift detector exists because they decay.

## Interop

Stable `schema_version: 1` contracts on day records, verdicts, digests,
and drift reports (see `docs/ARCHITECTURE.md`). Every sibling import
is lazy and fail-soft: the package imports, runs, and tests with zero
siblings installed. The runner degrades loudly (notes on every skipped
step) rather than silently.

| Sibling | Use | If absent |
|---|---|---|
| `trade-swing` | ValidationReport expectations, demo bars, signals | no expectations, no signals — runner records, doesn't trade |
| `trade-regime` | conviction for the new-entry gate | proceeds with a loud note (or blocks, if configured) |
| `trade-risk` | `KellySizer` fractional-Kelly sizing | orders size zero |
| `trade-paper` | `FakeBroker` paper execution | no execution path — dry-run only |
| `trade-agents` | PM briefing hook | digest stays human-read |

## License

MIT — see [LICENSE](LICENSE).
