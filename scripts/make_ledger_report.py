"""Tables and figures for the PureChain PoA² measurements.

    python scripts/make_ledger_report.py --results results/purechain
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from make_report import INK2, SERIES  # noqa: E402  (shared palette and rcParams)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/purechain")
    args = ap.parse_args()
    R = Path(args.results)
    out = R / "report"
    out.mkdir(exist_ok=True)
    parts = [pd.read_csv(f) for f in sorted(R.glob("ledger_bench*.csv"))]
    df = pd.concat(parts, ignore_index=True)
    dep = json.loads(Path("deployments/purechain.json").read_text())

    e1 = df[df.experiment == "E1 sequential"]
    e2 = df[df.experiment == "E2 batching"].sort_values("records_per_tx")
    # the open-loop E3 sweep supersedes the closed-loop E3 of the first run (client-limited)
    e3 = df[df.experiment.str.startswith("E3") & df.get("senders", pd.Series(dtype=float)).notna()]
    e5 = df[df.experiment.str.startswith("E5")]
    e4 = df[df.experiment.str.startswith("E4")]

    with open(out / "ledger_report.md", "w", encoding="utf-8") as f:
        f.write("# PureChain PoA² measurements\n\n")
        f.write(f"Contract `{dep['address']}` (chain {dep['chain_id']}, deployment gas {dep['gas_used']}, "
                f"block {dep['block']}). Gas in EVM units; the fee is zero on this network. "
                "Finality = inclusion (on-demand authority-sealed blocks).\n\n")
        for title, d, cols in [
            ("E1 confirmation latency (sequential single anchors)", e1,
             ["n_tx", "ok", "latency_ms_p50", "latency_ms_p95", "latency_ms_mean", "gas_per_record", "tx_bytes"]),
            ("E2 batching", e2, ["records_per_tx", "n_tx", "ok", "latency_ms_p50", "latency_ms_p95", "gas_per_record",
                                 "records_per_s_sequential"]),
            ("E3 sustained offered load (one authoriser account)", e3,
             ["experiment", "records_per_tx", "offered_tps", "sent", "ok", "failed_or_timeout", "throughput_tps",
              "throughput_records_per_s", "latency_ms_p50", "latency_ms_p95", "latency_ms_p99", "mean_tx_per_block"]),
            ("E5 per-sender limit: 1 vs N authoriser accounts", e5,
             ["experiment", "offered_tps", "sent", "ok", "failed_or_timeout", "throughput_tps", "latency_ms_p50",
              "latency_ms_p95", "mean_tx_per_block"]),
            ("E4 pre-settlement check (isSettleable eth_call)", e4, ["n_tx", "latency_ms_p50", "latency_ms_p95"]),
        ]:
            if len(d):
                f.write(f"\n### {title}\n\n")
                f.write(d[[c for c in cols if c in d]].round(1).to_markdown(index=False))
                f.write("\n")

    # Figure: confirmation latency vs offered load, 1 vs N sender accounts
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    for i, (name, g) in enumerate(e5.groupby("experiment")):
        g = g.sort_values("offered_tps")
        lbl = name.replace("E5 multi-account ", "").strip("()").replace("1 senders", "1 sender")
        ax.plot(g.offered_tps, g.latency_ms_p50 / 1000, marker="o", color=SERIES[i], label=f"{lbl}, p50")
        ax.plot(g.offered_tps, g.latency_ms_p95 / 1000, marker="o", ls="--", color=SERIES[i], label=f"{lbl}, p95",
                alpha=0.7)
    ax.set_xlabel("Offered load (anchor transactions / s)")
    ax.set_ylabel("Confirmation latency (s)")
    ax.set_yscale("log")
    ax.legend(fontsize=7)
    fig.savefig(out / "fig_ledger_latency_vs_load.png")
    fig.savefig(out / "fig_ledger_latency_vs_load.pdf")
    plt.close(fig)

    # Figure: gas per record vs batch size
    if len(e2):
        fig, ax = plt.subplots(figsize=(4.2, 2.8))
        ax.plot(e2.records_per_tx, e2.gas_per_record / 1000, marker="o", color=SERIES[0])
        for x, y in zip(e2.records_per_tx, e2.gas_per_record / 1000):
            ax.annotate(f"{y:.1f}k", (x, y), textcoords="offset points", xytext=(4, 6), fontsize=7, color=INK2)
        ax.set_xscale("log")
        ax.set_xlabel("Records per transaction (batch size)")
        ax.set_ylabel("Gas per anchored record (×1000)")
        ax.set_ylim(bottom=0)
        fig.savefig(out / "fig_ledger_gas_vs_batch.png")
        fig.savefig(out / "fig_ledger_gas_vs_batch.pdf")
        plt.close(fig)
    print(f"ledger report written to {out}")


if __name__ == "__main__":
    main()
