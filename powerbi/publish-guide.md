# FLAGSHIP 1 — Phase E: Publish the Power BI report (16 Nov 2026)

This is the last Phase E step before Phase F. The `.pbix` itself is
built in Power BI Desktop on a Windows machine (Hashir's PC or a
later session) from `powerbi/build-guide.md` — this file covers what
happens **after** the `.pbix` exists: publishing it to the Power BI
Service, sharing it, and proving the published numbers match the
verified model. Nothing here is a substitute for the `.pbix` build;
until the `.pbix` exists, the published-report link slot in the
flagship README stays empty and says so.

## 0. What you need before you start

| Item | Where it comes from |
|---|---|
| The `.pbix` | Built in Power BI Desktop per `powerbi/build-guide.md` (~20 min) |
| The model DB | `powerbi/f1_powerbi.db` — rebuild any time with `python3 powerbi/build_model.py` |
| The verified numbers | `powerbi/verified_measures.json` — every KPI the published report must show |
| A Power BI account | Free account signs in; **publishing to the Service needs a Power BI Pro licence** (or a Premium workspace). A free account can build and view the `.pbix` locally, but cannot publish. If there is no Pro licence, the honest fallback is: the `.pbix` + the preview renders in `outputs/` are the deliverable, and the README says so — never claim a published link that does not exist. |
| The three page previews | `outputs/page1_overview.png`, `page2_revenue_leak.png`, `page3_cohorts_churn.png` — what the published pages must look like |

## 1. Publish (Power BI Desktop → Service)

1. In Power BI Desktop, open the `.pbix`. File → Publish → Publish
   to Power BI → sign in with the same account that owns the
   workspace.
2. Pick a workspace. Use a workspace named `mhkh-stock-portfolio`
   (create it first in the Service if it does not exist) — not "My
   workspace", so the report can be shared without sharing a
   personal workspace.
3. After publishing, open the report in the Service and check the
   three pages render. The Service re-renders from the imported
   model, so the numbers must match `verified_measures.json`
   exactly — run the checklist in §3 before sharing anything.

## 2. Refresh — the honest answer for this dataset

The model is **Import mode** from a local SQLite file, and the data
is historical (Olist, Sep 2016 – Aug 2018 — it will never change).
So:

- **No scheduled refresh is needed or set up.** There is nothing
  new to refresh: the extract ends Aug 2018 and the trend stops
  there (`analysis/clean_trend_2017_2018.md`).
- **Do not promise "live" or "auto-refreshing".** The report is a
  static historical analysis. If the model is ever rebuilt from a
  newer extract, republish the `.pbix` from Desktop — that is the
  refresh path, and it takes two minutes.
- A gateway is **not** required: there is no on-premises source to
  reach, and setting one up for a frozen dataset would be theatre.

## 3. Verification checklist for the published report

Check each value on the published pages against
`powerbi/verified_measures.json` (and `src/check_powerbi_model.py`,
32 checks). Tick only what you actually saw on the published page.

| # | Page | Check | Must read |
|---|---|---|---|
| 1 | 1 — Overview | Total Revenue (Restated) | BRL 13,494,400.74 |
| 2 | 1 — Overview | Total Orders (Restated) | 98,199 |
| 3 | 1 — Overview | Total Customers (Restated) | 94,983 |
| 4 | 1 — Overview | Avg Order Value | BRL 137.42 |
| 5 | 1 — Overview | Churn Rate | 69.99% |
| 6 | 1 — Overview | Monthly trend ends Aug 2018; peak Nov 2017 | BRL 1,003,862.14 |
| 7 | 1 — Overview | Footnote: all-status revenue | BRL 13,591,643.70 |
| 8 | 2 — Leak | Total Freight (Restated) | BRL 2,245,816.19 |
| 9 | 2 — Leak | Freight % of Revenue | 16.64% |
| 10 | 2 — Leak | Items Over 100% Freight | 4,100 |
| 11 | 2 — Leak | Worst freight category (500+ items) | `eletronicos` 29.50% |
| 12 | 2 — Leak | Top state share | SP 38.27% |
| 13 | 3 — Cohorts | Repeat buyers | 2,887 (3.04%) |
| 14 | 3 — Cohorts | At-risk repeat buyers | 611 / BRL 168,541.14 |
| 15 | 3 — Cohorts | Month-1 retention, Nov 2017 cohort | 0.56% (vs 0.71% Oct 2017) |
| 16 | All | Slicer default = restated only | `is_restated = 1` |

If any published value differs, the `.pbix` is wrong, not the
model — rebuild from `build-guide.md` and re-check; never edit the
verified numbers to match a wrong visual.

## 4. Share it

1. In the Service, open the report → Share → copy the link.
2. Set the link to "People in your organisation" only if the
   workspace is organisational; for a public portfolio link, use
   **Publish to web** only if you accept the report becoming public
   (it contains no personal data — Olist is a public dataset — so
   this is safe, but it is a deliberate choice, not a default).
3. Paste the link into the flagship README's dashboard section
   (Phase F) and into the profile README library row for Flagship 1.
4. Record the link + the date + the checklist result in
   `powerbi/README.md` under a "Published" note, so the next person
   can see what was verified and when.

## 5. What "done" means for Phase E

- [ ] `.pbix` built in Power BI Desktop per `build-guide.md`
- [ ] Published to the Service (or the no-Pro fallback honestly
      recorded in the README)
- [ ] All 16 checks in §3 ticked against the published pages
- [ ] Link pasted into the flagship README + profile library row
- [ ] `powerbi/README.md` updated with the published note

Until the `.pbix` exists, Phase E is **not** closed — the model,
measures, guide, page layouts and previews are done, and this
publish guide is done, but the published report is still open work
for a Windows session. That is recorded honestly here, not hidden.

## Verify this guide

`python3 src/check_phase_e_publish.py` — checks that every file
this guide names exists, every KPI in the checklist matches
`verified_measures.json`, and every measure in `measures.dax` is
one of the 12 verified measures.
