"""Run the ATFA experimental protocol.

    python scripts/run_experiments.py --config configs/default.yaml --out results/full
    python scripts/run_experiments.py --config configs/quick.yaml   --out results/quick

Each world (scenario, compromise level, seed) is written to <out>/worlds/*.json, so an
interrupted run resumes where it stopped. Tables are merged into <out>/*.csv at the end.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

# One BLAS thread per worker process; parallelism comes from the process pool and torch threads.
for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.config import load_config  # noqa: E402
from atfa.experiment import run_world  # noqa: E402

TABLES = ("detection", "financial", "trust", "sensitivity", "world")


def _job(cfg, scen_name, scen, level, seed, path):
    res = run_world(cfg, scen_name, scen, level, seed, log=lambda m: print(m, flush=True))
    Path(path).write_text(json.dumps(res, default=float))
    return path


def merge(out: Path):
    parts = {t: [] for t in TABLES}
    for f in sorted((out / "worlds").glob("*.json")):
        res = json.loads(f.read_text())
        for t in TABLES:
            parts[t].extend(res.get(t, []))
    for t, rows in parts.items():
        if rows:
            pd.DataFrame(rows).to_csv(out / f"{t}.csv", index=False)
    print(f"merged {len(list((out / 'worlds').glob('*.json')))} worlds into {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="results/full")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--only", help="comma-separated scenario names")
    ap.add_argument("--merge-only", action="store_true", help="merge finished worlds into CSVs and exit")
    args = ap.parse_args()
    if args.merge_only:
        merge(Path(args.out))
        return

    cfg = load_config(args.config)
    out = Path(args.out)
    (out / "worlds").mkdir(parents=True, exist_ok=True)
    (out / "config.resolved.json").write_text(json.dumps(cfg, indent=2))
    ex = cfg["experiment"]
    only = set(args.only.split(",")) if args.only else None

    jobs = []
    for sname, scen in ex["scenarios"].items():
        if only and sname not in only:
            continue
        for level in scen["levels"]:
            for seed in scen.get("seeds", ex["seeds"]):
                p = out / "worlds" / f"{sname}__L{level:.2f}__s{seed}.json"
                if not p.exists():
                    jobs.append((sname, scen, level, seed, str(p)))
    print(f"{len(jobs)} worlds to run")
    t0 = time.time()
    workers = args.workers or ex.get("workers", 1)
    if workers <= 1:
        for j in jobs:
            _job(cfg, *j)
    else:
        with ProcessPoolExecutor(workers) as pool:
            futs = {pool.submit(_job, cfg, *j): j for j in jobs}
            failed = 0
            for i, f in enumerate(as_completed(futs), 1):
                try:
                    f.result()
                    status = "ok"
                except Exception as e:  # keep going; rerunning the command retries missing worlds
                    failed += 1
                    status = f"FAILED {futs[f][0]} L={futs[f][2]} s={futs[f][3]}: {type(e).__name__}: {str(e)[:120]}"
                print(f"[{i}/{len(jobs)}] {(time.time() - t0) / 60:.1f} min elapsed {status}", flush=True)
            if failed:
                print(f"{failed} worlds failed; rerun the same command to retry them", flush=True)
    merge(out)


if __name__ == "__main__":
    main()
