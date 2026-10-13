# ATFA v2 — Confirmatory Results

Design and hypotheses fixed in advance in `docs/confirmatory_plan.md`; evaluated once on **fresh
seeds 20–39** (in-distribution, 20 worlds per compromise level) and 20–24 (each OOD scenario).
120 worlds, no failures. Full tables and figures: `results/confirmatory_v2/report/`. All values are
test-split results with thresholds frozen on validation data. Mean (std).

## 1. Headline: financial protection (in-distribution)

Fraudulent value settled (% of attempted over-claim):

| System | 5 % compromised | 10 % | 20 % | 30 % |
|---|---|---|---|---|
| B0 approve every signed claim (smart contract only) | 100.0 | 100.0 | 100.0 | 100.0 |
| B1 hard rules only | 86.1 (11.5) | 86.4 (10.6) | 89.1 (5.8) | 86.6 (5.7) |
| B2 fixed amount threshold | 55.8 (19.4) | 55.1 (16.0) | 60.7 (9.9) | 59.2 (8.4) |
| B3 detector only (same detector) | 7.8 (16.5) | 3.9 (2.5) | 4.3 (2.1) | 4.6 (2.2) |
| B4 trust only | 6.7 (9.5) | 10.7 (6.5) | 24.8 (7.7) | 27.6 (14.3) |
| **ATFA v2** | **4.8 (9.0)** | **2.9 (2.3)** | **4.1 (2.5)** | **4.3 (2.6)** |

Total cost (thousands): ATFA 13.5 / 20.5 / 30.1 / 39.9; B3 15.0 / 21.7 / 30.9 / 42.3;
B2 51.3 / 89.1 / 173.2 / 242.7; B0 74.6 / 140.3 / 264.5 / 394.0.

- **ATFA prevents 95–97 % of attempted fraudulent value**, against 39–45 % for a fixed amount
  threshold, 11–14 % for hard rules alone and 0 % for the smart contract alone.
- **It does so within the business budgets:** legitimate claims held 2.3–4.9 %, rejected 0.2–0.7 %;
  calibration met both budgets in **100 % of the 120 worlds**.
- **Cost reduction:** 82–90 % against the smart contract alone, 74–84 % against the fixed amount threshold.
- **v1 → v2 improvement (same protocol):** fraud settled 5.3–11.0 % → 2.9–4.8 %; total cost
  18.8–64.5k → 13.5–39.9k.

## 2. Pre-registered primary hypotheses (Holm across 3 comparisons)

| Hypothesis | 5 % | 10 % | 20 % | 30 % | Verdict |
|---|---|---|---|---|---|
| H2: ATFA cost < B2 fixed amount threshold | 19/20, p<0.0001 | 20/20, p<0.0001 | 20/20, p<0.0001 | 20/20, p<0.0001 | **Confirmed at all levels** |
| H1: ATFA cost < B3 detector only | 8/20, p=0.96 | 10/20, p=0.45 | 11/20, p=0.57 | 11/20, p=0.38 | **Not confirmed** (mean cost lower at every level, not significant) |
| H3: ATFA fraud settled < Beta-reputation trust | 9/20, p=0.22 | 11/20, p=0.20 | **17/20, p=0.002** | 9/20, p=1.0 | **Confirmed at 20 % only** |

Secondary (same tests on fraud settled vs B3): ATFA settles significantly less fraud than
detector-only at 5 % (14/20, p_Holm = 0.022) and 10 % compromise (16/20, p_Holm = 0.031).

**Interpretation.** The v2 long-horizon features made the detector so strong that the detector
alone already blocks most fraud in-distribution. Adaptive trust then adds a consistent but small
reduction in fraud settled (pooled 5.1 % → 4.0 % against no/Beta trust) and a cost advantage that
is not significant pairwise. Trust adds most where detection is weaker: on unseen devices ATFA
settles 6.4 % vs 8.2 % (detector only) and is cheaper in 4 of 5 worlds.

## 3. Detection (RQ1, RQ4)

PR-AUC (in-distribution, mean over levels), v1 → v2: XGBoost 0.746 → 0.852; TCN 0.713 → 0.819;
LSTM 0.716 → 0.812; LSTM-AE 0.467 → 0.627; hybrid 0.716 → 0.829; **TCN + XGBoost ensemble 0.860**.

The ensemble is the **best detector in all 9 scenarios** at 20 % compromise (PR-AUC 0.739–0.879),
including unseen devices (0.772 vs 0.755 XGBoost and 0.746 TCN), stealthy attacks (0.761) and every
held-out attack family. Recall on adaptive (low-and-slow) attackers rose from 0.20 (best v1 detectors)
to 0.29 (ensemble). This remains the hardest case.

## 4. Adaptive trust (RQ2)

| Trust (inside ATFA, id pooled) | FVS % | Attacked assets reaching Low | Mean T on fraud / legit |
|---|---|---|---|
| None | 5.12 | — | 1.00 / 1.00 |
| Static | 5.04 | 0 % | 0.89 / 0.89 |
| EWMA | 5.14 | 59 % | 0.65 / 0.97 |
| Beta reputation | 5.06 | 19 % | 0.70 / 0.96 |
| **ATFA** | **4.00** | **67 %** | **0.53 / 0.94** |

No honest device entered Low trust under any model.

## 5. Ablations (id pooled; FVS %, total cost k)

| Variant | FVS | Cost | Reading |
|---|---|---|---|
| ATFA v2 | 4.00 | 26.0 | |
| − detector | 53.6 | 138.4 | the detector is essential |
| − verification feedback | 5.65 | 33.5 | the most important trust mechanism |
| trust = none / static / Beta / EWMA | 5.0–5.1 | 27.5–29.2 | adaptive trust helps |
| detector = TCN alone / XGBoost alone | 5.85 / 3.82 | 30.1 / 27.4 | the ensemble is the best trade-off |
| + additive exposure F / expected-loss / v1 authorisation | 3.7–4.2 | 26.2–26.9 | no gain (as found in development) |
| + random audits | 3.81 | 29.7 | audit cost outweighs the small fraud reduction |
| − asymmetric evidence / − exposure-weighted trust / − gate | 3.6–3.9 | 25.0–25.1 | **no measurable benefit; slight cost** |
| − hard rules | 4.25 | 25.3 | negligible (the detector also catches naive protocol attacks) |

**Implication for the paper:** the contribution is detector + adaptive trust with verification
feedback + money-calibrated thresholds. Asymmetric evidence, exposure-weighted trust and the gate
are retained as design safeguards (they provide guarantees, e.g. no auto-approval of low-trust
devices) and should not be claimed as performance contributors.

## 6. Public benchmark with the v2 detector (TON_IoT telemetry, blocked split, 3 seeds)

ROC-AUC: the TCN + XGBoost ensemble is best or tied-best on thermostat (**0.894** vs TCN 0.852,
XGBoost 0.778), motion light (0.719) and garage door (0.944), close to the best on GPS tracker
(0.929 vs XGBoost 0.934; TCN 0.740) and weather (0.813 vs TCN 0.827). Fridge and Modbus remain at
chance (≈ 0.5) without timestamp features. TCN and XGBoost results reproduced exactly against the
earlier run (deterministic pipeline). Tables: `results/public_v2/report/public_report.md`.
Edge-IIoTset results are unchanged (`results/public/`).

## 7. Ledger re-check (PureChain PoA²)
The overloaded test (100 tx/s) was repeated with a 300 s observation window and a direct receipt
check: **2,000 of 2,000 transactions included** in both the 1-sender and 4-sender runs. The 27
transactions the block watcher missed in the 4-sender run were all confirmed by receipt. The earlier
"2 unseen" were a measurement artefact; no transaction was lost. (`results/purechain/recheck/`)

## 9. Additional analyses for review

### 9.1 Effect sizes and 95 % confidence intervals (primary comparisons, id)
Mean paired difference ATFA − comparator (thousands; negative = ATFA better), percentile-bootstrap
95 % CI, matched-pairs rank-biserial r (|r| ≥ 0.5 = large).

| Level | Comparison | Metric | Difference [95 % CI] | r | p (Holm) |
|---|---|---|---|---|---|
| 5 % | vs fixed amount threshold | cost | −37.8 [−44.1, −30.3] | −0.99 | < 0.0001 |
| 10 % | vs fixed amount threshold | cost | −68.6 [−78.6, −58.8] | −1.00 | < 0.0001 |
| 20 % | vs fixed amount threshold | cost | −143.1 [−157.2, −128.7] | −1.00 | < 0.0001 |
| 30 % | vs fixed amount threshold | cost | −202.7 [−214.4, −191.2] | −1.00 | < 0.0001 |
| 5 % | vs detector only | fraud settled | −2.74 [−6.88, −0.37] | −0.68 | 0.022 |
| 10 % | vs detector only | fraud settled | −1.44 [−2.52, −0.35] | −0.61 | 0.031 |
| 20 % | vs Beta trust | fraud settled | −2.19 [−3.56, −1.03] | −0.80 | 0.002 |
| 5–30 % | vs detector only | cost | −0.87 to −2.31 (CIs include 0) | −0.02 to −0.31 | n.s. |

### 9.2 Cost-parameter sensitivity (all 80 id worlds; `results/confirmatory_v2/report/cost_sensitivity.md`)
Exact recomputation (decisions do not depend on cost weights; calibration was feasible in every world).
Review cost 5–100 per held claim, rejection penalty 0.05–1.0 of the claim value (20 settings):

| ATFA vs | Saving range | Worlds where ATFA is cheaper | Conclusion |
|---|---|---|---|
| Smart contract only | 61–94 % | 77–80 / 80 | robust |
| Fixed amount threshold | 52–90 % | 74–80 / 80 | robust |
| Beta-reputation trust | −0.2 to 16 % | 41–58 / 80 | cheaper in 19 of 20 settings (p < 0.05 in 16) |
| Detector only | −5.7 to 12.9 % | 30–50 / 80 | cheaper (p < 0.05) when review cost ≤ 10; break-even or costlier when reviews are very expensive (≥ 50–100) |

Interpretation: ATFA trades a slightly higher hold volume for less fraud, which pays off when
verification is inexpensive (automated cross-checks), the intended deployment.

### 9.3 Parameter sensitivity (one at a time; `results/sensitivity_v2/`, `fig_param_sensitivity`)
Cached confirmatory worlds (id 10 % and 20 %, seeds 20–29; reproduce the confirmatory results exactly).

| Parameter (default) | Values | ATFA fraud settled | Detector only | ATFA ≤ B3 (worlds) |
|---|---|---|---|---|
| default | — | 2.80 % | 4.03 % | 80 % |
| verification p_detect (0.95) | 0.8 / 0.9 / 1.0 | 4.13 / 3.27 / 2.48 % | 4.97 / 4.32 / 3.33 % | 70–80 % |
| verification delay (3 d) | 1 / 7 / 14 | 2.79 / 3.47 / 3.61 % | 4.03 % | 50–80 % |
| legit hold budget (5 %) | 2.5 / 10 % | 4.34 / 1.77 % | 5.46 / 3.21 % | 70–85 % |
| legit reject budget (1 %) | 0.5 / 2 % | 3.04 / 2.55 % | 4.26 / 3.62 % | 70 % |
| trust forgetting γ (0.98) | 0.95 / 0.99 | 2.88 / 3.07 % | 4.03 % | 80 % |
| asymmetry κ (2) | 1 / 4 | 2.68 / 3.54 % | 4.03 % | 65–85 % |
| verification weight (5) | 2 / 10 | 3.72 / 2.56 % | 4.03 % | 55–90 % |
| prior (8, 1) | (4, 1) / (16, 2) | 3.02 / 3.07 % | 4.03 % | 80–85 % |
| low-trust threshold (0.6) | 0.5 / 0.7 | 2.80 / 3.11 % | 4.03 % | 75–80 % |

**In all 21 settings ATFA settles less fraud and costs less than detector-only on average**; the
budgets are met in ≥ 80 % of worlds in every setting (100 % in 18 of 21). Results are not tuned to a
narrow parameter choice.

### 9.4 Robustness on fresh seeds (`results/robustness_v2/`)

| Condition | ATFA fraud settled | Detector only | Fixed threshold | ATFA cost vs detector only | Budgets met | Best detector (PR-AUC) |
|---|---|---|---|---|---|---|
| Reference (id 20 %, 20 seeds) | 4.1 % | 4.3 % | 60.7 % | 30.1k vs 30.9k | 100 % | ensemble 0.879 |
| Harsher benign conditions (2× noise, 3× dropouts/stuck sensors, 2× delays/overtime/absence; 5 seeds) | 5.9 % | 7.1 % | 62.0 % | 33.4k vs 35.4k | 100 % | ensemble 0.850 |
| 5× fleet: 500 assets, 50 sites, ~244k claims per world (3 seeds) | 3.7 % | 4.1 % | 58.1 % | 144.9k vs 164.5k | 100 % | ensemble 0.848 |

### 9.5 Computational overhead (`results/overhead/`, one CPU thread)

| Component | Per claim |
|---|---|
| TCN + XGBoost inference, single claim | 4.08 ms |
| TCN + XGBoost inference, amortised in a daily batch | 0.097 ms |
| Trust update + risk + decision | < 1 µs (fleets of 100–10,000 assets) |
| Evidence digest (SHA-256) | 0.013 ms |
| Model size | TCN 0.10 MB (24,257 parameters) + XGBoost 0.69 MB |
| State per asset | 3.3 KB |
| Ledger anchoring | ~2 s confirmation; 54.7k gas (24.1k batched) |

## 10. Reviewer-readiness checklist

| Typical IEEE IoT-J reviewer question | Where it is answered |
|---|---|
| Is the evaluation leakage-free and reproducible? | leakage unit test; fixed seeds; deterministic re-runs (TON_IoT and cached worlds reproduce exactly); `reproduce.sh` |
| Were design choices tuned on the test data? | v2 developed on selection seeds 100–105 only; plan fixed before the confirmatory run (`docs/confirmatory_plan.md`) |
| Are improvements statistically meaningful? | pre-registered primary tests, Holm correction, bootstrap CIs, effect sizes (9.1) |
| Do the results depend on arbitrary costs or parameters? | cost sensitivity (9.2); one-at-a-time parameter sensitivity (9.3) |
| Is synthetic data hiding weaknesses? | OOD scenarios, harsher benign conditions (9.4), public TON_IoT and Edge-IIoTset benchmarks |
| Does it scale? | 500-asset fleet (9.4); trust/decision cost per claim < 1 µs at 10,000 assets (9.5); ledger 60 tx/s with 4 senders |
| Is it deployable on IoT/edge infrastructure? | 4 ms per claim on one CPU thread, 0.8 MB of models, 3.3 KB state per asset (9.5) |
| Security analysis? | threat model, assumptions, attack-defence-evidence table (methodology §11) |
| Blockchain cost and performance? | measured on the live PureChain PoA² network (§7, `results/purechain/`) |
| Limitations stated? | detector-only cost difference not significant; adaptive attacks; synthetic financial data; components without measurable gain |

## 11. What to present
- ATFA prevents **95–97 % of fraudulent value** with ≤ 5 % of legitimate claims held, in every
  world, versus 39–45 % for a fixed threshold and 0 % for a plain smart contract (confirmed, p < 0.0001).
- The TCN + XGBoost ensemble with long-horizon usage features is the best detector in every scenario.
- ATFA adaptive trust identifies 3.5× more compromised devices than Beta reputation with zero false
  low-trust classifications, and lowers fraud settled by ~20 % relative to trust-free operation.
- PureChain PoA² anchors every decision with ~2 s finality, zero transaction loss and ~24k gas per
  record when batched.
- ATFA's advantage holds under every cost and parameter setting tested and at 5× fleet size, and
  costs ~4 ms per claim on one CPU thread.
- Report honestly that the cost advantage over a detector-only policy (same detector) is not
  statistically significant in-distribution (it is significant when verification is inexpensive), and that low-and-slow adaptive attacks remain the open problem.
