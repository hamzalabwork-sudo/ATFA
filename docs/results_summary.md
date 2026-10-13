# ATFA — Results Summary

Protocol: `docs/methodology.md`. Full tables (Markdown + LaTeX) and figures: `results/full/report/`,
`results/public/report/`, `results/purechain/report/`. All values are on test data with thresholds
frozen on validation data. Mean (std) over 10 seeds (in-distribution) or 5 seeds (each OOD scenario).
Paired Wilcoxon tests are Holm-corrected across ~20 comparators; with 10 seeds the smallest
attainable corrected p is ≈ 0.047, reached when ATFA wins in 10 of 10 worlds.

## 1. Financial protection (RQ3) — in-distribution

Fraudulent value settled (% of attempted over-claim):

| System | 5 % compromised | 10 % | 20 % | 30 % |
|---|---|---|---|---|
| B0 approve every signed claim | 100.0 | 100.0 | 100.0 | 100.0 |
| B1 hard rules only | 86.7 (15.0) | 86.7 (9.8) | 87.6 (6.0) | 85.2 (4.0) |
| B2 fixed amount threshold | 59.5 (19.1) | 51.0 (10.8) | 60.1 (14.6) | 64.5 (8.2) |
| B3 detector only | 26.9 (17.6) | 11.6 (14.2) | 18.6 (9.2) | 12.5 (5.8) |
| B4 trust only | 11.9 (9.7) | 10.6 (8.1) | 33.2 (13.3) | 42.0 (11.9) |
| **ATFA (validation-calibrated)** | **10.6 (6.9)** | **5.3 (4.2)** | **11.0 (4.7)** | **10.5 (6.9)** |
| ATFA (provisional 0.30 / 0.60) | 9.0 (6.9) | 3.1 (2.5) | 4.1 (2.0) | 2.5 (0.7) |

Total cost (thousands; fraud settled + review cost + rejection cost):

| System | 5 % | 10 % | 20 % | 30 % |
|---|---|---|---|---|
| B0 | 65.4 | 162.6 | 272.8 | 389.4 |
| B2 | 49.0 | 94.2 | 174.8 | 261.2 |
| B3 detector only | 27.0 | 31.0 | 68.4 | 67.1 |
| B4 trust only | 22.6 | 34.4 | 107.7 | 175.3 |
| **ATFA** | **18.8** | **21.7** | **51.0** | **64.5** |
| ATFA (provisional) | 26.8 | 33.3 | 61.6 | 77.4 |

- ATFA has the lowest mean total cost at every compromise level. It is significantly cheaper than
  B2 at all levels and than B4 at 10–30 % (10/10 worlds). It is cheaper than B3 in 5–8 of 10 paired
  worlds; the B3 difference is not significant after Holm correction.
- Calibrated ATFA respects the business budgets: legitimate claims held 3.8–5.6 %, rejected
  0.1–0.5 %. Calibration met both budgets in 92 % of in-distribution worlds and in 100 % of OOD worlds.
- The provisional thresholds settle less fraud (2.5–9 %) but hold 9.7–12.9 % of legitimate claims at
  20–30 % compromise, above the 5 % budget, and cost more. This is the trade-off shown in
  `fig_threshold_tradeoff`, and the reason thresholds must be calibrated rather than fixed.

## 2. Adaptive trust (RQ2)

| Trust model (inside ATFA) | FVS % (pooled) | Attacked assets reaching Low | Median days to Low | Mean T on fraud / legit |
|---|---|---|---|---|
| None | 15.8 | — | — | 1.00 / 1.00 |
| Static | 15.8 | 0 % | — | 0.89 / 0.89 |
| EWMA | 15.2 | 43 % | 22 | 0.74 / 0.97 |
| Beta reputation | 15.1 | 12 % | 21 | 0.78 / 0.96 |
| **ATFA** | **9.4** | **73 %** | **15** | **0.56 / 0.93** |

No trust model put an honest device into Low trust (honest low-trust rate 0.0 for all).
ATFA trust beats no trust on fraud settled in 10/10 worlds at 5 % and 10 % compromise.

## 3. Ablation (RQ5), pooled in-distribution

| Variant | FVS % | Total cost (k) | Reading |
|---|---|---|---|
| ATFA (full) | 9.4 | 39.0 | |
| − detector (s = 0) | 29.0 | 86.4 | the detector is the largest contributor |
| − verification feedback | 15.8 | 52.8 | the main trust mechanism (significant at 10–30 %) |
| − adaptive trust (none / static / EWMA / Beta) | 15.1–15.8 | 46.5–48.9 | adaptive trust matters |
| weighted-sum risk instead of noisy-OR | 11.2 | 41.4 | noisy-OR slightly better |
| − exposure term F | 9.4 | 39.0 | **no measurable effect** |
| − exposure-weighted trust | 9.4 | 39.3 | **no measurable effect** |
| − asymmetric evidence | 9.2 | 37.1 | **no measurable effect** |
| − low-trust gate | 8.9 | 36.2 | **no measurable effect** |
| − hard rules | 9.2 | 38.4 | **no measurable effect** (detector also catches naive protocol attacks) |

**Implication for the paper:** the gains come from the detector, adaptive trust with
verification feedback, and calibrated thresholds. The exposure term, exposure weighting,
asymmetry and gate do not improve results in this setting. Report them as design safeguards
(the gate and hard rules give guarantees in Section 5 of the methodology), not as performance
contributors, or simplify the model.

## 4. Detection (RQ1) and generalisation (RQ4)

In-distribution PR-AUC, mean over levels: XGBoost 0.75, LSTM 0.72, **TCN 0.71**, hybrid 0.72,
rules 0.55, LSTM-AE 0.47, Isolation Forest 0.21. In-distribution, XGBoost is marginally best and
the hybrid adds nothing over the TCN.

**Out of distribution the TCN generalises better** (recall on an attack family never seen in training):

| Held-out family | XGBoost | TCN | LSTM-AE |
|---|---|---|---|
| Forged identity | 0.36 | **0.78** | 0.66 |
| Replay | 0.26 | **0.61** | 0.52 |
| On-off | 0.53 | **0.71** | 0.55 |
| Inflation | 0.36 | **0.42** | 0.28 |
| Gradual | **0.35** | 0.30 | 0.09 |

Unseen devices: TCN PR-AUC 0.760 vs XGBoost 0.699. Stealthier attacks (intensity × 0.4) are
hardest for all models (PR-AUC 0.64–0.69); adaptive "low-and-slow" attackers remain the main open problem.
ATFA reduces fraud settled relative to detector-only in every OOD scenario (e.g. held-out replay
5.5 % vs 12.5 %; unseen assets 14.9 % vs 18.0 %).

**Choice of primary detector:** TCN, justified by generalisation to unseen attacks and devices
rather than by in-distribution accuracy, with XGBoost reported as a strong in-distribution baseline.

## 5. Public benchmarks

**TON_IoT telemetry (blocked split, ROC-AUC):** clear signal on 4 of 7 streams: garage door
(XGBoost 0.94, TCN 0.94), GPS tracker (XGBoost 0.93, TCN 0.74), thermostat (TCN 0.85, XGBoost 0.78)
and weather (TCN 0.83, XGBoost 0.72). The TCN beats the LSTM on every stream with signal. Fridge and
Modbus show no detectable signal (≈ 0.5) once timestamps are excluded; near-perfect TON_IoT telemetry
results in the literature typically rely on date/time features. Under the chronological novelty
protocol, label-free models are near chance on all streams.

**Edge-IIoTset** (152,196 records after dropping leakage fields and 5,604 duplicates): XGBoost F1 0.986,
PR-AUC 0.999 (false-positive rate 0.15 at the F1-optimal threshold, attack base rate ~84 %); 15-class
macro-F1 0.891; Isolation Forest fails (ROC-AUC 0.52).

## 6. PureChain PoA² (RQ6)

| Measurement | Result |
|---|---|
| Confirmation latency, single anchor | p50 1.98 s, p95 2.03 s (100/100 included) |
| Gas per record | 54.7k single; 26.9k (batch 10); 24.4k (50); 24.1k (100), with unchanged latency |
| Sustained load, one authoriser account | stable ≤ 10 tx/s (p50 1.8 s); saturates at ~16 tx/s |
| Per-sender limit (4 accounts) | 45 tx/s at 2.1 s p50 (50 offered); 60 tx/s at 100 offered |
| Batched load (100 records/tx, one account) | ~290 records/s |
| Pre-settlement check (`isSettleable`) | p50 55 ms, p95 91 ms |
| Failures | 0 send errors over ~9,000 transactions; 2 not observed within 120 s in the most overloaded run |

The ~16 tx/s ceiling is per sender account (blocks carried ~16 of one sender's transactions, far
below the gas limit). It scales with authoriser accounts and with batching. The simulated
fleet (100 assets, ~70 claims/day) needs < 0.001 tx/s, so the ledger is not a bottleneck.

## 7. Threats to validity
Synthetic financial data and assumed cost parameters; the modelled verification process; modest
significance after multiple-comparison correction with 10 seeds; TON_IoT from a community mirror
(record counts verified against the publication); PureChain measured from a single client host over
the public RPC endpoint.
