# Flagship 1 — Power BI dashboard (Phase E, started 14 Nov 2026)

**Model:** `f1_powerbi.db` — the Olist star schema plus `dim_order_status`
and `order_status` on the fact table. Rebuild any time with
`python3 powerbi/build_model.py` (reads `data/processed/f1.db`
read-only + `data/raw/olist_orders_dataset.csv`). The model DB is NOT
uploaded to GitHub (rebuildable, same rule as every `.db` in this
portfolio).

**Files**

| File | What it is |
|---|---|
| `build_model.py` | Builds the model DB; writes `verified_measures.json` |
| `measures.dax` | 12 DAX measures with verified values (restated headline first) |
| `build-guide.md` | Relationships + 3 pages + ~20-min build steps |
| `verified_measures.json` | Every measure value, recomputed from the model |
| `f1_powerbi.db` | The model database (local only, not uploaded) |

**Previews** (`../outputs/`): `preview_monthly_revenue.png`,
`preview_revenue_by_category.png`, `preview_revenue_by_state.png`,
`preview_freight_by_category.png` — matplotlib renders of the same
numbers the dashboard shows, all restated.

**The one decision that matters:** the restatement is a
measure-level filter, not a deleted fact. The fact table keeps all
112,650 rows; every headline measure filters
`dim_order_status[is_restated] = 1` (cancelled + unavailable
excluded, `sql/14`). The all-status figure (BRL 13,591,643.70) stays
provable from the model as a footnote — nothing is silently deleted.

**Verify:** `python3 src/check_powerbi_model.py` — 32 checks, all passing.
