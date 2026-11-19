"""Every rule in BOT.md's restock section, as an executable check."""
import pathlib
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from restock_math import (  # noqa: E402
    Candidate, Quote, RestockError, assess, compare, should_buy,
)

TODAY = date(2026, 11, 19)
CONFIG = {
    "sales_tax_rate": 0.08,
    "sell_fee_pct": 13.25,
    "sell_fixed_fee": 12.0,
    "ev_realisation_rate": 0.65,
    "min_net_profit": 20.0,
}


def cand(name="Box A", ev=400.0, age=5, quotes=None):
    return Candidate(name, ev, TODAY - timedelta(days=age), quotes or [
        Quote("Amazon", 180.0, 0.0),
        Quote("Walmart", 185.0, 5.0),
    ])


def test_net_accounts_for_fees_shipping_and_tax():
    a = assess(cand(), CONFIG, today=TODAY)
    assert a.eligible
    # realised = 400*.65*(1-.1325) - 12 = 213.55 ; landed = 180*1.08 = 194.40
    assert round(a.net, 2) == 19.15
    assert a.chosen.retailer == "Amazon"
    assert a.buy_price == 180.0


def test_ev_is_never_treated_as_cash():
    full = assess(cand(), {**CONFIG, "ev_realisation_rate": 1.0}, today=TODAY)
    partial = assess(cand(), CONFIG, today=TODAY)
    assert full.net > partial.net


def test_stale_ev_is_refused():
    a = assess(cand(age=31), CONFIG, today=TODAY)
    assert not a.eligible and "stale discovery" in a.reason


def test_ev_at_the_limit_is_allowed():
    assert assess(cand(age=30), CONFIG, today=TODAY).eligible


def test_future_dated_ev_is_refused():
    a = assess(cand(age=-1), CONFIG, today=TODAY)
    assert not a.eligible and "future" in a.reason


def test_low_rated_seller_is_rejected():
    c = cand(quotes=[Quote("Amazon", 180.0), Quote("Shady", 150.0, seller_rating=0.90)])
    a = assess(c, CONFIG, today=TODAY)
    assert a.chosen.retailer == "Amazon"
    assert any("seller rating" in r for r in a.rejected)


def test_out_of_stock_is_rejected():
    c = cand(quotes=[Quote("Amazon", 180.0), Quote("Walmart", 100.0, in_stock=False)])
    a = assess(c, CONFIG, today=TODAY)
    assert a.chosen.retailer == "Amazon"
    assert any("out of stock" in r for r in a.rejected)


def test_deep_discount_is_flagged_not_trusted():
    c = cand(quotes=[Quote("Amazon", 180.0), Quote("Walmart", 182.0), Quote("TooGood", 100.0)])
    a = assess(c, CONFIG, today=TODAY)
    assert a.chosen.retailer == "Amazon"          # not the suspicious 100
    assert any("possibly mispriced" in f for f in a.flagged)


def test_a_deep_outlier_never_becomes_the_buy_price():
    # With two quotes the median is their mean, so the high one stays trusted:
    # the outlier is flagged and shown, never chosen.
    c = cand(quotes=[Quote("A", 200.0), Quote("B", 50.0)])
    a = assess(c, CONFIG, today=TODAY)
    assert a.eligible
    assert a.chosen.retailer == "A"
    assert a.buy_price == 200.0
    assert any("possibly mispriced" in f for f in a.flagged)


def test_identical_quotes_are_not_flagged():
    c = cand(quotes=[Quote("A", 100.0), Quote("B", 100.0), Quote("C", 100.0)])
    a = assess(c, CONFIG, today=TODAY)
    assert a.eligible and not a.flagged


def test_no_usable_quote_means_no_recommendation():
    c = cand(quotes=[Quote("A", 180.0, in_stock=False)])
    assert not assess(c, CONFIG, today=TODAY).eligible


def test_unset_assumptions_refuse():
    for key in ("sales_tax_rate", "sell_fee_pct", "sell_fixed_fee", "ev_realisation_rate"):
        cfg = {k: v for k, v in CONFIG.items() if k != key}
        with pytest.raises(RestockError, match=key):
            assess(cand(), cfg, today=TODAY)


def test_impossible_rates_refuse():
    with pytest.raises(RestockError):
        assess(cand(), {**CONFIG, "ev_realisation_rate": 1.5}, today=TODAY)
    with pytest.raises(RestockError):
        assess(cand(), {**CONFIG, "sell_fee_pct": 150}, today=TODAY)


def test_compare_requires_three_candidates():
    with pytest.raises(RestockError, match="three-candidate"):
        compare([cand("A"), cand("B")], CONFIG, today=TODAY)


def test_compare_ranks_by_realised_net():
    a = cand("Cheap", ev=400.0, quotes=[Quote("Amazon", 160.0), Quote("Walmart", 165.0)])
    b = cand("Mid", ev=400.0, quotes=[Quote("Amazon", 180.0), Quote("Walmart", 185.0)])
    c = cand("Dear", ev=400.0, quotes=[Quote("Amazon", 220.0), Quote("Walmart", 225.0)])
    out = compare([b, c, a], CONFIG, today=TODAY)
    assert out["winner"]["name"] == "Cheap"
    assert [r["name"] for r in out["ranked"]] == ["Cheap", "Mid", "Dear"]


def test_single_retailer_cannot_win():
    # Lone is cheapest but quoted once; the two-retailer rule must beat price.
    lone = cand("Lone", quotes=[Quote("Amazon", 150.0)])
    paired = cand("Paired", quotes=[Quote("Amazon", 160.0), Quote("Walmart", 165.0)])
    dear = cand("Dear", quotes=[Quote("Amazon", 220.0), Quote("Walmart", 225.0)])
    out = compare([lone, paired, dear], CONFIG, today=TODAY)
    assert out["winner"]["name"] == "Paired"
    lone_row = next(r for r in out["ranked"] if r["name"] == "Lone")
    assert "fewer than two retailers" in lone_row["reason"]


def test_profit_floor_is_enforced():
    out = compare([cand("A"), cand("B"), cand("C")], {**CONFIG, "min_net_profit": 500.0}, today=TODAY)
    assert out["winner"] is None
    assert "profit floor" in out["reason"]


def test_buy_trigger_waits_for_the_price():
    w = {"buy_price": 180.0, "retailer": "Amazon", "net": 19.15}
    assert not should_buy(w, 195.0, 1000.0)["buy"]
    assert should_buy(w, 180.0, 1000.0)["buy"]
    assert should_buy(w, 170.0, 1000.0)["buy"]


def test_buy_trigger_respects_the_restock_balance():
    w = {"buy_price": 180.0, "retailer": "Amazon", "net": 19.15}
    out = should_buy(w, 175.0, 100.0)
    assert not out["buy"] and out["shortfall"] == 75.0


def test_buy_trigger_never_places_an_order():
    w = {"buy_price": 180.0, "retailer": "Amazon", "net": 19.15}
    out = should_buy(w, 170.0, 500.0)
    assert out["buy"] and "operator places this order" in out["note"]
    assert "order" in out and "placed" not in out
