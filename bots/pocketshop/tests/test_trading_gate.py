"""The gate must fail closed. Every test here is a way money could be lost."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from trading_gate import Gate, GateError, evaluate, stake_for  # noqa: E402

FINANCE = {"savings": 1000.0, "restock_balance": 200.0, "next_restock_buy_price": 180.0}
CONFIG = {"savings_floor": 400.0, "trade_max_absolute": 50.0, "trade_max_pct_of_savings": 10}


def test_open_gate_reports_tradable_and_cap():
    g = evaluate(FINANCE, CONFIG)
    assert g.open
    assert g.tradable == 600.0          # 1000 - max(400, 180)
    assert g.max_stake == 50.0          # min(60, 50, 600) -> absolute cap binds


def test_percentage_cap_binds_when_smaller():
    g = evaluate(FINANCE, {**CONFIG, "trade_max_absolute": 500.0})
    assert g.max_stake == 60.0          # 10% of 600


def test_unfunded_restock_disables_trading():
    g = evaluate({**FINANCE, "restock_balance": 100.0}, CONFIG)
    assert not g.open
    assert "restock reserve not funded" in g.reason
    assert g.shortfall == 80.0
    assert g.max_stake == 0.0


def test_restock_price_above_floor_raises_the_reserve():
    # next box costs 700; floor is 400 -> reserve is 700, tradable 300
    g = evaluate({**FINANCE, "restock_balance": 700.0, "next_restock_buy_price": 700.0}, CONFIG)
    assert g.open
    assert g.reserve_required == 700.0
    assert g.tradable == 300.0


def test_savings_at_the_floor_is_closed():
    g = evaluate({**FINANCE, "savings": 400.0}, CONFIG)
    assert not g.open
    assert "ring-fenced floor" in g.reason


def test_losing_streak_halts():
    g = evaluate(FINANCE, {**CONFIG, "losing_streak": 3, "losing_streak_halt": 3})
    assert not g.open
    assert "consecutive losses" in g.reason


def test_unset_floor_refuses_rather_than_defaulting():
    with pytest.raises(GateError, match="savings_floor"):
        evaluate(FINANCE, {"trade_max_absolute": 50.0})


def test_unset_absolute_cap_refuses():
    with pytest.raises(GateError, match="trade_max_absolute"):
        evaluate(FINANCE, {"savings_floor": 400.0})


def test_negative_and_nonnumeric_limits_refuse():
    with pytest.raises(GateError):
        evaluate(FINANCE, {**CONFIG, "savings_floor": -1})
    with pytest.raises(GateError):
        evaluate(FINANCE, {**CONFIG, "trade_max_absolute": "lots"})


def test_percentage_over_hundred_refuses():
    with pytest.raises(GateError):
        evaluate(FINANCE, {**CONFIG, "trade_max_pct_of_savings": 150})


def test_default_percentage_is_ten():
    g = evaluate(FINANCE, {"savings_floor": 400.0, "trade_max_absolute": 500.0})
    assert g.max_stake == 60.0


def test_stake_is_clamped_and_closed_gate_yields_zero():
    g = evaluate(FINANCE, CONFIG)
    assert stake_for(g, 999.0) == 50.0
    assert stake_for(g, 12.5) == 12.5
    closed = evaluate({**FINANCE, "restock_balance": 0.0}, CONFIG)
    assert stake_for(closed, 999.0) == 0.0


def test_stake_can_never_exceed_tradable():
    tiny = evaluate({**FINANCE, "savings": 405.0}, {**CONFIG, "trade_max_absolute": 500.0})
    assert tiny.open
    assert tiny.max_stake <= tiny.tradable
    assert stake_for(tiny, 100.0) <= 5.0


def test_negative_stake_refuses():
    with pytest.raises(GateError):
        stake_for(evaluate(FINANCE, CONFIG), -5.0)


def test_as_dict_is_json_shaped():
    d = evaluate(FINANCE, CONFIG).as_dict()
    assert isinstance(d, dict) and d["open"] is True
    assert all(isinstance(d[k], (int, float, str, bool)) for k in d)
