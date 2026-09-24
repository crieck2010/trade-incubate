"""Tests: ledger round-trip, digest rendering, demo arc."""

from trade_incubate.demo import run_demo
from trade_incubate.digest import build_digest, render_digest
from trade_incubate.ledger import IncubationLedger


# --------------------------------------------------------------- ledger

def test_ledger_round_trip(tmp_path):
    path = str(tmp_path / "inc.jsonl")
    led = IncubationLedger(path)
    led.record_day({"day": 1, "equity": 100_000.0, "trades": [{"pnl": 10.0}]})
    led.record_day({"day": 2, "equity": 100_010.0, "trades": []})
    assert led.equity_curve() == [100_000.0, 100_010.0]
    assert led.closed_trades() == [{"pnl": 10.0}]
    assert led.last()["day"] == 2

    led2 = IncubationLedger(path)  # reload from disk
    assert len(led2.days()) == 2
    assert led2.last()["equity"] == 100_010.0


def test_ledger_memory_only():
    led = IncubationLedger()
    assert led.last() is None
    led.record_day({"day": 1, "equity": 1.0})
    assert led.last()["schema_version"] == 1


# --------------------------------------------------------------- digest

def test_digest_build_and_render():
    d = build_digest(strategy="s", day=5, stage="WARMUP", equity=101_000.0,
                     start_equity=100_000.0, day_pnl=200.0,
                     positions=[{"symbol": "AAA", "qty": 10, "unrealized": 50.0}],
                     conviction=55.0, drift="OK", pending_approvals=2,
                     paused=False)
    assert d["schema_version"] == 1
    assert d["inception_pct"] == 1.0
    text = render_digest(d)
    assert "day 5/63" in text and "AAA" in text and "drift: OK" in text
    assert "PAUSED" not in text


def test_digest_paused_shows_kill():
    d = build_digest(strategy="s", day=61, stage="PAUSED", equity=99_000.0,
                     start_equity=100_000.0, day_pnl=-500.0, positions=[],
                     conviction=20.0, drift="VIOLATION", pending_approvals=0,
                     paused=True,
                     kill_trips=[{"day": 61, "condition": "drift_violation",
                                  "detail": "x"}])
    text = render_digest(d)
    assert "PAUSED" in text and "drift_violation" in text


def test_digest_watch_line():
    d = build_digest(strategy="s", day=45, stage="GRADUATION_REVIEW",
                     equity=100_000.0, start_equity=100_000.0, day_pnl=0.0,
                     positions=[], conviction=50.0, drift="WATCH",
                     pending_approvals=0, paused=False)
    assert "WATCH" in render_digest(d)


# ----------------------------------------------------------------- demo

def test_demo_deterministic():
    a, b = run_demo(seed=7), run_demo(seed=7)
    assert a["final_equity"] == b["final_equity"]
    assert a["drift_history"] == b["drift_history"]
    assert a["paused_day"] == b["paused_day"]


def test_demo_arc_detects_degradation_and_pauses():
    arc = run_demo(seed=7)
    assert arc["paused"] is True
    assert arc["paused_day"] is not None and arc["paused_day"] > 40
    hist = arc["drift_history"]
    assert hist[39] == "OK"            # day 40: still healthy
    assert "WATCH" in hist and hist[-1] == "VIOLATION"
    assert any(k["condition"] == "drift_violation" for k in arc["kill_trips"])
    assert arc["digest_text"]  # the phone digest renders the arc
