---
name: savings-markets
description: Gate savings capital, then draft cited attention-market proposals.
version: 1.0.0
author: Binder
license: MIT
metadata:
  hermes:
    tags: [finance, polymarket, kalshi, sentiment, risk]
---

# Savings → attention markets

Drafts wagers on attention markets from the slice of savings that sits above a
ring-fenced floor. **Proposes only.** The operator places every order.

## Step 1 — the gate, before any market is looked at

```bash
python bots/pocketshop/trading_gate.py   # or import evaluate() from it
```

```python
from trading_gate import evaluate, stake_for
gate = evaluate(finance, config)
if not gate.open:
    report(gate.reason, shortfall=gate.shortfall)
    stop()
```

`evaluate()` reads `data/finance.json` (`savings`, `restock_balance`,
`next_restock_buy_price`) and the operator's config:

| Key | Meaning | If unset |
|---|---|---|
| `savings_floor` | amount that must survive any losing streak | **refuses** — no default |
| `trade_max_absolute` | hard per-wager ceiling in dollars | **refuses** — no default |
| `trade_max_pct_of_savings` | percent of *tradable*, not of savings | defaults to 10 |
| `losing_streak_halt` | consecutive losses that halt trading | defaults to 3 |

The arithmetic, in order:

1. `restock_balance < next_restock_buy_price` → **closed**, report the shortfall.
2. losing streak at the halt threshold → **closed**.
3. `reserve_required = max(savings_floor, next_restock_buy_price)`
4. `tradable = savings − reserve_required`; `<= 0` → **closed**.
5. `max_stake = min(tradable × pct/100, trade_max_absolute, tradable)`

An unset money limit raises `GateError`. Never substitute a guess: a fabricated
floor is how a store loses its restock money.

## Step 2 — evidence, not prophecy

For each candidate market (Polymarket, Kalshi), collect the X posts that inform
it: **author, timestamp, the claim, and the market's current price**. Weight
recent, high-signal accounts. Keep the set — do not summarise it into a vibe.

Sentiment is evidence about the crowd, never a prediction. If the posts are thin,
say so and set the stake to zero.

## Step 3 — draft the proposal

Only where sentiment and price disagree materially. Each proposal carries:

- market, side, current price
- stake, clamped by `stake_for(gate, requested)` — a closed gate yields `0.0`
- expected value, stated as an estimate with its assumptions
- the posts it rests on, linked with author and timestamp
- **the strongest argument against it**

Write to the operator's review queue. Never place, cancel or withdraw an order.

## Step 4 — settle honestly

On resolution, reconcile stake, payout and outcome against the proposal that
caused it, into `data/finance.json`. Score the strategy including every losing
wager. A streak that reaches `losing_streak_halt` closes the gate on the next run.

## Holds

- Never stake money reserved for restock.
- Never exceed the per-wager cap or the percentage cap.
- Never place, cancel or withdraw an order automatically.
- Never present unsourced sentiment as a signal.
- If any connector (X, marketplace, exchange) is unavailable, halt and report —
  do not substitute estimates.

## Tests

`bots/pocketshop/tests/test_trading_gate.py` — 15 cases, every one a way money
could be lost: unfunded reserve, savings at the floor, streak halt, unset limits,
negative and non-numeric values, percentage over 100, stake clamping, and the
invariant that a stake can never exceed tradable.
