# INCUBATION — the quarter program runbook

The human's operating manual for running a strategy through its paper
quarter. Week by week, day by day.

## Before day 1

1. The strategy has a **ValidationReport** (trade-swing `validate`) with
   no FAIL gates. A strategy that failed validation does not get a
   quarter — it goes back to research.
2. Pick a preset: `conservative` (unproven strategy), `balanced`
   (clean validation pass), `aggressive` (long paper history elsewhere).
3. `trade-incubate start --strategy my-strat --preset balanced
   --backtest-sharpe 1.2 --backtest-dd 0.06` prints the program card.
   Keep it: it is the contract.

## Every trading day (the 60-second routine)

1. The runner executes the daily cycle (schedule it: cron, or the
   trade-paper runner's slot). Dry-run stays on until *you* decide the
   plumbing is trusted — dry-run still records the full track record.
2. Read the digest on your phone. It tells you: equity and P&L,
   positions, regime conviction, drift status, pending approvals,
   and whether anything is paused.
3. Clear the approval queue (trade-paper `approvals`). In supervised
   mode nothing trades without your tap.

That's the whole job. The program watches the statistics; you watch
the program.

## Week by week

- **Days 1–10 (WARMUP).** Half size. Expect drift OK — the bands are
  wide and there is little data. You are validating *plumbing*: fills
  record correctly, the ledger grows, the digest arrives.
- **Days 11–40 (OBSERVATION).** Full size. The drift detector starts
  having opinions. An early WATCH usually means "not enough data,"
  not "broken." A WATCH that persists across two weeks deserves a
  look at *which* metric is off (the digest details say).
- **Days 41–63 (GRADUATION_REVIEW).** Run `trade-incubate graduate`
  any day; it is meaningful at day 63. All five criteria must pass.

## When the program pauses

A kill trip (drawdown breach or drift VIOLATION) pauses the program.
This is the system working. Do:

1. Read the kill detail in the digest — which condition, which day,
   how far beyond the line.
2. Decide: was it the strategy or the world? (A vol spike that broke
   every model is not the strategy's fault — but it still doesn't
   graduate on that quarter.)
3. Either `resume` (human action, recorded) or retire the strategy.

Never auto-resume. The pause exists because something happened that
the backtest did not contain; resuming without understanding it is
how small losses become large ones.

## Graduation

`trade-incubate graduate` at day 63. Five criteria (see METHODOLOGY.md).
If it graduates: the strategy earned *consideration* for capital — not
capital itself. Allocation is a separate decision with its own sizing
(Kelly from the *paper* stats now, not the backtest's).

If it doesn't graduate: the criteria say exactly which one failed.
Common outcomes:

- Failed on trades (< 20): the strategy trades too rarely for a
  63-day quarter. Either extend the program or accept lower statistical
  confidence explicitly.
- Failed on Sharpe tolerance: the edge didn't survive contact with
  paper. Back to research.
- Failed on drawdown multiple: the strategy met a regime its backtest
  never saw. Valuable information — keep the track record.

## Retirement

A strategy is retired, not tweaked, when: it fails graduation twice,
it trips the same kill condition twice, or its drift verdict sits at
WATCH for a full quarter without resolving. Tweaking parameters to
make a failed incubation pass is overfitting with extra steps.

## Ledger rotation

One JSONL file per strategy per quarter:
`incubation-<strategy>-<YYYY>Q<n>.jsonl`. The ledger is append-only;
never edit it. If you resume after a pause, the pause and the resume
are both in the record.
