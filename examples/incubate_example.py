"""End-to-end incubation walkthrough: program, drift, digest, runner dry-run."""

from trade_incubate.demo import run_demo, EXPECTATIONS
from trade_incubate.digest import render_digest
from trade_incubate.drift import compare
from trade_incubate.ledger import IncubationLedger
from trade_incubate.program import IncubationProgram, ProgramConfig, stage_for
from trade_incubate.runner import run_day, DayConfig, _demo_bars

print("== the 63-day arc ==")
arc = run_demo(seed=7)
print(f"days run: {arc['days_run']}, paused day {arc['paused_day']}, "
      f"final equity ${arc['final_equity']:,.2f}")
print()

print("== drift on a healthy vs degraded record ==")
import random as _random
_rng = _random.Random(11)
rng_eq = [100_000.0]
for _ in range(40):
    rng_eq.append(rng_eq[-1] * (1.0 + _rng.gauss(0.0008, 0.011)))
healthy_trades = [{"pnl": 240.0}] * 18 + [{"pnl": -150.0}] * 22
r = compare(EXPECTATIONS, rng_eq, healthy_trades)
print("healthy-ish 40d:", r["verdict"], "|", "; ".join(r["details"][:2]))
bad_eq = rng_eq + [rng_eq[-1] * (1 - 0.004) ** i for i in range(1, 24)]
bad_trades = healthy_trades + [{"pnl": -210.0}] * 15 + [{"pnl": 180.0}] * 5
r = compare(EXPECTATIONS, bad_eq, bad_trades)
print("degraded 63d:  ", r["verdict"], "|", "; ".join(r["details"][:2]))
print()

print("== dry-run day ==")
prog = IncubationProgram("swing-trend",
                         {"sharpe": 1.2, "max_drawdown": 0.06, "n_trades": 500})
led = IncubationLedger()
day = run_day(prog, led, DayConfig(dry_run=True))
print(f"day {day['day']} [{day['stage']}] drift={day['drift']} "
      f"dry_run={day['dry_run']}")
for n in day["notes"]:
    print("  -", n)
print()
print(render_digest(day["digest"]))
