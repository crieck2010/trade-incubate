"""Tests: runner dry-run, regime gate, adapters fail-soft, Kelly integration."""

import pytest

from trade_incubate import adapters
from trade_incubate.ledger import IncubationLedger
from trade_incubate.program import IncubationProgram
from trade_incubate.runner import run_day, DayConfig


def make_prog():
    return IncubationProgram("swing-trend",
                             {"sharpe": 1.2, "max_drawdown": 0.06,
                              "n_trades": 500})


# --------------------------------------------------------------- runner

def test_runner_dry_run_deterministic(monkeypatch):
    monkeypatch.setattr(adapters, "get_conviction",
                        lambda seed=7: (55.0, "test"))
    cfg = DayConfig(dry_run=True)
    r1 = run_day(make_prog(), IncubationLedger(), cfg)
    r2 = run_day(make_prog(), IncubationLedger(), cfg)
    assert r1["dry_run"] is True
    assert r1["verdict"] == r2["verdict"]
    assert r1["digest"] == r2["digest"]
    assert any("dry-run" in n for n in r1["notes"])


def test_runner_regime_gate_blocks_entries(monkeypatch):
    monkeypatch.setattr(adapters, "get_conviction",
                        lambda seed=7: (10.0, "test"))  # below min 30
    r = run_day(make_prog(), IncubationLedger(), DayConfig(dry_run=True))
    assert r["verdict"]["new_entries_allowed"] is False
    assert any("blocked" in n for n in r["notes"])


def test_runner_missing_conviction_blocks_when_required(monkeypatch):
    monkeypatch.setattr(adapters, "get_conviction",
                        lambda seed=7: (None, "trade-regime not installed"))
    cfg = DayConfig(dry_run=True, require_conviction=True)
    r = run_day(make_prog(), IncubationLedger(), cfg)
    assert r["verdict"]["new_entries_allowed"] is False


def test_runner_missing_conviction_proceeds_loudly_by_default(monkeypatch):
    monkeypatch.setattr(adapters, "get_conviction",
                        lambda seed=7: (None, "trade-regime not installed"))
    r = run_day(make_prog(), IncubationLedger(), DayConfig(dry_run=True))
    assert r["verdict"]["new_entries_allowed"] is True  # None conviction
    assert any("conviction" in n for n in r["notes"])


def test_runner_records_day_in_ledger(monkeypatch):
    monkeypatch.setattr(adapters, "get_conviction",
                        lambda seed=7: (55.0, "test"))
    led = IncubationLedger()
    run_day(make_prog(), led, DayConfig(dry_run=True))
    assert len(led.days()) == 1
    assert led.days()[0]["schema_version"] == 1


# -------------------------------------------------------------- adapters

def test_adapters_fail_soft_without_siblings(monkeypatch):
    monkeypatch.setattr(adapters, "_optional", lambda name: None)
    report, note = adapters.get_validation_report()
    assert report is None and "not installed" in note
    conv, note = adapters.get_conviction()
    assert conv is None and "not installed" in note
    sizer, note = adapters.get_sizer(0.5, 1.5)
    assert sizer is None and "not installed" in note
    fills, note = adapters.execute_paper([], {})
    assert fills is None and "not installed" in note
    brief, note = adapters.pm_brief({})
    assert brief is None and "not installed" in note


def test_kelly_sizer_via_real_trade_risk_api():
    """Fractional Kelly through the real trade-risk API (skips if absent)."""
    trade_risk = pytest.importorskip("trade_risk.sizers")
    sizer_info, note = adapters.get_sizer(0.6, 2.0)
    assert note == "ok"
    sizer, ctx_factory = sizer_info
    assert sizer.name == "kelly"
    ctx = ctx_factory(equity=100_000.0, price=100.0,
                      win_prob=0.6, payoff=2.0)
    # f = 0.5 * (0.6 - 0.4/2.0) = 0.2 -> qty = 100000*0.2/100 = 200
    assert sizer.quantity(ctx) == pytest.approx(200.0)
    # non-positive edge -> zero size, never negative
    ctx2 = ctx_factory(equity=100_000.0, price=100.0,
                       win_prob=0.3, payoff=1.5)  # edge = -0.167
    assert sizer.quantity(ctx2) == 0.0


def test_execute_paper_via_real_fake_broker():
    """Paper execution through trade-paper's FakeBroker (skips if absent)."""
    pytest.importorskip("trade_paper.brokers")
    fills, note = adapters.execute_paper(
        [{"symbol": "AAA", "side": "BUY", "quantity": 10.0}],
        {"AAA": 50.0}, equity=100_000.0)
    assert note == "ok"
    assert len(fills) == 1 and fills[0]["symbol"] == "AAA"
