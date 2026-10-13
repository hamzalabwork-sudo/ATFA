"""Development comparison of authorisation rules on cached SELECTION-world scores.

    python scripts/dev_authorisation.py --cache results/dev_cache/pkl

Each variant is calibrated on the validation window and evaluated on the test window of the
selection worlds (seeds 100+), exactly as in the main protocol. Used only to choose the design
that is then evaluated once on fresh seeds (configs/confirmatory_v2.yaml).
"""
from __future__ import annotations

import argparse
import copy
import pickle
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.authorisation import SystemSpec, calibrate, simulate  # noqa: E402
from atfa.config import load_config  # noqa: E402


def variants(det):
    V = {
        "B3 detector only": (SystemSpec("B3", detector=det, trust="none", risk="detector", use_F=False,
                                        gate=False), {}),
        "noisy-OR with F (v2 current)": (SystemSpec("a", detector=det, audit=False), {}),
        "noisy-OR without F": (SystemSpec("b", detector=det, use_F=False, audit=False), {}),
        "noisy-OR with F + audits": (SystemSpec("c", detector=det), {}),
    }
    for lam in (0.3, 0.5, 0.7):
        V[f"expected-loss lambda={lam}"] = (SystemSpec("d", detector=det, risk="expected_loss", audit=False),
                                            {"el_floor": lam})
    V["expected-loss lambda=0.5, beta trust"] = (SystemSpec("e", detector=det, risk="expected_loss", trust="beta",
                                                            audit=False), {"el_floor": 0.5})
    V["expected-loss lambda=0.5, no trust"] = (SystemSpec("f", detector=det, risk="expected_loss", trust="none",
                                                          audit=False), {"el_floor": 0.5})
    return V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/dev_cache/pkl")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--detectors", default="tcn,tcn_xgb")
    args = ap.parse_args()
    base = load_config(args.config)
    rows = []
    for f in sorted(Path(args.cache).glob("*.pkl")):
        w = pickle.loads(f.read_bytes())
        for det in args.detectors.split(","):
            for name, (spec, au_over) in variants(det).items():
                cfg = copy.deepcopy(base)
                cfg["authorisation"].update(au_over)
                theta, cap, feas = calibrate(spec, w["val"], cfg, w["v_from"], seed=w["key"]["seed"])
                m = simulate(spec, w["test"], cfg, theta, cap, seed=w["key"]["seed"] + 1, eval_from=w["t_from"])
                rows.append(dict(w["key"], detector=det, variant=name, feasible=feas, fvs_pct=m["fvs_pct"] * 100,
                                 legit_hold=m["legit_hold_rate"] * 100, legit_rej=m["legit_reject_rate"] * 100,
                                 cost_k=m["total_cost"] / 1e3))
        print("done", f.name, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(Path(args.cache).parent / "dev_authorisation.csv", index=False)
    pd.set_option("display.width", 250)
    for det in df.detector.unique():
        d = df[df.detector == det]
        print(f"\n=== detector {det}: mean over worlds ===")
        t = d.groupby("variant")[["fvs_pct", "legit_hold", "legit_rej", "cost_k", "feasible"]].mean()
        t["cost_by_scen"] = d.groupby(["variant", "scenario", "level"]).cost_k.mean().unstack([1, 2]).round(1) \
            .astype(str).agg(" | ".join, axis=1)
        print(t.sort_values("cost_k").round(2).to_string())


if __name__ == "__main__":
    main()
