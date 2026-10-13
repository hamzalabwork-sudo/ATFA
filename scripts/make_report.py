"""Aggregate experiment results into paper tables (Markdown + LaTeX) and figures.

    python scripts/make_report.py --results results/full

Statistics: mean ± std over seeds; paired two-sided Wilcoxon signed-rank tests of ATFA against
each comparator on the same worlds (same scenario, level, seed), Holm-corrected per metric.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

# Reference categorical palette (dataviz skill), fixed order; text in neutral ink.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "lines.linewidth": 2, "lines.markersize": 6, "savefig.dpi": 300, "savefig.bbox": "tight",
})

MAIN_SYSTEMS = ["B0 approve all (smart contract only)", "B1 hard rules only", "B2 fixed amount threshold",
                "B3 detector only", "B4 trust only", "ATFA (provisional thresholds)", "ATFA", "Oracle"]
FIN_COLS = ["fvs_pct", "fraud_block_rate", "legit_hold_rate", "legit_reject_rate", "holds_per_1000", "total_cost"]
# Pre-registered primary comparisons (docs/confirmatory_plan.md); Holm correction across these only.
PRIMARY = ["B3 detector only", "B2 fixed amount threshold", "ATFA trust=beta"]
DET_COLS = ["pr_auc", "f1", "precision", "recall", "fpr", "episode_detect_rate", "infer_ms_per_window", "n_params"]


def mstd(df, keys, cols, pct=()):
    g = df.groupby(keys, sort=False)[cols]
    m, s = g.mean(), g.std().fillna(0)
    out = m.copy().astype(object)
    for c in cols:
        k = 100 if c in pct else 1
        fmt = "{:.1f} ± {:.1f}" if k == 100 else ("{:.0f} ± {:.0f}" if m[c].abs().max() > 100 else "{:.3f} ± {:.3f}")
        out[c] = [fmt.format(a * k, b * k) for a, b in zip(m[c], s[c])]
    return out.reset_index()


def boot_ci(diff, n_boot=10_000, seed=0):
    """Percentile bootstrap 95 % CI of the mean paired difference (ATFA - comparator)."""
    rng = np.random.default_rng(seed)
    if len(diff) < 2:
        return np.nan, np.nan
    means = diff[rng.integers(0, len(diff), (n_boot, len(diff)))].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def rank_biserial(diff):
    """Matched-pairs rank-biserial correlation; negative = ATFA lower (better). |r|: .1 small, .3 medium, .5 large."""
    d = diff[diff != 0]
    if len(d) == 0:
        return 0.0
    from scipy.stats import rankdata
    r = rankdata(np.abs(d))
    return float((r[d > 0].sum() - r[d < 0].sum()) / r.sum())


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def paired_tests(fin, ref="ATFA", metrics=("fvs", "total_cost"), comparators=None):
    rows = []
    for (scen, lvl), d in fin.groupby(["scenario", "level"]):
        piv = {m: d.pivot_table(index="seed", columns="system", values=m) for m in metrics}
        for m in metrics:
            P = piv[m]
            if ref not in P or len(P) < 5:
                continue
            res = []
            for sysname in P.columns:
                if sysname == ref or sysname == "Oracle":
                    continue
                if comparators is not None and sysname not in comparators:
                    continue
                a, b = P[ref], P[sysname]
                ok = a.notna() & b.notna()
                diff = (a[ok] - b[ok])
                p = wilcoxon(a[ok], b[ok]).pvalue if (diff != 0).any() else 1.0
                lo, hi = boot_ci(diff.to_numpy())
                res.append(dict(scenario=scen, level=lvl, metric=m, comparator=sysname,
                                atfa_mean=a[ok].mean(), comparator_mean=b[ok].mean(),
                                mean_diff=diff.mean(), diff_ci95_lo=lo, diff_ci95_hi=hi,
                                rank_biserial=rank_biserial(diff.to_numpy()),
                                atfa_better_in=f"{int((diff < 0).sum())}/{int(ok.sum())}", p=p))
            if res:
                adj = holm([r["p"] for r in res])
                for r, q in zip(res, adj):
                    r["p_holm"] = q
                rows += res
    return pd.DataFrame(rows)


def write_table(df, path_md, title, f):
    f.write(f"\n### {title}\n\n")
    f.write(df.to_markdown(index=False))
    f.write("\n")
    df.to_latex(path_md.with_suffix(".tex"), index=False, escape=True)


def fig_fvs_vs_level(fin, out):
    d = fin[fin.scenario == "id"]
    systems = ["B2 fixed amount threshold", "B4 trust only", "B3 detector only", "ATFA"]
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    for i, s in enumerate(systems):
        g = d[d.system == s].groupby("level").fvs_pct
        m, sd = g.mean() * 100, g.std().fillna(0) * 100
        c = SERIES[i]
        ax.plot(m.index * 100, m.values, marker="o", color=c, label=s)
        ax.fill_between(m.index * 100, (m - sd).clip(lower=0), m + sd, color=c, alpha=0.15, lw=0)
    ax.set_xlabel("Compromised assets (%)")
    ax.set_ylabel("Fraudulent value settled (% of attempted)")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=7)
    fig.savefig(out / "fig_fvs_vs_compromise.png")
    fig.savefig(out / "fig_fvs_vs_compromise.pdf")
    plt.close(fig)


def fig_tradeoff(sens, out):
    if sens.empty:
        return
    d = sens[sens.scenario == "id"]
    lv = sorted(d.level.unique())
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    for i, l in enumerate(lv):
        x = d[d.level == l]
        ax.scatter(x.legit_hold_rate * 100, x.fvs_pct * 100, s=14, color=SERIES[i], alpha=0.6,
                   label=f"{l * 100:.0f}% compromised", edgecolor="white", linewidth=0.5)
        sel = x[x.selected]
        ax.scatter(sel.legit_hold_rate * 100, sel.fvs_pct * 100, s=70, facecolor="none",
                   edgecolor=INK, linewidth=1.2)
    ax.set_xlabel("Legitimate claims held for verification (%)")
    ax.set_ylabel("Fraudulent value settled (%)")
    ax.set_title("Threshold sensitivity (test split; ring = validation-selected)", fontsize=8, color=INK2)
    ax.legend(fontsize=7)
    fig.savefig(out / "fig_threshold_tradeoff.png")
    fig.savefig(out / "fig_threshold_tradeoff.pdf")
    plt.close(fig)


def fig_trust(trust, out):
    d = trust[(trust.scenario == "id") & trust.system.isin(
        ["ATFA trust=static", "ATFA trust=ewma", "ATFA trust=beta", "ATFA"])]
    if d.empty:
        return
    order = ["ATFA trust=static", "ATFA trust=ewma", "ATFA trust=beta", "ATFA"]
    labels = ["Static", "EWMA", "Beta rep.", "ATFA"]
    g = d.groupby("system")
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6))
    for ax, col, ttl, k in [(axes[0], "low_trust_reach_rate", "Attacked assets reaching low trust (%)", 100),
                            (axes[1], "mean_trust_on_fraud", "Mean trust when submitting fraud", 1)]:
        m = g[col].mean().reindex(order) * k
        sd = g[col].std().reindex(order).fillna(0) * k
        yerr = np.vstack([np.minimum(sd.values, m.values), sd.values])   # rates cannot go below 0
        ax.bar(labels, m.values, yerr=yerr, color=SERIES[0], width=0.6,
               error_kw=dict(ecolor=INK2, lw=1, capsize=2))
        ax.set_title(ttl, fontsize=8, color=INK)
        ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(out / "fig_trust_comparison.png")
    fig.savefig(out / "fig_trust_comparison.pdf")
    plt.close(fig)


def fig_ablation(fin, out, level=0.2):
    d = fin[(fin.scenario == "id") & (fin.level == level)]
    if d.empty:
        return
    ref = d[d.system == "ATFA"].set_index("seed").total_cost
    rows = []
    for s in d[d.group.isin(["ablation", "trust"])].system.unique():
        x = d[d.system == s].set_index("seed").total_cost
        delta = (x - ref).dropna() / ref.reindex(x.index) * 100
        rows.append((s.replace("ATFA ", ""), delta.mean(), delta.std()))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(4.6, 0.28 * len(rows) + 0.8))
    names, m, sd = zip(*rows)
    ax.barh(names, m, xerr=sd, color=[SERIES[0] if v >= 0 else SERIES[1] for v in m], height=0.6,
            error_kw=dict(ecolor=INK2, lw=1, capsize=2))
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlabel(f"Change in total cost vs full ATFA (%), {level * 100:.0f}% compromised")
    ax.grid(axis="y", visible=False)
    fig.savefig(out / "fig_ablation.png")
    fig.savefig(out / "fig_ablation.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/full")
    args = ap.parse_args()
    R = Path(args.results)
    out = R / "report"
    out.mkdir(exist_ok=True)
    det = pd.read_csv(R / "detection.csv")
    fin = pd.read_csv(R / "financial.csv")
    trust = pd.read_csv(R / "trust.csv")
    sens = pd.read_csv(R / "sensitivity.csv") if (R / "sensitivity.csv").exists() else pd.DataFrame()
    world = pd.read_csv(R / "world.csv")

    with open(out / "report.md", "w", encoding="utf-8") as f:
        f.write(f"# ATFA results ({R.name})\n\nMean ± std over seeds. Values are measured on the test "
                "split with thresholds frozen on validation data.\n")
        wd = world.groupby(["scenario", "level"]).agg(
            worlds=("seed", "count"), claims=("n_claims", "mean"), anomaly_rate=("anomaly_rate", "mean"),
            fraud_claim_rate=("fraud_claim_rate", "mean"), hard_violation_rate=("hard_violation_rate", "mean"),
            runtime_s=("runtime_s", "mean")).reset_index().round(4)
        write_table(wd, out / "t0_worlds.md", "Simulated worlds", f)

        for scen in det.scenario.unique():
            d = det[det.scenario == scen]
            t = mstd(d, ["level", "detector"], DET_COLS)
            write_table(t, out / f"t1_detection_{scen}.md", f"Detection - {scen}", f)
        rc = [c for c in det.columns if c.startswith("recall[")]
        t = det[det.scenario == "id"].groupby("detector")[rc].mean().round(3).reset_index()
        write_table(t, out / "t2_recall_breakdown.md", "Detection recall by attack family / attacker knowledge (id, all levels)", f)
        fc = [c for c in det.columns if c.startswith("fpr[")]
        t = det[det.scenario == "id"].groupby("detector")[fc].mean().round(4).reset_index()
        write_table(t, out / "t3_fpr_benign.md", "False-positive rate by benign event type (id)", f)

        pct = {"fvs_pct", "fraud_block_rate", "legit_hold_rate", "legit_reject_rate"}
        for grp, title in [("main", "Financial protection - baselines vs ATFA"), ("trust", "Trust models"),
                           ("detector", "Detector choice inside ATFA"), ("ablation", "Ablations")]:
            if grp == "main":
                d = fin[fin.system.isin(MAIN_SYSTEMS)]
            else:
                d = fin[(fin.group == grp) | (fin.system == "ATFA")]
            for scen in d.scenario.unique():
                t = mstd(d[d.scenario == scen], ["level", "system"], FIN_COLS, pct=pct)
                write_table(t, out / f"t4_fin_{grp}_{scen}.md", f"{title} - {scen} (percentages for rates)", f)

        tc = ["honest_low_trust_rate", "low_trust_reach_rate", "median_days_to_low", "mean_trust_on_fraud",
              "mean_trust_on_legit"]
        d = trust[(trust.scenario == "id") & (trust.group.isin(["trust", "atfa", "baseline"]))]
        write_table(mstd(d, ["level", "system"], tc), out / "t5_trust.md", "Trust behaviour (id)", f)

        ff = [c for c in fin.columns if c.startswith("fvs_pct[")]
        d = fin[fin.system.isin(["B3 detector only", "ATFA"])]
        t = d.groupby(["scenario", "system"])[ff].mean().mul(100).round(1).reset_index()
        write_table(t, out / "t6_fvs_by_family.md", "Fraudulent value settled by attack family (%)", f)

        prim = paired_tests(fin, comparators=PRIMARY)
        if not prim.empty:
            write_table(prim.round(4), out / "t7a_primary_tests.md",
                        "PRIMARY (pre-registered) paired Wilcoxon tests, ATFA vs 3 comparators, Holm over 3", f)
        tests = paired_tests(fin)
        if not tests.empty:
            tests = tests.round(4)
            write_table(tests, out / "t7_wilcoxon.md", "Secondary: paired Wilcoxon tests vs all comparators (Holm over all)", f)
        feas = fin.groupby("system").calib_feasible.mean().round(3).reset_index()
        write_table(feas, out / "t8_calibration_feasibility.md",
                    "Share of worlds where validation calibration met the hold/reject budgets", f)

    fig_fvs_vs_level(fin, out)
    fig_tradeoff(sens, out)
    fig_trust(trust, out)
    fig_ablation(fin, out)
    print(f"report written to {out}")


if __name__ == "__main__":
    main()
