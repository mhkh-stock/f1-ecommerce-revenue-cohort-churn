# Flagship 1 — Executive summary skeleton (Phase D, 9 Nov 2026)

Skeleton for the 2-page executive summary (Phase F, 21–26 Nov).
Every figure below is verified; the numbers in brackets are the
placeholders Phase F fills with the final restated revenue and the
Power BI visuals. No number here is a draft estimate — where a figure
is still open, the skeleton says so instead of guessing.

## Page 1 — the story

**Headline (one sentence):** Olist's Brazilian e-commerce business
made **BRL 13,591,643.70** from **95,420 customers** across **98,666
orders** (Sep 2016 – Oct 2018), but it buys customers it does not
keep: **96.9% buy once**, lifetime value is flat at **BRL 142.44**
per customer, and **70.01% have churned** — so the margin is in
freight and geography, not in loyalty.

**The three numbers that carry the story:**

| Number | Value | Source |
|---|---:|---|
| Revenue (as loaded) | BRL 13,591,643.70 | ingest + `sql/12` validation |
| Freight (delivery cost, not revenue) | BRL 2,256,599.44 (16.6% of price) | `sql/06` |
| Customers / one-time buyers | 95,420 / 92,507 (96.9%) | `sql/09` + `sql/10` |
| Lifetime value per customer | BRL 142.44 (range BRL 131–167 by cohort) | `sql/09`, re-checked `sql/13` |
| Churned / active | 66,802 (70.01%) / 28,618 (29.99%) | `sql/11` |
| Saveable at-risk revenue | BRL 169,495.02 (617 repeat buyers) | `sql/11` |
| [Restated revenue excl. cancelled/unavailable] | [Phase D restatement — open] | next Phase D block |

**The story in three paragraphs (draft text for Phase F):**

1. *Revenue is real but leaky.* Freight eats 16.6% of every real
   of price, and 4,119 items cost more to deliver than they sell
   for. The leak is concentrated in electronics (29.07% freight,
   22.08% of items over 100%), not spread across the catalogue —
   which is why it is fixable without touching product prices.
2. *Customers are bought, not kept.* Lifetime value sits in a narrow
   BRL 131–167 band for every cohort with more than 300 customers,
   including the Nov 2017 Black Friday cohort (7,217 customers,
   BRL 140.63 each) — size bought revenue, not better customers.
   Retention in month 1 is 0.55% for that cohort and 0.70% for its
   neighbour: the discount-buyer hypothesis fails because nothing
   retains. In the fully-observed 2016–2017 cohorts, 98.71–99.23%
   of customers have churned.
3. *Geography is the concentration risk.* São Paulo is 38.28% of
   revenue; the top 3 states are 63.36%. No single category
   dominates (top category 9.26%), so the business is diversified
   by product and concentrated by place — the opposite of the
   obvious reading.

## Page 2 — the three moves + caveats

**The three recommendations** (full text in
`analysis/recommendations.md`):

1. Fix freight pricing on electronics first — category-level
   delivery pricing; success = electronics over-100% rate from
   22.08% toward ~9%, overall freight share from 16.6% toward ~14%.
2. Grow acquisition outside São Paulo — SP share below 35% while
   total revenue grows; test cost per acquired customer by state.
3. Retain the 617 at-risk repeat buyers only — win-back to 617
   people, worth BRL 169,495.02; report "revenue at risk" as that
   figure, never as BRL 2.75M.

**Caveats the summary must carry (not footnotes):**

- Revenue as loaded includes ~1.24% of orders that are cancelled or
  unavailable (625 + 609 of 99,441); the restated figure lands in
  the next Phase D block and replaces the headline if it moves.
- Churn is 59.50–70.01% depending on the cut-off (2018-09-03 vs
  2018-10-17); 70.01% is the headline under the locked definition,
  and the 44 dead days after the last item-bearing purchase
  (2018-09-03) put a +44-day floor under every recency.
- 2018 cohorts read worse on repeat share only because they had
  less calendar time to make a second purchase (censoring, not a
  worsening business); the honest comparison set is cohorts up to
  Dec 2017.
- RFM segments describe *when* people bought once, not a loyalty
  ladder — NTILE frequency score is meaningless here (92,507
  customers share frequency = 1), so segments use R score + actual
  order count.
- Sep–Dec 2016 cohorts are tiny (3, 305, 0, 1 customers) — their
  per-customer figures are not comparable to later cohorts.

**What Phase E/F still adds:** the Power BI dashboard (model + DAX
+ screenshots), the architecture diagram, the 2-page summary in its
final layout, and the one-pager. The skeleton above is the content
those visuals hang on — no new analysis is needed for the summary
itself beyond the open restatement.
