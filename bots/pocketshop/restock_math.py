"""Which of three sealed boxes is actually the most profitable to buy.

MTGStocks EV is the market value of a box's *contents*, not cash in hand. Bulk
does not sell, fees and shipping are real, and a box sits unsold for weeks. So
this module never treats EV as revenue: it applies an explicit realisation rate
and the operator's own fee assumptions, and refuses when those are unset.

Recommender only. It returns a ranked comparison and a buy price. It never
places an order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

MAX_EV_AGE_DAYS = 30
MIN_SELLER_RATING = 0.95
MISPRICE_UNDER_MEDIAN = 0.15


class RestockError(ValueError):
    """An assumption is missing or a rule is violated; do not recommend."""


@dataclass(frozen=True)
class Quote:
    retailer: str
    price: float
    shipping: float = 0.0
    seller_rating: float = 1.0
    in_stock: bool = True
    url: str = ""

    def landed(self, tax_rate: float) -> float:
        return (self.price + self.shipping) * (1.0 + tax_rate)


@dataclass
class Candidate:
    name: str
    ev: float
    ev_as_of: date
    quotes: list[Quote] = field(default_factory=list)


@dataclass
class Assessment:
    name: str
    eligible: bool
    reason: str
    net: float = 0.0
    buy_price: float = 0.0
    chosen: Quote | None = None
    rejected: list[str] = field(default_factory=list)
    flagged: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "eligible": self.eligible,
            "reason": self.reason,
            "net": round(self.net, 2),
            "buy_price": round(self.buy_price, 2),
            "retailer": self.chosen.retailer if self.chosen else None,
            "rejected": self.rejected,
            "flagged": self.flagged,
        }


def _req(config: dict, key: str) -> float:
    if key not in config or config[key] is None:
        raise RestockError(f"{key} is not set; refusing to guess a money assumption")
    try:
        value = float(config[key])
    except (TypeError, ValueError) as exc:
        raise RestockError(f"{key} must be a number, got {config[key]!r}") from exc
    if value < 0:
        raise RestockError(f"{key} must not be negative, got {value}")
    return value


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def assess(candidate: Candidate, config: dict, *, today: date | None = None) -> Assessment:
    """Score one candidate. `config` must carry the operator's own assumptions."""
    today = today or date.today()
    tax = _req(config, "sales_tax_rate")
    fee_pct = _req(config, "sell_fee_pct")
    fee_fixed = _req(config, "sell_fixed_fee")
    realisation = _req(config, "ev_realisation_rate")
    if realisation > 1:
        raise RestockError(f"ev_realisation_rate must be <= 1, got {realisation}")
    if fee_pct > 100:
        raise RestockError(f"sell_fee_pct must be <= 100, got {fee_pct}")

    if isinstance(candidate.ev_as_of, datetime):
        ev_day = candidate.ev_as_of.date()
    else:
        ev_day = candidate.ev_as_of
    age = (today - ev_day).days
    if age > MAX_EV_AGE_DAYS:
        return Assessment(candidate.name, False,
                          f"EV is {age} days old (limit {MAX_EV_AGE_DAYS}); stale discovery is not a recommendation")
    if age < 0:
        return Assessment(candidate.name, False, "EV is dated in the future")

    rejected: list[str] = []
    usable: list[Quote] = []
    for q in candidate.quotes:
        if not q.in_stock:
            rejected.append(f"{q.retailer}: out of stock")
        elif q.seller_rating < MIN_SELLER_RATING:
            rejected.append(f"{q.retailer}: seller rating {q.seller_rating:.2f} < {MIN_SELLER_RATING}")
        elif q.price <= 0:
            rejected.append(f"{q.retailer}: non-positive price")
        else:
            usable.append(q)

    if not usable:
        return Assessment(candidate.name, False, "no usable retailer quote", rejected=rejected)

    median = _median([q.price for q in usable])
    flagged: list[str] = []
    trusted: list[Quote] = []
    for q in usable:
        if median > 0 and q.price < median * (1.0 - MISPRICE_UNDER_MEDIAN):
            flagged.append(f"{q.retailer}: ${q.price:.2f} is >=15% under median ${median:.2f}; possibly mispriced")
        else:
            trusted.append(q)

    if not trusted:
        return Assessment(candidate.name, False,
                          "every quote is flagged as possibly mispriced", rejected=rejected, flagged=flagged)

    # Cash actually realised from the contents, after the selling costs.
    realised = candidate.ev * realisation * (1.0 - fee_pct / 100.0) - fee_fixed
    best = min(trusted, key=lambda q: q.landed(tax))
    net = realised - best.landed(tax)

    return Assessment(
        name=candidate.name,
        eligible=True,
        reason="ranked on realised net after fees, shipping and tax",
        net=net,
        buy_price=best.price,
        chosen=best,
        rejected=rejected,
        flagged=flagged,
    )


def compare(candidates: list[Candidate], config: dict, *, today: date | None = None) -> dict[str, Any]:
    """Rank three candidates. Returns the winner, the losers, and why.

    A winner must clear `min_net_profit` (default 0) and be quoted by at least
    two retailers overall, per the bot's standing rule.
    """
    if len(candidates) < 3:
        raise RestockError(f"the three-candidate comparison is the unit of decision; got {len(candidates)}")
    min_net = float(config.get("min_net_profit", 0.0) or 0.0)
    scored = [assess(c, config, today=today) for c in candidates]
    eligible = sorted([a for a in scored if a.eligible], key=lambda a: a.net, reverse=True)


    winner = None
    for a in eligible:
        if a.net < min_net:
            continue
        cand = next(c for c in candidates if c.name == a.name)
        retailers = {q.retailer for q in cand.quotes if q.in_stock}
        if len(retailers) < 2:
            a.eligible = False
            a.reason = "quoted by fewer than two retailers"
            continue
        winner = a
        break

    return {
        "winner": winner.as_dict() if winner else None,
        "reason": winner.reason if winner else "no candidate clears the profit floor with two retailer quotes",
        "ranked": [a.as_dict() for a in sorted(scored, key=lambda a: (a.eligible, a.net), reverse=True)],
        "min_net_profit": min_net,
    }


def should_buy(winner: dict | None, observed_price: float, restock_balance: float) -> dict[str, Any]:
    """The trigger. Still a buy ORDER for the operator, never a purchase."""
    if not winner:
        return {"buy": False, "reason": "no winning candidate"}
    if observed_price > winner["buy_price"]:
        return {"buy": False, "reason": f"observed ${observed_price:.2f} is above the buy price ${winner['buy_price']:.2f}"}
    if restock_balance < observed_price:
        return {"buy": False, "reason": "restock balance does not cover the price",
                "shortfall": round(observed_price - restock_balance, 2)}
    return {"buy": True, "reason": "price at or below target and funded",
            "order": {"retailer": winner["retailer"], "price": round(observed_price, 2),
                      "expected_net": winner["net"]},
            "note": "operator places this order; Binder never does"}
