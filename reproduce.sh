#!/usr/bin/env bash
# Reproduces every result in the paper, in order. Approximate CPU times on a 12-core laptop.
# Usage: bash reproduce.sh [quick]      ("quick" runs the smoke protocol only, ~20 min)
set -euo pipefail
PY=${PY:-.venv/Scripts/python}      # Linux/macOS: PY=.venv/bin/python bash reproduce.sh
[ -x "$PY" ] || PY=.venv/bin/python

echo "== 0. tests (leakage guard, invariants, ledger, loaders)"
$PY -m pytest -q tests

if [ "${1:-}" = "quick" ]; then
  $PY scripts/run_experiments.py --config configs/quick.yaml --out results/quick
  $PY scripts/make_report.py --results results/quick
  exit 0
fi

echo "== 1. window length selection on selection worlds (~15 min)"
$PY scripts/select_window.py --models tcn,lstm --out results/window_selection.csv

echo "== 2. v1 evaluation, seeds 0-9 (development history, ~3 h)"
$PY scripts/run_experiments.py --config configs/default.yaml --out results/full
$PY scripts/make_report.py --results results/full

echo "== 3. v2 development on selection worlds 100-105 (~45 min)"
$PY scripts/run_experiments.py --config configs/dev_v2.yaml --out results/dev_v2
$PY scripts/run_experiments.py --config configs/dev_cache.yaml --out results/dev_cache
$PY scripts/dev_authorisation.py --cache results/dev_cache/pkl

echo "== 4. CONFIRMATORY v2 evaluation, fresh seeds 20-39 (~3 h)"
$PY scripts/run_experiments.py --config configs/confirmatory_v2.yaml --out results/confirmatory_v2
$PY scripts/make_report.py --results results/confirmatory_v2
$PY scripts/cost_sensitivity.py --results results/confirmatory_v2

echo "== 5. parameter sensitivity on cached confirmatory worlds (~1 h)"
$PY scripts/run_experiments.py --config configs/cache_confirmatory.yaml --out results/sensitivity_v2
$PY scripts/param_sensitivity.py --cache results/sensitivity_v2/pkl --workers 4
$PY scripts/make_sensitivity_figure.py

echo "== 6. robustness: harsher benign conditions, 5x fleet (~1.5 h)"
$PY scripts/run_experiments.py --config configs/robustness_v2.yaml --out results/robustness_v2
$PY scripts/make_report.py --results results/robustness_v2

echo "== 7. public benchmarks (data in data/ton_iot and data/edge_iiotset)"
$PY scripts/run_public.py ton_iot --data data/ton_iot/Processed_IoT_dataset --out results/public_v2 --seeds 0,1,2 --protocols blocked --workers 4
$PY scripts/run_public.py ton_iot --data data/ton_iot/Processed_IoT_dataset --out results/public --seeds 0,1,2 --protocols novelty --workers 4
$PY scripts/run_public.py edge_iiot --data data/edge_iiotset/ML-EdgeIIoT-dataset.csv --out results/public --seeds 0,1,2
$PY scripts/make_public_report.py --results results/public_v2

echo "== 8. computational overhead"
$PY scripts/bench_decision.py --out results/overhead

echo "== 9. PureChain PoA² (needs network access; deploy once, then benchmark)"
echo "   $PY scripts/purechain_deploy.py --admin <admin wallet>"
echo "   $PY scripts/bench_ledger.py --adapter purechain --out results/purechain"
echo "   $PY scripts/purechain_bench_setup.py --accounts 4 && $PY scripts/bench_ledger.py --only E5 --out results/purechain"
echo "   PYTHONPATH=scripts $PY scripts/make_ledger_report.py --results results/purechain"
