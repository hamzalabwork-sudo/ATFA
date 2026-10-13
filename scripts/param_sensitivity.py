"""One-at-a-time sensitivity of ATFA to its assumptions, on cached confirmatory worlds.

    python scripts/param_sensitivity.py --cache results/sensitivity_v2/pkl --workers 4

Each setting changes ONE parameter from configs/default.yaml; ATFA and the detector-only baseline
(B3) are re-calibrated on validation and evaluated on test under that setting. The cached worlds
reproduce results/confirmatory_v2 exactly at default settings (checked before use).
"""
from __future__ import annotations

import argparse
import copy
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.authorisation import calibrate, simulate  # noqa: E402
from atfa.config import load_config  # noqa: E402
from atfa.experiment import build_systems  # noqa: E402

SETTINGS = [
    ("default", None, None),
    *[("verification p_detect", ("authorisation", "verification", "p_detect"), v) for v in (0.8, 0.9, 1.0)],
    *[("verification delay (days)", ("authorisation", "verification", "delay_days"), v) for v in (1, 7, 14)],
    *[("legit hold budget", ("authorisation", "objective", "max_legit_hold"), v) for v in (0.025, 0.10)],
    *[("legit reject budget", ("authorisation", "objective", "max_legit_reject"), v) for v in (0.005, 0.02)],
    *[("trust forgetting gamma", ("trust", "atfa", "gamma"), v) for v in (0.95, 0.99)],
    *[("trust asymmetry kappa", ("trust", "atfa", "kappa"), v) for v in (1.0, 4.0)],
    *[("verification weight", ("trust", "atfa", "verify_weight"), v) for v in (2.0, 10.0)],
    *[("trust prior (a0, b0)", ("trust", "prior"), v) for v in ([4.0, 1.0], [16.0, 2.0])],
    *[("low-trust threshold", ("trust", "low"), v) for v in (0.5, 0.7)],
]


def _set(cfg, path, value):
    node = cfg
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value


def run_world(args):
    path, cfg0 = args
    w = pickle.loads(Path(path).read_bytes())
    k = w["key"]
    systems = {s.name: s for s in build_systems(cfg0)}
    rows = []
    for name, p, v in SETTINGS:
        cfg = copy.deepcopy(cfg0)
        if p:
            _set(cfg, p, v)
        for sysname in ("ATFA", "B3 detector only"):
            spec = systems[sysname]
            th, cap, feas = calibrate(spec, w["val"], cfg, w["v_from"], seed=k["seed"])
            m = simulate(spec, w["test"], cfg, th, cap, seed=k["seed"] + 1, eval_from=w["t_from"])
            rows.append(dict(k, parameter=name, value=str(v) if p else "default", system=sysname, feasible=feas,
                             fvs_pct=m["fvs_pct"], legit_hold_rate=m["legit_hold_rate"],
                             legit_reject_rate=m["legit_reject_rate"], total_cost=m["total_cost"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/sensitivity_v2/pkl")
    ap.add_argument("--config", default="configs/confirmatory_v2.yaml")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="results/sensitivity_v2")
    args = ap.parse_args()
    cfg = load_config(args.config)
    files = sorted(Path(args.cache).glob("*.pkl"))
    rows = []
    with ProcessPoolExecutor(args.workers) as pool:
        for r in pool.map(run_world, [(str(f), cfg) for f in files]):
            rows += r
    df = pd.DataFrame(rows)
    out = Path(args.out)
    df.to_csv(out / "param_sensitivity_raw.csv", index=False)
    piv = df.pivot_table(index=["parameter", "value", "level", "seed"], columns="system",
                         values=["fvs_pct", "legit_hold_rate", "total_cost"])
    s = pd.DataFrame({
        "ATFA fraud settled %": piv[("fvs_pct", "ATFA")] * 100,
        "B3 fraud settled %": piv[("fvs_pct", "B3 detector only")] * 100,
        "ATFA legit held %": piv[("legit_hold_rate", "ATFA")] * 100,
        "ATFA cost k": piv[("total_cost", "ATFA")] / 1e3,
        "B3 cost k": piv[("total_cost", "B3 detector only")] / 1e3,
        "ATFA fraud <= B3": (piv[("fvs_pct", "ATFA")] <= piv[("fvs_pct", "B3 detector only")]).astype(float),
    }).groupby(level=["parameter", "value"]).mean()
    feas = df[df.system == "ATFA"].groupby(["parameter", "value"]).feasible.mean().rename("ATFA budgets met")
    s = s.join(feas).round(3)
    order = [n for n, _, _ in SETTINGS]
    s = s.reset_index()
    s["_o"] = s.parameter.map({n: i for i, n in enumerate(dict.fromkeys(order))})
    s = s.sort_values(["_o", "value"]).drop(columns="_o")
    s.to_csv(out / "param_sensitivity.csv", index=False)
    (out / "param_sensitivity.md").write_text(
        "# One-at-a-time parameter sensitivity (cached confirmatory worlds: id 10 % and 20 %, seeds 20-29)\n\n"
        + s.to_markdown(index=False) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
