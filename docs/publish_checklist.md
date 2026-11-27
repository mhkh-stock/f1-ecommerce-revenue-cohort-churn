# Flagship 1 — Publish Checklist (Phase F)

**Target live: Fri 27 Nov 2026.** This checklist is ticked in order
on publish day. Nothing is ticked from memory — each line is verified
against the live repo or a fresh check run in the same session.

## 1. Analysis complete (all done — re-verify, don't re-do)

- [ ] Phase A — ingest: `data/processed/f1.db` builds from raw CSVs
      with `python3 src/ingest.py` — 112,650 fact rows, 0 rejected.
- [ ] Phase B — cohorts + LTV: `sql/09` + re-check `sql/13` — 23
      cohorts, LTV flat BRL 131–167.
- [ ] Phase C — RFM + churn: `sql/10`, `sql/11` — churn 69.99%.
- [ ] Phase D — validation + restatement + clean trend: `sql/12`
      (11 headlines reconcile 3 ways), `sql/14` (restated revenue
      BRL 13,494,400.74), `sql/15` (Nov 2016 gap is in the source),
      `sql/16` (clean trend Jan 2017 → Aug 2018).
- [ ] Phase E — Power BI: model + 12 DAX measures
      (`powerbi/verified_measures.json`), 3 page layouts + previews,
      publish guide, README draft.
- [ ] Phase F prep — architecture diagram
      (`docs/architecture.mmd` + `outputs/architecture_diagram.png`).

## 2. Regression sweep (run every check script fresh on publish day)

- [ ] `python3 src/validate_headlines.py` — 11 checks
- [ ] `python3 src/check_rfm.py` — 30 checks
- [ ] `python3 src/check_order_status.py` — 36 checks
- [ ] `python3 src/check_ltv_recheck.py` — 13 checks
- [ ] `python3 src/check_nov2016_gap.py` — 26 checks
- [ ] `python3 src/check_clean_trend.py` — 25 checks
- [ ] `python3 src/check_powerbi_model.py` — 32 checks
- [ ] `python3 src/check_dashboard_pages.py` — 29 checks
- [ ] `python3 src/check_phase_e_publish.py` — 70 checks
- [ ] `python3 src/check_architecture.py` — 62 checks
- [ ] `python3 src/check_one_pager.py` — 46 checks
- [ ] `python3 src/check_executive_summary.py` — 110 checks
- [ ] `python3 src/check_phase_f_polish.py` — README polish + this checklist

All must pass with 0 failures. Any failure stops the publish —
fix it, re-run, and say so plainly in the day's report.

## 3. README final (Phase F)

- [x] Status line no longer says DRAFT — it says LIVE with the
      publish date and the repo link. (DONE 27 Nov 2026)
- [x] Every headline number matches `powerbi/verified_measures.json`
      and the Phase D notes (checked by
      `src/check_phase_f_polish.py`). (DONE 27 Nov 2026 — polish check 68/68)
- [x] File counts in the project-structure block match the repo
      (sql 16 + schema, src 12 check scripts + 2 render scripts,
      analysis 12 notes, outputs 8 renders). (DONE 27 Nov 2026 — polish check 68/68)
- [x] Power BI report link slot: filled with the published report
      URL if the `.pbix` is built, otherwise still honestly empty
      with the "not yet published" wording kept. (DONE 27 Nov 2026 — .pbix NOT built, wording kept)
- [x] One-pager present (Phase F deliverable — see §6). (DONE 27 Nov 2026 — outputs/one_pager.pdf live)

## 4. The `.pbix` question (honest either way)

- [ ] `.pbix` built in Power BI Desktop on a Windows machine
      (his PC or a later session) from `powerbi/build-guide.md`?
- [ ] If YES: published to Power BI Service, link pasted into the
      README + `powerbi/publish-guide.md` §3 checklist ticked
      against the live pages.
- [ ] If NO: README keeps the "not yet published" wording and the
      "No `.pbix` is bundled" note. Never ship a fake `.pbix`.

## 5. Publish steps (proven flow)

1. [x] Browser task creates the empty public repo
      `f1-ecommerce-revenue-cohort-churn`. (DONE 27 Nov 2026)
2. [x] GitHub App pushes all text files (README, PLAN, sql/, src/,
      analysis/, docs/, powerbi/ — NO `.db`, NO raw CSVs). (DONE 27 Nov 2026 — commit 8f55b88b, 62 files)
3. [x] Browser task uploads the binaries into their matching
      folders: `outputs/` (8 PNGs + one_pager.pdf). (DONE 27 Nov 2026 — commit 1883dda)
4. [x] Verify live: every file present in its correct folder;
      every binary byte-size matched against the local original. (DONE 27 Nov 2026 — 18/20 blob SHAs identical, 2 largest size-verified)
5. [x] Proprietary LICENSE pushed to the repo root
      (`python3 ~/workspace/license-push/run_batch.py
      f1-ecommerce-revenue-cohort-churn`) and verified live. (DONE 27 Nov 2026 — commit ac8299f7, blob SHA c21c637a)
6. [x] Profile README library table updated with the live repo
      link (download the live README first, byte-match, add the
      row, push, verify live). (DONE 27 Nov 2026 — commit 411fc4c0)
7. [x] Second-pass review: re-check the repo, the records
      (TRACKER.md, SCHEDULE.md) and the profile table, fix or
      report any gap plainly, once. (DONE 27 Nov 2026 — 10 spot-check files live; records updated)

## 6. Still open before publish day

**Review 20 Nov 2026 (Phase F checklist review):** full regression
sweep re-run fresh — 446 checks, 0 failures (11 validate + 30 RFM +
36 order-status + 13 LTV + 26 Nov-2016 gap + 25 clean trend + 32
Power BI model + 29 dashboard pages + 70 publish + 62 architecture
+ 46 one-pager + 66 polish). One real drift found and fixed the same
day: `src/check_one_pager.py` (added 19 Nov with the one-pager) made
11 check scripts, but the README, this checklist §3 and
`check_phase_f_polish.py` still said 10 — all three now say 11, and
§2 now lists `check_one_pager.py`. Nothing else drifted.

- [x] **One-pager** (Phase F deliverable): built 19 Nov 2026, then
      restated-basis final pass 21 Nov 2026 with the executive
      summary (see below) — `docs/one_pager.md` +
      `outputs/one_pager.pdf` (exactly 1 page, A4) +
      `src/build_one_pager.py` + `src/check_one_pager.py`.
- [x] **2-page executive summary** — final pass DONE 21 Nov 2026
      (`analysis/executive_summary.md` FINAL +
      `src/check_executive_summary.py`): every figure recomputed
      from the model DB on the restated basis; the draft's
      all-status figures replaced (over-100% items 4,119 → 4,100;
      one-time buyers 92,507 → 92,096; LTV range 131–167 → 131–163;
      SP 38.28% → 38.27%; electronics 29.07% → 29.50%, 22.08% →
      22.18%; Nov 2017 cohort 7,217 / BRL 140.63 → 7,188 /
      BRL 140.30; retention 0.55%/0.70% → 0.56%/0.71%; cohort churn
      98.71–99.23% → 98.62–99.24%; AOV band 126–147 → 126–145;
      orders growth "~9x" → "about 8–9x" (787 → 6,145–7,187 a
      month); top category 9.26% → 9.31%; at-risk customers 18,594 →
      18,536).
      The README and one-pager were aligned to the same restated
      basis the same day, so all three publish-facing documents
      agree; the Phase B/C/D analysis notes keep their all-status
      figures with their own basis (the analysis record, not the
      publish story). The clean-trend note's AOV band was corrected
      the same way (126–147 → 126–145: the 147 was never verified;
      restated max BRL 145.31, all-status max BRL 145.41).
- [ ] Pins: after Flagship 1 goes live, pin it in the profile
      README's target set (F1 first).

## 7. Numbers that must never drift (the lock)

| Number | Locked value |
|---|---:|
| Restated revenue | BRL 13,494,400.74 |
| Restated orders / customers | 98,199 / 94,983 |
| As-loaded revenue (footnote) | BRL 13,591,643.70 |
| Fact rows | 112,650 |
| Churn | 69.99% (66,476 customers) |
| At-risk repeat buyers worth saving | 611 — BRL 168,541.14 |
| Clean trend total | BRL 13,449,529.68 (Jan 2017 → Aug 2018) |
| Peak month | Nov 2017 — BRL 1,003,862.14 |
| Repeat buyers | 2,887 (3.04%) |

If any check ever disagrees with this table, the check is right
and the table is wrong — or the data changed. Stop and find out
which, before anything is published.
