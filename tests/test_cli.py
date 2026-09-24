"""Tests: CLI commands."""

from trade_incubate.cli import main


def test_cli_demo(capsys):
    assert main(["demo", "--seed", "7"]) == 0
    out = capsys.readouterr().out
    assert "paused=True" in out


def test_cli_demo_json(capsys):
    import json
    assert main(["demo", "--seed", "7", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["paused"] is True


def test_cli_start_and_presets(capsys):
    assert main(["start", "--preset", "conservative"]) == 0
    assert "WARMUP" in capsys.readouterr().out
    assert main(["presets"]) == 0
    assert "conservative" in capsys.readouterr().out


def test_cli_status_empty_ledger(capsys, tmp_path):
    assert main(["status", "--ledger", str(tmp_path / "x.jsonl")]) == 0
    assert "no incubation days" in capsys.readouterr().out


def test_cli_license(capsys):
    import json
    assert main(["license", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["product"] == "trade-incubate"
