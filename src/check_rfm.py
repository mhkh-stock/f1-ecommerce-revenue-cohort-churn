"""FLAGSHIP 1 — Phase C verification (7 Nov 2026).

Runs sql/10_rfm_segments.sql and sql/11_churn_analysis.sql against
the live star schema and asserts reconciliation. Read-only: the
database is opened with mode=ro, so this script cannot modify f1.db.

    python3 src/check_rfm.py [--db data/processed/f1.db]

Assertions (every number comes from the queries, not from memory):
- RFM base (file 10, Q1): 95,420 customers, 98,666 orders,
  BRL 13,591,643.70 revenue.
- Segments (file 10, Q3): 9 named segments; customer counts sum to
  95,420; segment revenue sums to BRL 13,591,643.70; shares sum to
  ~100%.
- F-score diagnostic (file 10, Q4): buckets 1-4 hold zero repeat
  buyers; bucket 5 holds 16,171 one-time + 2,913 repeat buyers.
- Churn (file 11, Q1): churned 66,802 + active 28,618 = 95,420;
  revenues sum to BRL 13,591,643.70.
- Churn by cohort year (file 11, Q2): customer and churned counts
  reconcile to Q1.
- At-risk (file 11, Q3-Q4): 18,594 customers, BRL 2,751,210.98 at
  stake; the one-time/repeat split sums back to Q3; at-risk is a
  subset of active (count and revenue).
- At-risk list (file 11, Q5): exactly 25 rows.
- Cut-off sensitivity (file 11, Q6): 10,026 customers would flip if
  the cut-off were 2018-09-03; churn under that cut-off is 56,776
  (59.50%).

Exit code 0 when every check passes, 1 otherwise.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SQL_10 = PROJECT / "sql" / "10_rfm_segments.sql"
SQL_11 = PROJECT / "sql" / "11_churn_analysis.sql"

TOTAL_CUSTOMERS = 95_420
TOTAL_ORDERS = 98_666
TOTAL_REVENUE = 13_591_643.70
CHURNED = 66_802
ACTIVE = 28_618
AT_RISK = 18_594
AT_RISK_REVENUE = 2_751_210.98
TOL = 0.01

EXPECTED_SEGMENTS = {
    "Champions",
    "Loyal",
    "Potential Loyalists",
    "Recent One-Time",
    "Fading One-Time",
    "At-Risk",
    "At-Risk One-Time",
    "Hibernating",
    "Lost",
}


def split_statements(text):
    """Split a .sql file into statements: a statement ends on a line
    whose last non-blank character is ';'. Comment lines never end
    in ';', so they ride along with the following statement."""
    statements, buf = [], []
    for line in text.splitlines(keepends=True):
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_file(conn, path):
    """Execute every statement in a .sql file, return results in order."""
    statements = split_statements(path.read_text())
    results = []
    for stmt in statements:
        cur = conn.execute(stmt)
        results.append(cur.fetchall())
    return results


def close(actual, expected, tol=TOL):
    return abs(actual - expected) <= tol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(PROJECT / "data" / "processed" / "f1.db"))
    args = parser.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    try:
        rfm = run_file(conn, SQL_10)
        churn = run_file(conn, SQL_11)
    finally:
        conn.close()

    passed, failed = [], []

    def check(name, ok, detail=""):
        (passed if ok else failed).append(name)
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

    # --- file 10, Q1: RFM base totals -------------------------------
    q1 = rfm[0][0]
    check("10-Q1 customers == 95,420", q1[0] == TOTAL_CUSTOMERS, f"got {q1[0]}")
    check("10-Q1 orders == 98,666", q1[1] == TOTAL_ORDERS, f"got {q1[1]}")
    check("10-Q1 revenue == BRL 13,591,643.70",
          close(q1[2], TOTAL_REVENUE), f"got {q1[2]:,.2f}")

    # --- file 10, Q3: segment reconciliation ------------------------
    seg = rfm[2]
    names = {row[0] for row in seg}
    check("10-Q3 exactly the 9 expected segments",
          names == EXPECTED_SEGMENTS and len(seg) == 9,
          f"got {sorted(names)}")
    cust_sum = sum(row[1] for row in seg)
    rev_sum = sum(row[3] for row in seg)
    check("10-Q3 segment customers sum to 95,420",
          cust_sum == TOTAL_CUSTOMERS, f"got {cust_sum}")
    check("10-Q3 segment revenue sums to BRL 13,591,643.70",
          close(rev_sum, TOTAL_REVENUE), f"got {rev_sum:,.2f}")
    share_sum = sum(row[2] for row in seg)
    check("10-Q3 customer shares sum to ~100%",
          99.98 <= share_sum <= 100.02, f"got {share_sum}")

    # --- file 10, Q4: F-score diagnostic -----------------------------
    diag = {row[0]: row for row in rfm[3]}
    check("10-Q4 F buckets 1-4 hold zero repeat buyers",
          all(diag[b][3] == 0 for b in (1, 2, 3, 4)),
          f"got {[diag[b][3] for b in (1, 2, 3, 4)]}")
    check("10-Q4 F bucket 5 = 16,171 one-time + 2,913 repeat",
          diag[5][2] == 16_171 and diag[5][3] == 2_913,
          f"got {diag[5][2]} one-time, {diag[5][3]} repeat")

    # --- file 11, Q1: churned + active -------------------------------
    c1 = {row[0]: row for row in churn[0]}
    check("11-Q1 churned == 66,802", c1["churned"][1] == CHURNED,
          f"got {c1['churned'][1]}")
    check("11-Q1 active == 28,618", c1["active"][1] == ACTIVE,
          f"got {c1['active'][1]}")
    check("11-Q1 churned + active == 95,420",
          c1["churned"][1] + c1["active"][1] == TOTAL_CUSTOMERS)
    rev_total = c1["churned"][3] + c1["active"][3]
    check("11-Q1 churned + active revenue == BRL 13,591,643.70",
          close(rev_total, TOTAL_REVENUE), f"got {rev_total:,.2f}")
    check("11-Q1 churn rate == 70.01%",
          close(c1["churned"][2], 70.01, 0.005),
          f"got {c1['churned'][2]}%")

    # --- file 11, Q2: churn by cohort year reconciles to Q1 ---------
    c2 = churn[1]
    check("11-Q2 cohort-year customers sum to 95,420",
          sum(row[1] for row in c2) == TOTAL_CUSTOMERS,
          f"got {sum(row[1] for row in c2)}")
    check("11-Q2 cohort-year churned sums to 66,802",
          sum(row[2] for row in c2) == CHURNED,
          f"got {sum(row[2] for row in c2)}")
    by_year = {row[0]: row for row in c2}
    check("11-Q2 2017 churn rate == 99.23%",
          close(by_year["2017"][3], 99.23, 0.005),
          f"got {by_year['2017'][3]}%")
    check("11-Q2 2018 churn rate == 45.50% (censored, see write-up)",
          close(by_year["2018"][3], 45.50, 0.005),
          f"got {by_year['2018'][3]}%")

    # --- file 11, Q3-Q4: at-risk --------------------------------------
    q3 = churn[2][0]
    check("11-Q3 at-risk == 18,594 customers", q3[0] == AT_RISK,
          f"got {q3[0]}")
    check("11-Q3 revenue at stake == BRL 2,751,210.98",
          close(q3[1], AT_RISK_REVENUE), f"got {q3[1]:,.2f}")
    check("11-Q3 at-risk is a subset of active (count)",
          q3[0] <= ACTIVE, f"{q3[0]} <= {ACTIVE}")
    check("11-Q3 at-risk is a subset of active (revenue)",
          q3[1] <= c1["active"][3] + TOL,
          f"{q3[1]:,.2f} <= {c1['active'][3]:,.2f}")
    q4 = {row[0]: row for row in churn[3]}
    check("11-Q4 at-risk split sums back to 18,594",
          q4["repeat buyers (saveable)"][1]
          + q4["one-time buyers (phantom at stake)"][1] == AT_RISK)
    check("11-Q4 at-risk split revenue sums to BRL 2,751,210.98",
          close(q4["repeat buyers (saveable)"][2]
                + q4["one-time buyers (phantom at stake)"][2],
                AT_RISK_REVENUE),
          f"got {q4['repeat buyers (saveable)'][2] + q4['one-time buyers (phantom at stake)'][2]:,.2f}")
    check("11-Q4 saveable at-risk repeat buyers == 617",
          q4["repeat buyers (saveable)"][1] == 617,
          f"got {q4['repeat buyers (saveable)'][1]}")
    check("11-Q4 saveable revenue == BRL 169,495.02",
          close(q4["repeat buyers (saveable)"][2], 169_495.02),
          f"got {q4['repeat buyers (saveable)'][2]:,.2f}")

    # --- file 11, Q5-Q6 ----------------------------------------------
    check("11-Q5 at-risk list returns exactly 25 rows",
          len(churn[4]) == 25, f"got {len(churn[4])}")
    q6 = churn[5][0]
    check("11-Q6 would-flip customers == 10,026", q6[0] == 10_026,
          f"got {q6[0]}")
    check("11-Q6 churn under 2018-09-03 cut-off == 56,776 (59.50%)",
          q6[1] == 56_776 and close(q6[2], 59.50, 0.005),
          f"got {q6[1]} ({q6[2]}%)")

    # --- cross-file ---------------------------------------------------
    check("cross-file: segment revenue == churn revenue",
          close(rev_sum, rev_total),
          f"{rev_sum:,.2f} vs {rev_total:,.2f}")

    print(f"\n{len(passed)} passed, {len(failed)} failed "
          f"({len(passed) + len(failed)} checks)")
    if failed:
        print("Failed checks:", ", ".join(failed))
        return 1
    print("All Phase C checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
