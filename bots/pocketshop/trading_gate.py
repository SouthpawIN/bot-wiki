"""Capital-preservation gate for the savings -> attention-markets loop.

Pure arithmetic, no network, no orders. The loop calls this BEFORE it looks at a
single market, so an unfunded restock reserve stops the run rather than being
discovered after a proposal is drafted.

Money rule: an unset limit is a refusal, never a default. Guessing a floor with
someone's savings is the one failure this module exists to prevent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class GateError(ValueError):
    """Configuration is missing or malformed; trading must not proceed."""


@dataclass(frozen=True)
class Gate:
    open: bool
    reason: str
    tradable: float = 0.0
    max_stake: float = 0.0
    reserve_required: float = 0.0
    shortfall: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "open": self.open,
            "reason": self.reason,
            "tradable": round(self.tradable, 2),
            "max_stake": round(self.max_stake, 2),
            "reserve_required": round(self.reserve_required, 2),
            "shortfall": round(self.shortfall, 2),
        }


def _number(source: dict, key: str, *, required: bool = True) -> float | None:
    if key not in source or source[key] is None:
        if required:
            raise GateError(f"{key} is not set; refusing to guess a money limit")
        return None
    try:
        value = float(source[key])
    except (TypeError, ValueError) as exc:
        raise GateError(f"{key} must be a number, got {source[key]!r}") from exc
    if value < 0:
        raise GateError(f"{key} must not be negative, got {value}")
    return value


def _required(source: dict, key: str) -> float:
    """A required limit is always a float; a missing one raises above."""
    value = _number(source, key, required=True)
    assert value is not None  # _number(required=True) never returns None
    return value


def evaluate(finance: dict, config: dict) -> Gate:
    """Decide whether any capital may be proposed, and how much per wager.

    finance: savings, restock_balance, next_restock_buy_price
    config:  savings_floor (required), trade_max_pct_of_savings (default 10),
             trade_max_absolute (required), losing_streak, losing_streak_halt
    """
    savings = _required(finance, "savings")
    restock_balance = _required(finance, "restock_balance")
    next_buy = _required(finance, "next_restock_buy_price")

    floor = _required(config, "savings_floor")
    absolute = _required(config, "trade_max_absolute")
    pct = _number(config, "trade_max_pct_of_savings", required=False)
    if pct is None:
        pct = 10.0
    if pct > 100:
        raise GateError(f"trade_max_pct_of_savings must be <= 100, got {pct}")

    # Restock is reserved before anything else is considered.
    if restock_balance < next_buy:
        shortfall = next_buy - restock_balance
        return Gate(
            open=False,
            reason="trading disabled: restock reserve not funded",
            reserve_required=next_buy,
            shortfall=shortfall,
        )

    streak = int(config.get("losing_streak", 0) or 0)
    halt_at = int(config.get("losing_streak_halt", 3) or 3)
    if streak >= halt_at:
        return Gate(
            open=False,
            reason=f"trading halted: {streak} consecutive losses (halt at {halt_at})",
            reserve_required=next_buy,
        )

    reserve_required = max(floor, next_buy)
    tradable = savings - reserve_required
    if tradable <= 0:
        return Gate(
            open=False,
            reason="trading disabled: no savings above the ring-fenced floor",
            reserve_required=reserve_required,
        )

    max_stake = min(tradable * pct / 100.0, absolute, tradable)
    if max_stake <= 0:
        return Gate(
            open=False,
            reason="trading disabled: per-wager cap resolves to zero",
            tradable=tradable,
            reserve_required=reserve_required,
        )

    return Gate(
        open=True,
        reason="trading enabled within caps",
        tradable=tradable,
        max_stake=max_stake,
        reserve_required=reserve_required,
    )


def stake_for(gate: Gate, requested: float) -> float:
    """Clamp a proposed stake to the gate. A closed gate always yields zero."""
    if not gate.open:
        return 0.0
    if requested < 0:
        raise GateError(f"stake must not be negative, got {requested}")
    return round(min(requested, gate.max_stake), 2)
