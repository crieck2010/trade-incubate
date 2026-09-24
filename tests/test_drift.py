"""Tests: drift statistics and verdicts."""

import math
import random

import pytest

from trade_incubate.drift import paper_stats, drift_verdict, compare
from trade_incubate.demo import EXPECTATIONS


def healthy_series(seed=11, n=40):
    rng = random.Random(seed)
    eq = [100_000.0]
    trades = []
    for _ in range(n):
        e = eq[-1]
        e = e * (1.0 + rng.gauss(0.0008, 0.011))
        if rng.random() < 0.9:
            pnl = 240.0 if rng.random() < 0.45 else -150.0
            trades.append({"pnl": pnl})
            e += pnl
        eq.append(e)
    return eq, trades


# ---------------------------------------------------------- paper_stats

def test_paper_stats_hand_computed():
    eq = [100.0, 110.0, 115.5]          # +10%, +5%
    trades = [{"pnl": 20.0}, {"pnl": -10.0}, {"pnl": 30.0}]
    s = paper_stats(eq, trades)
    assert s["n_trades"] == 3
    assert s["win_rate"] == pytest.approx(2 / 3)
    assert s["avg_win"] == pytest.approx(25.0)
    assert s["avg_loss"] == pytest.approx(10.0)
    assert s["payoff"] == pytest.approx(2.5)
    # positive mean, nonzero vol: positive Sharpe, finite SE
    assert s["sharpe"] > 0 and math.isfinite(s["sharpe_se"])
    # peak 115.5, no dip -> no drawdown
    assert s["max_drawdown"] == pytest.approx(0.0)


def test_paper_stats_drawdown():
    s = paper_stats([100.0, 120.0, 90.0, 95.0], [])
    assert s["max_drawdown"] == pytest.approx(30.0 / 120.0)


def test_paper_stats_empty():
    s = paper_stats([], [])
    assert s["n_trades"] == 0 and s["sharpe"] == 0.0
    assert s["max_drawdown"] == 0.0


def test_paper_stats_zero_volatility():
    s = paper_stats([100.0, 100.0, 100.0], [])
    assert s["sharpe"] == 0.0  # sd = 0 -> defined as 0, not inf


# ------------------------------------------------------------- verdicts

def test_matching_series_is_ok():
    eq, trades = healthy_series()
    r = compare(EXPECTATIONS, eq, trades)
    assert r["schema_version"] == 1
    assert r["verdict"] in ("OK", "WATCH")  # bands are wide at n=40


def test_collapsed_win_rate_violates():
    eq, trades = healthy_series()
    # append 40 straight losses: win rate craters well past 3 SE
    bad = trades + [{"pnl": -200.0}] * 40
    eq2 = eq + [eq[-1] - 200.0 * i for i in range(1, 11)]
    r = compare(EXPECTATIONS, eq2, bad)
    assert r["verdict"] == "VIOLATION"
    assert r["grades"]["win_rate"] == "VIOLATION"


def test_tiny_sample_says_ok_with_note():
    r = compare(EXPECTATIONS, [100_000.0, 100_500.0], [{"pnl": 500.0}])
    assert r["verdict"] == "OK"
    assert any("too few" in d or "no data" in d for d in r["details"])


def test_no_losses_payoff_not_zero():
    eq, trades = healthy_series()
    wins_only = [t for t in trades if t["pnl"] > 0][:8]
    r = compare(EXPECTATIONS, eq, wins_only)
    assert "undefined" in " ".join(r["details"])
    assert r["grades"]["payoff"] == "OK"


def test_better_drawdown_is_never_drift():
    eq = [100_000.0 * (1.001 ** i) for i in range(40)]  # monotonic up
    trades = [{"pnl": 100.0}] * 30
    r = compare(EXPECTATIONS, eq, trades)
    assert r["grades"]["max_drawdown"] == "OK"


def test_trade_frequency_halved_is_watch():
    eq, _ = healthy_series()
    few = [{"pnl": 240.0 if i % 2 else -150.0} for i in range(16)]  # 0.4/day
    r = compare(EXPECTATIONS, eq, few)
    assert r["grades"]["trade_frequency"] == "WATCH"


def test_trade_frequency_quartered_is_violation():
    eq, _ = healthy_series()
    few = [{"pnl": 240.0 if i % 2 else -150.0} for i in range(8)]  # 0.2/day
    r = compare(EXPECTATIONS, eq, few)
    assert r["grades"]["trade_frequency"] == "VIOLATION"


def test_drawdown_ratio_bands():
    base = {"sharpe": 1.2, "win_rate": 0.45, "payoff": 1.6,
            "max_drawdown": 0.06, "trades_per_day": 0.9}
    eq = [100_000.0 * (1.001 ** i) for i in range(40)]
    trades = [{"pnl": 100.0}] * 30
    paper = paper_stats([100_000.0, 92_000.0, 100_000.0], trades)  # 8% DD
    r = drift_verdict({**base}, paper)
    assert r["grades"]["max_drawdown"] == "WATCH"  # 1.33x
    paper = paper_stats([100_000.0, 88_000.0, 100_000.0], trades)  # 12% DD
    r = drift_verdict({**base}, paper)
    assert r["grades"]["max_drawdown"] == "VIOLATION"  # 2x
