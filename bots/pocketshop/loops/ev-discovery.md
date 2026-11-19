---
type: loop
slug: ev-discovery
bot: pocketshop
schedule: "0 9 * * *"
state: ready
skill: restock-ev-pick
created: 2026-11-07
---

# ev-discovery

Daily 09:00. Refresh EV candidates; compare three, recommend one, never buy.

## Steps

1. Refresh MTGStocks EV for **set booster boxes in the $150–$250 band**. Record
   `ev` and `ev_as_of` for each; EV older than 30 days is refused downstream.
2. Pick **three** candidates. Fewer than three is not a comparison — say so and
   stop rather than promoting a single box.
3. Price each candidate across **at least two retailers** (Amazon, Walmart,
   MTGgoldfish, TCGplayer as reference, and any other real seller), including
   markdowns. Each quote carries retailer, price, shipping, seller rating,
   stock and URL.
4. **Rank in code**, not prose:

   ```python
   from restock_math import Candidate, Quote, compare, should_buy
   out = compare(candidates, config)      # config = the operator's assumptions
   ```

   `compare()` applies every standing refusal: 30-day EV, seller rating < 0.95,
   out-of-stock, and a quote ≥15% under the median flagged as possibly mispriced
   rather than trusted. Net is realised EV after selling fees, shipping and tax —
   **EV is never treated as cash**.
5. If `out["winner"]` is None, report `out["reason"]` and the losing quotes. Stop.
6. Otherwise watch the winner's price. `should_buy(winner, observed_price,
   restock_balance)` returns the trigger; when it fires, write a **buy order**
   for the operator with the retailer, price and expected net.

## Holds

- **Never purchase.** `should_buy` returns an order for the operator's click.
- `sales_tax_rate`, `sell_fee_pct`, `sell_fixed_fee` and `ev_realisation_rate`
  must be set by the operator; an unset assumption raises rather than defaults.
- The losing quotes are always shown, so the decision can be audited.

## Stop condition

Exit if fewer than 3 candidates clear the 30-day price-data rule; say so once.
