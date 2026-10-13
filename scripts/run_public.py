"""Detection experiments on public datasets.

    python scripts/run_public.py ton_iot  --data data/ton_iot   --out results/public --seeds 0,1,2
    python scripts/run_public.py edge_iiot --data data/edge_iiotset/DNN-EdgeIIoT-dataset.csv --out results/public

TON_IoT: every *.csv in --data is one device stream (see atfa/public.py). For each stream, the
same detectors, calibration and val_policy-selected thresholds as the ATFA experiments are used.
Unsupervised models (Isolation Forest, LSTM-AE) are trained on train-split rows labelled normal
(semi-supervised novelty detection), because TON_IoT has no attack-free commissioning period.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.config import load_config  # noqa: E402
from atfa.detectors import REGISTRY, FitContext, HybridStacker, Platt, Split, timed_score  # noqa: E402
from atfa.metrics import best_f1_threshold, detection_metrics  # noqa: E402
from atfa.public import blocked_split, load_edge_iiot, load_ton_iot_file  # noqa: E402
from atfa.windows import WindowStore  # noqa: E402

TON_MODELS = ("iforest", "xgboost", "lstm", "tcn", "lstm_ae", "hybrid", "tcn_xgb")


def run_ton_stream(path, cfg, seed, W, protocol="blocked", max_train=60_000):
    """One TON_IoT device stream.

    blocked: 1-hour blocks assigned to train/val_calib/val_policy/test (attack and attack-free
             blocks stratified), first W rows of each block embargoed; all models.
    novelty: strictly chronological 60/20/20; label-free models only (Isolation Forest, LSTM-AE)
             trained on the attack-free first 60 %; calibration + threshold on [60 %, 80 %).
    """
    X, y, typ, feats, ts = load_ton_iot_file(path, return_ts=True)
    N = len(y)
    rng = np.random.default_rng(seed)
    if protocol == "blocked":
        tr_i, vc_i, vp_i, te_i = blocked_split(ts, y, W, seed=seed)
        models = TON_MODELS
    else:
        b = [int(0.6 * N), int(0.8 * N)]
        tr_i, vc_i, te_i = np.arange(W, b[0]), np.arange(b[0], b[1]), np.arange(b[1], N)
        vp_i = vc_i
        models = ("iforest", "lstm_ae")
    mask = np.zeros((1, N), bool)
    mask[0, tr_i] = True
    store = WindowStore.fit(X[None], W, mask)
    mk = lambda idx: Split(np.zeros(len(idx), int), idx, y[idx])
    tr_fit = tr_i if len(tr_i) <= max_train else np.sort(rng.choice(tr_i, max_train, replace=False))
    tr_norm = tr_i[y[tr_i] == 0]
    tr_norm = tr_norm if len(tr_norm) <= max_train else np.sort(rng.choice(tr_norm, max_train, replace=False))
    tr, vc, vp, te = mk(tr_fit), mk(vc_i), mk(vp_i), mk(te_i)
    base = dict(dataset="TON_IoT", protocol=protocol, stream=Path(path).stem, seed=seed, n_rows=N,
                n_features=len(feats), n_train=len(tr_i), n_test=len(te_i),
                **{f"pos_{k}": int(v.y.sum()) for k, v in zip(("train", "val_calib", "val_policy", "test"),
                                                             (mk(tr_i), vc, vp, te))})
    need_sup = any(m in ("xgboost", "lstm", "tcn", "hybrid", "tcn_xgb") for m in models)
    if (need_sup and tr.y.sum() == 0) or vc.y.sum() == 0 or te.y.sum() == 0 or (te.y == 0).all():
        return [dict(base, detector="(skipped: a split lacks one class)")]
    ctx = FitContext(store, tr, vc, mk(tr_norm), cfg["detectors"], seed)
    raw = {}
    for name in [m for m in models if m not in ("hybrid", "tcn_xgb")]:
        det = REGISTRY[name]().fit(ctx)
        allidx = np.concatenate([vc_i, vp_i, te_i]) if protocol == "blocked" else np.concatenate([vc_i, te_i])
        allidx = np.unique(allidx)
        r, ms = timed_score(det, store, np.zeros(len(allidx), int), allidx)
        full = np.full(N, np.nan)
        full[allidx] = r
        raw[name] = (full, det.transform, ms, det.n_params())
    prob = {n: Platt(tf).fit(r[vc_i], vc.y)(np.nan_to_num(r)) for n, (r, tf, _, _) in raw.items()}
    if "hybrid" in models:
        hs = HybridStacker().fit(raw["tcn"][0][vc_i], raw["lstm_ae"][0][vc_i], vc.y)
        prob["hybrid"] = hs(np.nan_to_num(raw["tcn"][0], nan=0.5), np.nan_to_num(raw["lstm_ae"][0], nan=1.0))
    if "tcn_xgb" in models:
        ens = HybridStacker(kinds=("logit", "logit")).fit(raw["tcn"][0][vc_i], raw["xgboost"][0][vc_i], vc.y)
        prob["tcn_xgb"] = ens(np.nan_to_num(raw["tcn"][0], nan=0.5), np.nan_to_num(raw["xgboost"][0], nan=0.5))
    rows = []
    for name, p in prob.items():
        thr = best_f1_threshold(vp.y, p[vp_i])
        pt = p[te_i]
        row = dict(base, detector=name, **detection_metrics(te.y, pt, thr),
                   infer_ms_per_window=raw[name][2] if name in raw else np.nan)
        for t in np.unique(typ[te_i]):
            if t != "normal":
                m = typ[te_i] == t
                row[f"recall[{t}]"] = float((pt[m] >= thr).mean())
        rows.append(row)
    return rows


def _ton_job(args):
    f, cfg, seed, W, protocol = args
    import torch
    torch.set_num_threads(cfg["detectors"]["deep"]["threads"])
    print(f"start {Path(f).stem} seed={seed} {protocol}", flush=True)
    rows = run_ton_stream(f, cfg, seed, W, protocol)
    print(f"done  {Path(f).stem} seed={seed} {protocol}", flush=True)
    return rows


def run_edge(path, cfg, seed):
    from sklearn.ensemble import IsolationForest
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier
    X, yb, yt, feats, n_dup = load_edge_iiot(path)
    idx = np.arange(len(yb))
    tr, rest = train_test_split(idx, test_size=0.4, stratify=yt, random_state=seed)
    va, te = train_test_split(rest, test_size=0.5, stratify=yt[rest], random_state=seed)
    base = dict(dataset="Edge-IIoTset", seed=seed, n_rows=len(yb), n_features=len(feats), duplicates_removed=n_dup)
    rows = []
    xgb = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                        eval_metric="aucpr", early_stopping_rounds=30, random_state=seed, n_jobs=4,
                        tree_method="hist").fit(X[tr], yb[tr], eval_set=[(X[va], yb[va])], verbose=False)
    p = xgb.predict_proba(X)[:, 1]
    rows.append(dict(base, detector="xgboost", **detection_metrics(yb[te], p[te], best_f1_threshold(yb[va], p[va]))))
    iso = IsolationForest(n_estimators=200, random_state=seed, n_jobs=4).fit(X[tr][yb[tr] == 0])
    r = -iso.score_samples(X)
    pi = Platt("identity").fit(r[va], yb[va])(r)
    rows.append(dict(base, detector="iforest", **detection_metrics(yb[te], pi[te], best_f1_threshold(yb[va], pi[va]))))
    classes, ytc = np.unique(yt, return_inverse=True)
    mc = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, random_state=seed, n_jobs=4,
                       tree_method="hist", early_stopping_rounds=30).fit(
        X[tr], ytc[tr], eval_set=[(X[va], ytc[va])], verbose=False)
    pred = mc.predict(X[te])
    from sklearn.metrics import f1_score
    rows.append(dict(base, detector="xgboost_multiclass", macro_f1=f1_score(ytc[te], pred, average="macro"),
                     n_classes=len(classes)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", choices=["ton_iot", "edge_iiot"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="results/public")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--protocols", default="blocked,novelty")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--epochs", type=int, default=10, help="deep-model epochs for public streams")
    args = ap.parse_args()
    cfg = load_config(args.config)
    cfg["detectors"]["deep"]["epochs"] = args.epochs
    cfg["detectors"]["deep"]["patience"] = 3
    cfg["detectors"]["lstm_ae"]["epochs"] = args.epochs
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds = list(map(int, args.seeds.split(",")))
    rows = []
    if args.dataset == "ton_iot":
        files = sorted(Path(args.data).rglob("*.csv"))
        if not files:
            sys.exit(f"no CSV files under {args.data}")
        jobs = [(str(f), cfg, s, cfg["windows"]["length"], pr) for pr in args.protocols.split(",")
                for s in seeds for f in files]
        if args.workers > 1:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(args.workers) as pool:
                for r in pool.map(_ton_job, jobs):
                    rows += r
        else:
            for j in jobs:
                rows += _ton_job(j)
    else:
        for seed in seeds:
            rows += run_edge(args.data, cfg, seed)
    df = pd.DataFrame(rows)
    df.to_csv(out / f"{args.dataset}_detection.csv", index=False)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
