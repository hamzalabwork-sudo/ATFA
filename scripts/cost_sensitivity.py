"""Sensitivity of total-cost conclusions to the assumed cost parameters.

    python scripts/cost_sensitivity.py --results results/confirmatory_v2

Decisions do not depend on the cost weights: thresholds minimise fraudulent value settled under
hold/reject budgets, and calibration was feasible in every world (the cost-based fallback was never
used). Total cost can therefore be recomputed exactly for any (review cost, rejection penalty):
    total = FVS + review * (holds + audits) + penalty * legitimate value rejected
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

REVIEW = [5, 10, 25, 50, 100]
PENALTY = [0.05, 0.2, 0.5, 1.0]
COMPARATORS = ["B3 detector only", "B2 fixed amount threshold", "ATFA trust=beta", "B0 approve all (smart contract only)"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/confirmatory_v2")
    args = ap.parse_args()
    R = Path(args.results)
    fin = pd.read_csv(R / "financial.csv")
    assert fin[fin.system == "ATFA"].calib_feasible.all(), "cost fallback used somewhere; recomputation invalid"
    fin = fin[fin.scenario == "id"].copy()
    audits = fin.get("audits_per_1000", pd.Series(0.0, index=fin.index)).fillna(0.0)
    fin["holds_n"] = (fin.holds_per_1000 + audits) * fin.n_claims / 1000
    rows = []
    for rv in REVIEW:
        for pen in PENALTY:
            fin["cost"] = fin.fvs + rv * fin.holds_n + pen * fin.legit_rejected_value
            piv = fin.pivot_table(index=["level", "seed"], columns="system", values="cost")
            for comp in COMPARATORS:
                a, b = piv["ATFA"], piv[comp]
                diff = a - b
                p = wilcoxon(a, b).pvalue if (diff != 0).any() else 1.0
                rows.append(dict(review_cost=rv, reject_penalty=pen, comparator=comp,
                                 atfa_cost_k=a.mean() / 1e3, comparator_cost_k=b.mean() / 1e3,
                                 saving_pct=100 * (1 - a.mean() / b.mean()),
                                 atfa_cheaper_in=f"{int((diff < 0).sum())}/{len(diff)}", p=p))
    df = pd.DataFrame(rows)
    out = R / "report"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "cost_sensitivity.csv", index=False)
    with open(out / "cost_sensitivity.md", "w", encoding="utf-8") as f:
        f.write("# Cost-parameter sensitivity (in-distribution, all 80 worlds pooled)\n\n"
                "Total cost = fraud settled + review cost x (holds + audits) + penalty x legitimate value rejected. "
                "Defaults: review 25, penalty 0.2. p: paired Wilcoxon over 80 worlds (uncorrected).\n")
        for comp in COMPARATORS:
            t = df[df.comparator == comp].pivot_table(index="review_cost", columns="reject_penalty",
                                                      values="saving_pct").round(1)
            w = df[df.comparator == comp].pivot_table(index="review_cost", columns="reject_penalty",
                                                      values="atfa_cheaper_in", aggfunc="first")
            f.write(f"\n## ATFA cost saving vs {comp} (%)\n\n{t.to_markdown()}\n\nWorlds where ATFA is cheaper:\n\n"
                    f"{w.to_markdown()}\n")
    pd.set_option("display.width", 250)
    for comp in COMPARATORS:
        print(f"\n== saving % vs {comp}")
        print(df[df.comparator == comp].pivot_table(index="review_cost", columns="reject_penalty",
                                                    values="saving_pct").round(1).to_string())
        print(df[df.comparator == comp].pivot_table(index="review_cost", columns="reject_penalty",
                                                    values="atfa_cheaper_in", aggfunc="first").to_string())
        print(df[df.comparator == comp].pivot_table(index="review_cost", columns="reject_penalty",
                                                    values="p").round(4).to_string())


if __name__ == "__main__":
    main()
