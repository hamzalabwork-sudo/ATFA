"""Computational overhead of the ATFA decision path (per claim), for edge/server deployment.

    python scripts/bench_decision.py --out results/overhead

Measures on this host (CPU only):
  - detector inference latency for ONE claim (batch size 1) and amortised over a daily batch
    (TCN, XGBoost, TCN+XGBoost ensemble);
  - trust update + risk + decision per claim (vectorised daily step) for fleets of 100-10,000 assets;
  - evidence-record digest (SHA-256) per claim;
  - memory: model sizes and per-asset state.
Models are trained briefly (timing does not depend on accuracy); detection quality is reported elsewhere.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.authorisation import risk_score  # noqa: E402
from atfa.config import load_config  # noqa: E402
from atfa.detectors import REGISTRY, FitContext, HybridStacker, Split  # noqa: E402
from atfa.features import FEATURES, build_features, observable_view, to_tensor  # noqa: E402
from atfa.generator import generate_world  # noqa: E402
from atfa.ledger import EvidenceRecord  # noqa: E402
from atfa.trust import ATFATrust  # noqa: E402
from atfa.windows import WindowStore, index_grid  # noqa: E402


def timeit(fn, reps):
    fn()
    t = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t) / reps * 1000  # ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="results/overhead")
    ap.add_argument("--threads", type=int, default=1)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    cfg = load_config(args.config)
    cfg["detectors"]["deep"]["epochs"] = 2
    g = copy.deepcopy(cfg["generator"])
    g["compromise_fraction"] = 0.2
    rec, assets = generate_world(g, 7)
    rec = rec.sort_values(["asset_id", "day"]).reset_index(drop=True)
    A, D, W = g["n_assets"], g["n_days"], cfg["windows"]["length"]
    sp = cfg["splits"]
    t0 = time.perf_counter()
    X = to_tensor(build_features(observable_view(rec), assets, g["commissioning_days"]), A, D)
    feat_ms_per_report = (time.perf_counter() - t0) * 1000 / (A * D)
    y = rec.anomaly_label.to_numpy().reshape(A, D)
    mask = np.zeros((A, D), bool)
    mask[:, :sp["train_end"]] = True
    store = WindowStore.fit(X, W, mask)
    mk = lambda lo, hi: Split(*index_grid(np.arange(A), lo, hi))
    tr, vc = mk(0, sp["train_end"]), mk(sp["train_end"], sp["val_split"])
    tr.y, vc.y = y[tr.a, tr.t], y[vc.a, vc.t]
    ctx = FitContext(store, tr, vc, mk(10, g["commissioning_days"]), cfg["detectors"], 0)
    tcn = REGISTRY["tcn"]().fit(ctx)
    xgb = REGISTRY["xgboost"]().fit(ctx)
    ens = HybridStacker(("logit", "logit")).fit(tcn.score(store, vc.a, vc.t), xgb.score(store, vc.a, vc.t), vc.y)
    xgb.m.set_params(n_jobs=args.threads)

    a1, t1 = np.array([3]), np.array([600])
    ab, tb = index_grid(np.arange(A), 600, 601)         # one day's claims for the whole fleet
    rows = []
    for name, fn1, fnb in [
        ("TCN", lambda: tcn.score(store, a1, t1), lambda: tcn.score(store, ab, tb)),
        ("XGBoost", lambda: xgb.score(store, a1, t1), lambda: xgb.score(store, ab, tb)),
        ("TCN+XGBoost ensemble",
         lambda: ens(tcn.score(store, a1, t1), xgb.score(store, a1, t1)),
         lambda: ens(tcn.score(store, ab, tb), xgb.score(store, ab, tb))),
    ]:
        rows.append(dict(component=f"detector: {name}", single_claim_ms=timeit(fn1, 200),
                         per_claim_in_daily_batch_ms=timeit(fnb, 50) / len(ab)))

    tc = cfg["trust"]
    for n in (100, 1_000, 10_000):
        tm = ATFATrust(n, tc)
        rng = np.random.default_rng(0)
        s = rng.random(n) * 0.1
        z, one = np.zeros(n), np.ones(n, bool)

        def step():
            T = tm.value()
            R = risk_score("noisy_or", T, s, z, None)
            dec = np.where(R < 0.3, 0, np.where(R < 0.6, 1, 2))
            dec = np.where(T < tc["low"], np.maximum(dec, 1), dec)
            tm.update(s, z, one, z, z, one)
            return dec

        rows.append(dict(component=f"trust + risk + decision (fleet {n})", single_claim_ms=np.nan,
                         per_claim_in_daily_batch_ms=timeit(step, 200) / n))
    er = EvidenceRecord("EQ-0003", 600, 1600, "ab" * 32, 760.0, 0.93, 0.02, 0.0, 0.09, "approve", "atfa-v2")
    rows.append(dict(component="evidence digest (SHA-256)", single_claim_ms=timeit(er.digest, 2000),
                     per_claim_in_daily_batch_ms=np.nan))
    rows.append(dict(component="daily feature extraction (batch, per report)", single_claim_ms=np.nan,
                     per_claim_in_daily_batch_ms=feat_ms_per_report))

    buf = io.BytesIO()
    torch.save(tcn.model.state_dict(), buf)
    mem = dict(tcn_params=int(tcn.n_params()), tcn_state_bytes=buf.tell(),
               xgboost_model_bytes=len(xgb.m.get_booster().save_raw("ubj")),
               ensemble_stacker_bytes=len(pickle.dumps(ens)),
               per_asset_state_bytes=int(W * len(FEATURES) * 4 + 2 * 8 + 28 * 8),
               per_asset_state_note="window (W x features, float32) + trust (alpha, beta) + 28-day history")
    try:
        import psutil
        mem["process_rss_mb"] = psutil.Process(os.getpid()).memory_info().rss / 2**20
    except Exception:
        pass
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "decision_overhead.csv", index=False)
    (out / "memory.json").write_text(json.dumps(mem, indent=2))
    pd.set_option("display.width", 200)
    print(df.round(4).to_string(index=False))
    print(json.dumps(mem, indent=2))


if __name__ == "__main__":
    main()
