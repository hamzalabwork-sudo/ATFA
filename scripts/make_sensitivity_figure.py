"""Dot plot of ATFA vs detector-only fraud settled under one-at-a-time parameter changes.

    python scripts/make_sensitivity_figure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_report import INK2, SERIES  # noqa: E402

s = pd.read_csv("results/sensitivity_v2/param_sensitivity.csv")
s["label"] = s.apply(lambda r: "default" if r.parameter == "default" else f"{r.parameter} = {r.value}", axis=1)
s = s.iloc[::-1].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(5.2, 0.24 * len(s) + 0.9))
y = range(len(s))
for i, r in s.iterrows():
    ax.plot([r["ATFA fraud settled %"], r["B3 fraud settled %"]], [i, i], color="#c3c2b7", lw=1, zorder=1)
ax.scatter(s["B3 fraud settled %"], y, s=30, color=SERIES[1], label="Detector only (B3)", zorder=2,
           edgecolor="white", linewidth=0.8)
ax.scatter(s["ATFA fraud settled %"], y, s=30, color=SERIES[0], label="ATFA", zorder=3, edgecolor="white",
           linewidth=0.8)
ax.set_yticks(list(y))
ax.set_yticklabels(s.label, fontsize=7)
ax.set_xlabel("Fraudulent value settled (%), cached confirmatory worlds")
ax.set_xlim(left=0)
ax.grid(axis="y", visible=False)
ax.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
ax.axhline(len(s) - 1 - 0.5, color=INK2, lw=0.6)
out = Path("results/sensitivity_v2")
fig.savefig(out / "fig_param_sensitivity.png")
fig.savefig(out / "fig_param_sensitivity.pdf")
print("saved", out / "fig_param_sensitivity.png")
