"""Run a single world and print its tables (for development and sanity checks).

    python scripts/debug_world.py --config configs/quick.yaml --scenario id --level 0.2 --seed 0
    python scripts/debug_world.py --set detectors.lstm_ae.train_on=train_all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.config import load_config  # noqa: E402
from atfa.experiment import run_world  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/quick.yaml")
    ap.add_argument("--scenario", default="id")
    ap.add_argument("--level", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append", default=[], help="dotted.key=yaml_value override")
    args = ap.parse_args()
    cfg = load_config(args.config)
    for kv in args.set:
        k, v = kv.split("=", 1)
        node = cfg
        *path, last = k.split(".")
        for p in path:
            node = node[p]
        node[last] = yaml.safe_load(v)
    scen = cfg["experiment"]["scenarios"].get(args.scenario, {"split": "chronological"})
    r = run_world(cfg, args.scenario, scen, args.level, args.seed)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    d = pd.DataFrame(r["detection"])
    print(d[["detector", "precision", "recall", "f1", "pr_auc", "fpr", "fit_s", "infer_ms_per_window",
             "episode_detect_rate"]].round(3).to_string())
    print(d[["detector"] + [c for c in d if c.startswith("recall[")]].round(2).to_string())
    f = pd.DataFrame(r["financial"])
    print(f[["system", "theta_approve", "theta_reject", "calib_feasible", "fvs_pct", "fraud_block_rate",
             "legit_hold_rate", "legit_reject_rate", "total_cost"]].round(3).to_string())
    print(pd.DataFrame(r["trust"]).drop(columns=["scenario", "level", "seed"]).round(3).to_string())
    print(r["world"][0])


if __name__ == "__main__":
    main()
