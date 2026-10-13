# Confirmatory plan — ATFA v2

Written on 2026-10-12, **before** the confirmatory run (`configs/confirmatory_v2.yaml`). Nothing
below may be changed after results are seen; deviations must be reported as such.

## Why a v2 and how it was developed
The first full evaluation (seeds 0–9, `results/full/`, reported in `docs/results_summary.md`)
identified weaknesses. Changes were developed **only on selection worlds** (seeds 100–105, disjoint
from every evaluation seed), and evaluated here once on **fresh seeds 20–39**.

| Change | Motivation (from v1) | Development evidence (selection worlds) |
|---|---|---|
| Long-horizon detector features: usage deviation from a commissioning-anchored, peer-adjusted baseline; its 28-day drift; a worked-day CUSUM (slack 0.05); 28-day fuel-rate drift | low-and-slow attacks hid inside daily noise | TCN PR-AUC 0.72 → 0.81; adaptive attackers now separable (CUSUM mean 4.9 vs honest p95 2.3) |
| Primary detector = TCN + XGBoost ensemble (logistic stacking on val_calib) | XGBoost best in-distribution, TCN best out-of-distribution | best PR-AUC in every development scenario (0.80–0.85) |
| Risk R = 1 − T(1 − s), no additive exposure term | additive exposure F used up the hold budget on legitimate busy claims | lowest mean total cost (31.4k vs 33.3k with F; detector-only 34.7k) |
| Random audits off | — | added cost, no fraud reduction |

Explored and **not** adopted (reported as ablations): additive exposure term F, expected-loss
weighting (λ = 0.7), random audits, the v1 rolling-median exposure.

## Fixed design (ATFA v2)
Detector `tcn_xgb`; ATFA adaptive trust (unchanged); R = 1 − T(1 − s); hard rules override;
low-trust gate; thresholds calibrated on val_policy to minimise fraudulent value settled subject to
legitimate holds ≤ 5 % and rejects ≤ 1 %. All other parameters as in `configs/default.yaml`.

## Primary hypotheses
In-distribution scenario, each compromise level (5/10/20/30 %), 20 paired worlds:
- **H1** ATFA has lower total cost than B3 (detector only, same detector).
- **H2** ATFA has lower total cost than B2 (fixed amount threshold).
- **H3** ATFA settles less fraudulent value than the same design with Beta-reputation trust.

Test: two-sided paired Wilcoxon signed-rank; Holm correction across the 3 primary comparisons
(per metric and level); α = 0.05. All other comparisons (other baselines, trust models,
detectors, ablations, OOD scenarios) are **secondary** and reported with Holm correction across all comparators.

## Secondary analyses
OOD scenarios (held-out families ×5, intensity ×0.4 / ×2.0, unseen assets; 5 fresh seeds each);
detection metrics; trust metrics; ablations; threshold sensitivity (seed 20).

## Reporting commitments
All 120 worlds are reported. No seed, scenario, level or metric is dropped. v1 results remain
in the paper's supplementary material as the development history.
