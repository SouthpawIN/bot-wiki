---
type: loop
slug: savings-trading
bot: pocketshop
schedule: "15 9 * * *"
state: ready
skill: savings-markets
created: 2026-11-17
---

# Savings → attention markets (daily)

Runs after the sale-watch sweep, so the ledger is current before any capital is
considered.

## Steps

1. **Gate first, in code.** `from trading_gate import evaluate` and call
   `evaluate(finance, config)` before looking at any market. It reads
   `data/finance.json` and refuses if `savings_floor` or `trade_max_absolute` is
   unset — an unset money limit is a refusal, never a default.
2. If `gate.open` is false → stop, log `gate.reason`, report `gate.shortfall`.
   Nothing is proposed. Otherwise `gate.tradable` and `gate.max_stake` bound every
   stake, and `stake_for(gate, requested)` clamps it.
3. Aggregate X sentiment for candidate markets (Polymarket, Kalshi): for each,
   collect posts with author + timestamp + claim, and the market's current
   price. Weight recent, high-signal accounts; record the set, don't summarise
   it away.
4. For each market where sentiment and price disagree materially, draft a
   proposal: market, side, current price, stake (<= min(trade_max_pct_of_savings
   of tradable, absolute cap)), expected value, the posts that support it, and
   the strongest argument against.
5. Write proposals to the operator's review queue. **Never place an order.**
6. On settlement (from the previous day's proposals), reconcile stake, payout
   and outcome into the ledger, and score the strategy honestly — including the
   losing wagers.

## Holds

- Never stake money reserved for restock.
- Never exceed the per-wager cap or the percentage cap.
- Never place, cancel or withdraw an order automatically.
- Never present unsourced sentiment as a signal.
- If any connector (X, marketplace, exchange) is unavailable, halt and report;
  do not substitute estimates.
