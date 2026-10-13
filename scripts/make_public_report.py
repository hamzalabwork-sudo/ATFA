"""Tables for the public benchmarks (TON_IoT telemetry, Edge-IIoTset).

    python scripts/make_public_report.py --results results/public
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ORDER = ["iforest", "xgboost", "lstm", "tcn", "lstm_ae", "hybrid", "tcn_xgb"]


def pm(g, col):
    m, s = g[col].mean(), g[col].std().fillna(0)
    return m.map("{:.3f}".format) + " ± " + s.map("{:.3f}".format)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/public")
    args = ap.parse_args()
    R = Path(args.results)
    out = R / "report"
    out.mkdir(exist_ok=True)
    with open(out / "public_report.md", "w", encoding="utf-8") as f:
        f.write("# Public benchmarks (mean ± std over seeds)\n")
        ton = R / "ton_iot_detection.csv"
        if ton.exists():
            d = pd.read_csv(ton)
            d = d[~d.detector.str.startswith("(")]
            for proto in d.protocol.unique():
                x = d[d.protocol == proto]
                for metric in ("roc_auc", "pr_auc", "f1"):
                    g = x.groupby(["stream", "detector"])
                    t = pm(g, metric).unstack("detector")
                    t = t[[c for c in ORDER if c in t.columns]]
                    f.write(f"\n### TON_IoT telemetry - {proto} protocol - {metric}\n\n")
                    f.write(t.to_markdown())
                    f.write("\n")
                base = x.groupby("stream")[["n_rows", "pos_train", "pos_test", "n_test"]].first()
                base["test_attack_rate"] = (base.pos_test / base.n_test).round(3)
                f.write(f"\n### TON_IoT - {proto} protocol - split composition\n\n{base.to_markdown()}\n")
        edge = R / "edge_iiot_detection.csv"
        if edge.exists():
            d = pd.read_csv(edge)
            cols = [c for c in ["precision", "recall", "f1", "pr_auc", "roc_auc", "fpr", "macro_f1"] if c in d]
            g = d.groupby("detector")
            t = pd.DataFrame({c: pm(g, c) for c in cols})
            f.write(f"\n### Edge-IIoTset (leakage fields dropped; {int(d.duplicates_removed.iloc[0])} duplicates "
                    f"removed; {int(d.n_rows.iloc[0])} records)\n\n{t.to_markdown()}\n")
    print(f"public report written to {out}")


if __name__ == "__main__":
    main()
