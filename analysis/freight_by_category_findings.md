# Flagship 1 — Freight burden by category (Phase A, 5 Nov 2026)

Source: `sql/08_freight_by_category.sql`, run against the real loaded
star schema (`data/processed/f1.db`, 112,650 fact rows). This answers
the cross-tab question the revenue leak notes left for Phase D: is
the freight leak general, or a few categories' story?

## Reconciliation (the query must tie back to the ingest record)

- Categories: 74 (including 1,603 items with no category label,
  shown as `(no category)` — empty string in the source, not NULL;
  the query normalises it so those items are counted, never dropped).
- Items: 112,650 ✓ · Revenue: BRL 13,591,643.70 ✓ ·
  Freight: BRL 2,256,599.44 ✓ · Items where freight exceeds price:
  4,119 ✓ — all four match the ingest record and `sql/06` exactly.

## Findings

1. **The leak is concentrated, not general.** Electronics
   (`eletronicos`) is the clear outlier among large categories:
   freight is 29.07% of price and 611 of its 2,767 items (22.08%)
   cost more to deliver than they sell for. The next-worst large
   category on the over-100% share is `telefonia` at 9.46%
   (430 of 4,545 items) — less than half electronics' rate.
2. **Big-freight categories are not the worst-rate categories.**
   The largest freight bills sit in `cama_mesa_banho`
   (BRL 204,693.04, 19.74%), `beleza_saude` (BRL 182,748.35, 14.52%)
   and `moveis_decoracao` (BRL 173,483.29, 23.77%) — high in reais
   because they sell a lot, not because their rates are extreme.
   Fixing delivery pricing category-by-category starts with
   electronics, not with the biggest bill.
3. **Tiny categories show extreme rates on tiny bases — do not
   over-read them.** `casa_conforto_2` shows 53.97% freight but on
   just 30 items (BRL 760.27 revenue); `dvds_blu_ray` 37.50%
   over-100% on 64 items. These are footnotes, not strategy.
4. **The safe category proves the point.** `relogios_presentes`
   (watches/gifts) carries BRL 1,205,005.68 of revenue at only 8.34%
   freight and 0.53% over-100% items — high-ticket, light, shippable.
   The leak is a product-physics story (heavy/cheap electronics),
   not a whole-business story.

## What Phase D still owes

- Restated revenue after the order-status filter (cancelled /
  unavailable ~1.24% of orders) — unchanged by this query.
- Whether electronics' freight problem is weight-driven (join
  `dim_product.product_weight_g`) — the natural follow-up to this
  cross-tab, and a candidate Phase B query.
- The Nov 2016 gap check and the clean 2017–2018 trend — still open
  from the leak notes.
