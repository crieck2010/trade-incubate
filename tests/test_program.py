"""Tests: program stages, graduation criteria, kill conditions."""

import pytest

from trade_incubate.program import (
    IncubationProgram, ProgramConfig, Stage, stage_for,
    STAGE_SIZE_MULTIPLIER,
)


def make_program(**kw):
    bt = {"sharpe": 1.2, "max_drawdown": 0.06, "n_trades": 500}
    return IncubationProgram(strategy_name="test", backtest=bt, **kw)


# ------------------------------------------------------------ stages

@pytest.mark.parametrize("day,expected", [
    (1, Stage.WARMUP), (10, Stage.WARMUP),
    (11, Stage.OBSERVATION), (40, Stage.OBSERVATION),
    (41, Stage.GRADUATION_REVIEW), (63, Stage.GRADUATION_REVIEW),
    (0, Stage.WARMUP), (100, Stage.GRADUATION_REVIEW),
])
def test_stage_boundaries(day, expected):
    assert stage_for(day) == expected


def test_advance_walks_stages():
    p = make_program()
    for _ in range(10):
        p.advance()
    assert p.day == 10 and p.state == Stage.WARMUP
    p.advance()
    assert p.day == 11 and p.state == Stage.OBSERVATION
    for _ in range(29):
        p.advance()
    assert p.state == Stage.OBSERVATION
    p.advance()
    assert p.state == Stage.GRADUATION_REVIEW


def test_size_multiplier_by_stage():
    p = make_program()
    assert p.size_multiplier() == 0.5          # warmup
    p.day, p.state = 20, Stage.OBSERVATION
    assert p.size_multiplier() == 1.0
    p.day, p.state = 50, Stage.GRADUATION_REVIEW
    assert p.size_multiplier() == 1.0


def test_paused_sticks_on_advance():
    p = make_program()
    p.state = Stage.PAUSED
    p.advance()
    assert p.state == Stage.PAUSED and p.day == 0


# ------------------------------------------------------ kill conditions

def test_kill_drawdown_breach():
    p = make_program()
    p.day = 30
    # backtest DD 6%; paper DD 10% = 1.67x > 1.5x kill multiple
    tripped = p.check_kill({"max_drawdown": 0.10}, "OK")
    assert len(tripped) == 1 and tripped[0]["condition"] == "drawdown_breach"
    assert p.state == Stage.PAUSED


def test_kill_drawdown_within_band():
    p = make_program()
    p.day = 30
    tripped = p.check_kill({"max_drawdown": 0.08}, "OK")  # 1.33x < 1.5x
    assert tripped == [] and p.state == Stage.WARMUP


def test_kill_drift_violation():
    p = make_program()
    p.day = 30
    tripped = p.check_kill({"max_drawdown": 0.02}, "VIOLATION")
    assert any(t["condition"] == "drift_violation" for t in tripped)
    assert p.state == Stage.PAUSED


def test_kill_drift_watch_does_not_pause():
    p = make_program()
    p.day = 30
    assert p.check_kill({"max_drawdown": 0.02}, "WATCH") == []
    assert p.state == Stage.WARMUP


def test_resume_is_human_action():
    p = make_program()
    p.day = 30
    p.check_kill({"max_drawdown": 0.10}, "OK")
    assert p.state == Stage.PAUSED
    assert p.resume() == Stage.OBSERVATION
    assert p.kill_trips  # the trip stays on the record


# --------------------------------------------------------- graduation

def good_stats():
    return {"sharpe": 1.1, "max_drawdown": 0.05, "n_trades": 40}


def test_graduation_all_pass():
    p = make_program()
    p.day = 63
    result = p.graduation_check(good_stats())
    assert result["graduated"] is True
    assert all(c["pass"] for c in result["criteria"].values())


def test_graduation_sharpe_fail():
    p = make_program()
    s = good_stats(); s["sharpe"] = 0.2  # 1.2 - 0.2 = 1.0 > 0.75 tolerance
    result = p.graduation_check(s)
    assert result["graduated"] is False
    assert result["criteria"]["sharpe_within_tolerance"]["pass"] is False


def test_graduation_drawdown_fail():
    p = make_program()
    s = good_stats(); s["max_drawdown"] = 0.10  # > 1.25 * 0.06 = 0.075
    result = p.graduation_check(s)
    assert result["criteria"]["drawdown_within_multiple"]["pass"] is False


def test_graduation_trades_fail():
    p = make_program()
    s = good_stats(); s["n_trades"] = 12
    result = p.graduation_check(s)
    assert result["criteria"]["minimum_trades"]["pass"] is False


def test_graduation_kill_trip_fails():
    p = make_program()
    p.day = 30
    p.check_kill({"max_drawdown": 0.10}, "OK")
    p.resume()
    p.day = 63
    result = p.graduation_check(good_stats())
    assert result["criteria"]["no_kill_trips"]["pass"] is False
    assert result["graduated"] is False


def test_graduation_drift_violation_fails():
    p = make_program()
    p.day = 63
    p.drift_worst = "VIOLATION"
    result = p.graduation_check(good_stats())
    assert result["criteria"]["no_drift_violation"]["pass"] is False


def test_graduate_sets_state():
    p = make_program()
    p.day = 63
    result = p.graduate(good_stats())
    assert result["graduated"] is True and p.state == Stage.GRADUATED


# ------------------------------------------------------------ evaluate

def test_evaluate_schema_and_gates():
    p = make_program()
    p.day = 20
    v = p.evaluate({"sharpe": 1.0, "max_drawdown": 0.03, "n_trades": 15},
                   "OK", conviction=55.0)
    assert v["schema_version"] == 1
    assert v["stage"] == Stage.WARMUP
    assert v["new_entries_allowed"] is True
    assert v["paused"] is False


def test_evaluate_blocks_entries_at_low_conviction():
    p = make_program()
    p.day = 20
    v = p.evaluate({"sharpe": 1.0, "max_drawdown": 0.03, "n_trades": 15},
                   "OK", conviction=10.0)
    assert v["new_entries_allowed"] is False


def test_evaluate_tracks_drift_worst():
    p = make_program()
    p.day = 20
    p.evaluate({"sharpe": 1.0, "max_drawdown": 0.03, "n_trades": 15},
               "WATCH", conviction=55.0)
    assert p.drift_worst == "WATCH"
    p.evaluate({"sharpe": 1.0, "max_drawdown": 0.03, "n_trades": 15},
               "OK", conviction=55.0)
    assert p.drift_worst == "WATCH"  # worst sticks
