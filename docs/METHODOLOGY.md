# METHODOLOGY — trade-incubate

How the quarter is judged, and why the numbers are what they are.

## The 63-day quarter

63 trading days ≈ one calendar quarter. Long enough for a daily-bar
strategy to accumulate evidence, short enough that a broken strategy
doesn't burn a year. It is a *compromise*, stated plainly: 63 days will
not capture a full market cycle, and strategies with low trade frequency
may barely clear the minimum sample.

## The 20-trade minimum

With n closed trades, the standard error of the win rate is
`sqrt(p(1-p)/n)`. At p = 0.5 and n = 20, SE ≈ 11% — wide, but bounded.
Below ~20 trades the drift bands are so wide the detector can say
nothing at all, and graduation would be granted on noise. 20 is the
floor at which "the strategy traded enough to be judged" becomes
defensible. It is a convention, not a theorem.

## Graduation criteria (defaults)

- **Sharpe within tolerance** (paper ≥ backtest − 0.75): paper almost
  always underperforms backtest (costs, slippage, the optimizer's
  curse). The tolerance accepts normal degradation while failing a
  strategy whose edge evaporated.
- **Drawdown ≤ 1.25× backtest max DD**: drawdowns are the noisiest
  statistic in finance; 1.25× allows bad luck without allowing a
  regime the backtest never saw.
- **≥ 20 closed trades**: the sample-size floor above.
- **No kill trips, no drift VIOLATION**: a strategy that needed
  emergency stops does not graduate, even if the numbers recovered.

## Kill conditions

- **Drawdown > 1.5× backtest max DD → pause.** The backtest's worst
  case, exceeded by half again, means the market is doing something the
  backtest never contained. Pause first, investigate, resume only by
  human hand.
- **Drift VIOLATION → pause.** The detector's 3-SE bands are wide by
  design; breaching them means the track record is statistically
  distinguishable from the backtest. That is the definition of "the
  model broke."

## Drift bands

Each metric is compared with an approximate sampling band around the
backtest value: within 2 SE → OK, 2–3 SE → WATCH, beyond → VIOLATION.

- *Sharpe*: SE from Lo (2002), `sqrt((1 + S²/2)/N)` on N daily returns,
  annualized. With N = 63 the band is roughly ±0.35 around a Sharpe of
  1 — honest about how little 63 days prove.
- *Win rate*: binomial SE around the backtest rate.
- *Payoff*: ±50% of expected, scaled by `1/sqrt(n)` — deliberately
  humble; payoff is the noisiest trade-level stat. Ungraded below 5
  trades, undefined (not zero) with no losses yet.
- *Drawdown*: one-sided ratio bands (1.25×/1.5×). A *smaller* paper
  drawdown is never drift — luck in your favor is not a model break.
- *Trade frequency*: halved pace → WATCH, quarter pace → VIOLATION. A
  strategy that stops trading is telling you something.

Early in the quarter the bands are wide and the detector mostly says
OK — that is correct behavior, and the report says "not enough data"
instead of pretending otherwise.

## Fractional Kelly sizing

`f = fraction · (p − (1−p)/payoff)`, capped. p and payoff come from the
strategy's ValidationReport — the backtest's win rate and avg-win /
avg-loss. Half-Kelly (fraction 0.5) with a 25% cap is the default:
full Kelly maximizes log-growth but assumes the edge estimates are
exact; they never are, so we bet half and cap the worst case. Quantity
= equity · f / price. Non-positive edge → zero size, never a short.

The sizing inputs are *backtest* estimates, which are optimistic. The
drift detector exists precisely because these estimates decay.

## Stage sizing

Warmup trades at half size (days 1–10). Rationale: the first days of
any live or paper deployment are when integration bugs, not the
strategy, lose money. Half size bounds the cost of being wrong about
the plumbing.
