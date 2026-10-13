"""Select the window length W on validation data only (val_policy PR-AUC of the primary detector).

    python scripts/select_window.py --config configs/default.yaml --out results/window_selection.csv

Uses dedicated selection worlds (seeds 100+) so the chosen W is independent of the evaluation seeds.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.config import load_config  # noqa: E402
from atfa.detectors import REGISTRY, FitContext, Split  # noqa: E402
from atfa.features import build_features, observable_view, to_tensor  # noqa: E402
from atfa.generator import generate_world  # noqa: E402
from atfa.windows import WindowStore, index_grid  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--lengths", default="20,40,60")
    ap.add_argument("--seeds", default="100,101")
    ap.add_argument("--level", type=float, default=0.2)
    ap.add_argument("--models", default=None, help="default: primary detector")
    ap.add_argument("--out", default="results/window_selection.csv")
    args = ap.parse_args()
    cfg = load_config(args.config)
    sp = cfg["splits"]
    models = args.models.split(",") if args.models else [cfg["detectors"]["primary"]]
    rows = []
    for seed in map(int, args.seeds.split(",")):
        g = copy.deepcopy(cfg["generator"])
        g["compromise_fraction"] = args.level
        rec, assets = generate_world(g, seed)
        rec = rec.sort_values(["asset_id", "day"]).reset_index(drop=True)
        A, D = g["n_assets"], g["n_days"]
        X = to_tensor(build_features(observable_view(rec), assets), A, D)
        y = rec.anomaly_label.to_numpy().reshape(A, D)
        mask = np.zeros((A, D), bool)
        mask[:, :sp["train_end"]] = True
        for W in map(int, args.lengths.split(",")):
            store = WindowStore.fit(X, W, mask)
            sl = lambda lo, hi: Split(*index_grid(np.arange(A), lo, hi), None)
            tr, vc, vp = sl(0, sp["train_end"]), sl(sp["train_end"], sp["val_split"]), sl(sp["val_split"], sp["val_end"])
            for s in (tr, vc, vp):
                s.y = y[s.a, s.t]
            nm = sl(10, g["commissioning_days"])
            ctx = FitContext(store, tr, vc, nm, cfg["detectors"], seed)
            for m in models:
                det = REGISTRY[m]().fit(ctx)
                ap_ = average_precision_score(vp.y, det.score(store, vp.a, vp.t))
                rows.append(dict(seed=seed, W=W, model=m, val_policy_pr_auc=ap_))
                print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    summ = df.groupby(["model", "W"]).val_policy_pr_auc.agg(["mean", "std"])
    print(summ)
    best = summ["mean"].groupby(level=0).idxmax()
    print("selected W:", {m: w for m, (_, w) in best.items()})


if __name__ == "__main__":
    main()
