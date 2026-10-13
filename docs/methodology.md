# ATFA — Experimental Methodology

This document specifies the experimental protocol as implemented in this repository. Every
parameter named here is set in `configs/default.yaml`; section numbers are referenced from the code.

## 1. Research questions

- **RQ1 (Detection).** How accurately do temporal deep models (TCN, LSTM Autoencoder, hybrid)
  identify manipulated telemetry, compared with classical baselines, on synthetic and public data?
- **RQ2 (Adaptive trust).** Does ATFA's adaptive trust identify compromised devices faster and
  more reliably than static, EWMA and Beta-reputation trust, without penalising honest devices?
- **RQ3 (Financial protection).** How much fraudulent value is settled under ATFA versus
  baseline authorisation policies, and at what cost to legitimate claims?
- **RQ4 (Generalisation).** How do results change for unseen attack families, attack
  intensities and devices?
- **RQ5 (Contribution).** Which components (detector, trust, exposure, gate, feedback,
  hard rules) account for the gains (ablation)?
- **RQ6 (Ledger cost).** What throughput, inclusion and finality latency does anchoring ATFA
  decisions on PureChain PoA² incur? *(Measured on the real network; not part of the simulation.)*

## 2. ATFA-AssetFinance dataset

### 2.1 Application and threat model
Usage-based industrial equipment leasing: each asset reports daily usage; each report with
positive hours is a payment claim `claimed = reported_hours × contract_rate`. The adversary
controls a compromised device (or its reporting path) and benefits from **over-claimed** usage;
the payer is protected. Under-reporting by the lessee is out of scope.

### 2.2 Usage model (honest behaviour)
- 100 assets, 10 sites, 730 days (one report per asset per day); 4 asset types with type-specific
  rate, fuel consumption, RPM range, vibration and thermal parameters.
- **Site level:** a work calendar (weekday/Saturday/Sunday probabilities, shared holidays), a
  Markov chain over project phases (active / reduced / shutdown) and a seasonal ambient
  temperature with AR(1) weather noise.
- **Asset level:** mean hours and variability, maintenance stops (Poisson, 1–4 days), absences,
  legitimate overtime, and an AR(1) engine-load factor *L*.
- **Correlated channels** derived from true hours *h* and load *L*: fuel ∝ h·(0.35 + 0.65L);
  RPM = idle + (rated − idle)·L; engine temperature = base + 0.15·(ambient − 15) + 6L;
  vibration ∝ (0.6 + 0.8L)·wear; idle time; and an independent engine-hour meter.

Because channels are physically coupled, manipulation that is inconsistent across channels is
detectable, and this is what makes detector behaviour explainable.

### 2.3 Benign anomalies (false-positive drivers)
Hour-meter noise, per-channel transmission dropouts (1 %), stuck sensors (2–7 days), delayed and
out-of-order delivery (3 %, 6–60 h), clock drift with monthly resynchronisation, legitimate overtime,
maintenance stops, and project-phase changes.

### 2.4 Attack families and attacker knowledge
Attacks start only after a 120-day commissioning period. Compromised assets (5/10/20/30 %) are
assigned families round-robin and a knowledge level (naive 35 %, consistent 40 %, adaptive 25 %).

| Family | Mechanism |
|---|---|
| Inflation | episodes of hours × (1+α), α ∈ [0.15, 0.50]; phantom usage on idle days |
| On-off | alternating honest periods and bursts with α ∈ [0.40, 0.80] (trust exploitation) |
| Gradual compromise | α grows linearly from onset (0.2–1 %/day) up to 0.6 |
| Replay | a genuine past high-usage report (7–60 days old) is resubmitted |
| Forged identity | a cloned identity submits synthetic telemetry with inflated hours |

| Knowledge | Behaviour |
|---|---|
| Naive | changes the hours field only; replays verbatim (stale sequence number); forges with an invalid signature |
| Consistent | scales all usage-proportional channels (fuel, meter, idle) consistently; re-sequences replays; holds a stolen key but forges another type's profile |
| Adaptive | keeps inflation inside the noise band (α ≤ 0.10, slow drift); corrects replayed weather; forges the correct type profile |

### 2.5 Labels and leakage boundary
`anomaly_label` = the report was manipulated. `fraud_label` = reported − true hours > 0.5 h.
`overclaim_amount` = (reported − true) × rate for fraud records. Reference hours, labels,
attack family, knowledge and benign-event tags are **evaluator-only**. The pipeline sees only
the observable view (`atfa/features.py: OBSERVABLE`). A test (`tests/test_core.py`)
scrambles every evaluator-only column and asserts that all features and hard-rule outputs
are unchanged.

## 3. Detection

### 3.1 Features (19, platform-observable)
Daily features (15): hours; worked flag; hours − meter; fuel per hour (relative to rated);
normalised fuel, RPM, vibration; engine temperature rise over ambient; idle fraction; ambient
deviation from the same-site median; hours deviation from the same-site median; log delivery
delay; missing-channel count; day of week (sin/cos).

Long-horizon features (4, v2). **Expected usage** b_{i,t} = r_i · m_{s,t}, where m_{s,t} is the
same-site median of working peers' reported hours and r_i is the asset's median ratio to that
median over its attack-free commissioning period. Anchoring to commissioning (not to recent
claims) stops gradual inflation from moving its own reference. Features: usage deviation
d_t = (h_t − b_t)/max(b_t, 1); its 28-worked-day mean; a worked-day CUSUM
S_t = max(0, S_{t−1} + d_t − k) with k = 0.05 (half the smallest over-claim of interest, ~10 %);
and the 28-day drift of fuel per hour relative to commissioning. Absences are excluded from
the drift statistics. Standardised with training-split statistics.

### 3.2 Windows and splits
Causal windows of the last *W* reports of the same asset (left-padded at sequence start); the
label is that of the last report. *W* ∈ {20, 40, 60} is selected on validation PR-AUC in
dedicated selection worlds (seeds 100+, `scripts/select_window.py`). Selected: W = 40 (TCN
val PR-AUC 0.746 vs 0.733 for W = 20 and 0.719 for W = 60; the LSTM was insensitive to W,
0.690–0.697), used for all sequence models (`results/window_selection.csv`).
Chronological splits (days): train [0, 438), val_calib [438, 511), val_policy [511, 584),
test [584, 730). val_calib is used for early stopping, Platt calibration and hybrid stacking;
val_policy for the detection threshold (max F1) and all financial thresholds.

### 3.3 Models
| Model | Type | Role |
|---|---|---|
| Rules (window robust z + consistency checks) | none | domain baseline |
| Isolation Forest (window summaries) | unsupervised | classical unsupervised baseline |
| XGBoost (window summaries) | supervised | strong non-deep baseline |
| LSTM classifier | supervised | recurrent baseline |
| **TCN** (4 residual causal blocks, dilations 1-2-4-8, 32 channels, receptive field 61) | supervised | proposed primary |
| **LSTM Autoencoder** (trained on commissioning windows only; score = last-step reconstruction error) | label-free training | unseen-attack detector |
| **Hybrid** (logistic stacking of TCN logit and log AE error) | stacked | TCN + label-free combination |
| **TCN + XGBoost ensemble** (logistic stacking of both logits) | stacked | **primary detector (v2)**: temporal generalisation + in-distribution strength |

All scores are mapped to probabilities by Platt scaling on val_calib. Unsupervised models are
trained without labels, but their score-to-probability mapping and thresholds use the labelled
validation split (stated explicitly in the paper).

### 3.4 Metrics
Precision, recall, F1 at the val-selected threshold; PR-AUC; ROC-AUC; FPR; recall per attack
family and knowledge level; FPR per benign-event type; episode detection rate and latency (days
from episode onset to first alarm); inference time per window; parameter count.

## 4. Adaptive trust

Every model consumes the same evidence: the calibrated anomaly score *s* of each report.

| Model | Update |
|---|---|
| None | T = 1 |
| Static | T = T₀ = 0.89 |
| EWMA | T ← 0.95·T + 0.05·(1 − s) |
| Beta reputation (Jøsang & Ismail, 2002) | α ← α₀ + γ(α − α₀) + (1 − s); β ← β₀ + γ(β − β₀) + s; T = α/(α+β) |
| **ATFA** | Beta with forgetting, plus: negative evidence × κ = 2 (asymmetry); × claim size relative to expected usage, clipped to [0.5, 3] (exposure weighting); +5 to β on a hard violation; ±5 from the outcome of verified holds (feedback) |

All share the prior (α₀, β₀) = (8, 1) and γ = 0.98. States: Trusted T ≥ 0.80; Caution 0.60–0.80;
Low T < 0.60. **Trust is read before the current report updates it.**

Trust metrics: honest-device low-trust rate; fraction of attacked assets reaching Low; median
days from the first fraudulent claim to Low; mean trust when submitting fraud vs legitimate claims.

## 5. Financial-risk-aware authorisation

**Risk (v2).** R = 1 − T(1 − s): a claim is risky when the device is not trusted or the report is
anomalous. Note the use of *T* (not 1 − T): high trust lowers risk.

Financial-risk awareness enters through (i) the money-denominated calibration objective
(minimise fraudulent *value* settled under legitimate-hold and reject budgets), (ii) contract-cap
hard rules, and (iii) exposure-weighted trust evidence (negative evidence scaled by the claim's size
relative to expected usage b_{i,t}).

**Variants evaluated as ablations.** *Additive exposure (v1):* R = 1 − T(1 − s)(1 − F), with
F = f_max · clip((h − h_exp)/(τ·h_exp), 0, 1), τ = 0.5, f_max = 0.5 (v1 used h_exp = rolling median of
the last 28 paid claims; v2 uses b_{i,t}). *Expected-loss weighting:* R = q·(λ + (1 − λ)·x) with
q = 1 − T(1 − s), x the normalised excess and λ = 0.7. *Random audits:* 2 % of approved claims
verified after settlement (cost counted, no recovery), outcomes fed to trust. On selection worlds
none of these improved on the v2 rule (docs/confirmatory_plan.md).

**Decision.** Hard violation (invalid signature, duplicate sequence number, timestamp outside
±72 h, hours above contract cap, inactive contract) → Reject, regardless of trust. Otherwise
R < θ_a → Approve; θ_a ≤ R < θ_r → Hold; R ≥ θ_r → Reject. If T < 0.60, at least Hold.

**Design guarantees.** (i) A low-trust device can never be auto-approved. (ii) A trusted device
whose report carries no anomaly evidence has R = 1 − T ≤ 0.2 and cannot be rejected on claim size
alone (for the additive-exposure variant this is enforced by F ≤ f_max and θ_r > 1 − 0.8·(1 − f_max)).
(iii) No trust level overrides a hard violation.

**Verification model.** A held claim is verified independently with detection probability 0.95
after 3 days; a detected over-claim is settled at the verified amount, and the outcome feeds back
into ATFA trust. Undetected fraud is paid in full.

**Threshold calibration.** On val_policy only: minimise fraudulent value settled subject to
legitimate-hold rate ≤ 5 % and legitimate-reject rate ≤ 1 % (grid over θ_a, θ_r); tie-break on
total cost; if no grid point is feasible, minimise total cost (reported as infeasible). Thresholds
are frozen before the test split. The provisional thresholds (0.30 / 0.60) are reported
alongside, as a fixed-threshold comparison, and a threshold-sensitivity sweep is evaluated on test.

**Financial metrics.** Fraudulent value settled (FVS, absolute and % of attempted); fraud claims
blocked; legitimate hold and reject rates; legitimate value rejected; holds per 1,000 claims;
total cost = FVS + 25 × holds + 0.2 × legitimate value rejected (cost parameters are assumptions
and are varied in the sensitivity analysis).

## 6. Baselines, comparisons and ablations

| Group | Systems |
|---|---|
| Baselines | B0 approve every signed claim (smart contract only); B1 hard rules only; B2 fixed amount threshold for manual review (label-free, 95th percentile); B3 detector score only; B4 trust score only; Oracle (perfect labels, lower bound) |
| Trust comparison | ATFA with trust ∈ {none, static, EWMA, Beta, ATFA} |
| Detector comparison | ATFA with each detector |
| Ablations (v2) | −detector (s = 0); −exposure-weighted trust; −verification feedback; −asymmetric evidence; −low-trust gate; −hard rules; weighted-sum risk; +additive exposure F; expected-loss risk (λ = 0.7); +random audits; v1 authorisation (additive F with rolling-median exposure) |

## 7. Generalisation scenarios

| Scenario | Construction |
|---|---|
| In-distribution (id) | all families throughout; 5/10/20/30 % compromised; 10 seeds |
| Held-out family (×5) | the assets of one family attack only during the test period, so the family is absent from train/val |
| Intensity shift | attack intensity × 0.4 (stealthier) or × 2.0 (stronger) during the test period only |
| Unseen assets | 30 % of assets never seen in training/validation; evaluation on those assets only |

The gap between id and the out-of-distribution scenarios quantifies how much of the performance
depends on the generator's attack distribution.

## 8. Statistics and reproducibility
Mean ± standard deviation over seeds (v2: 20 for id, 5 per OOD scenario). Paired two-sided Wilcoxon
signed-rank tests compare ATFA with each comparator on identical worlds; the three pre-registered
primary comparisons are Holm-corrected among themselves, all others across all comparators. Effect
sizes: mean paired difference with a percentile-bootstrap 95 % CI (10,000 resamples) and the
matched-pairs rank-biserial correlation. Sensitivity analyses: cost parameters (review cost 5–100,
rejection penalty 0.05–1.0; exact recomputation, since decisions do not depend on cost weights) and
one-at-a-time variation of verification accuracy and delay, hold/reject budgets and all trust
parameters (`scripts/param_sensitivity.py`). Robustness: harsher benign conditions and a 5× larger
fleet on fresh seeds (`configs/robustness_v2.yaml`). All randomness is seeded; the resolved configuration is saved with every run.

## 9. Public benchmarks
**TON_IoT IoT telemetry** (UNSW; complete processed device streams, Kaggle mirror
`medworldmed/ton-iot-datasets`; record counts match the published dataset, e.g. 587,076 fridge
readings). Seven device streams (fridge, thermostat, GPS tracker, garage door, motion light,
Modbus, weather); `date`, `time` and attack `type` are never used as features.
In every stream all attacks occur in the final ~30 % of the timeline, so a plain chronological
split leaves no attacks for training. Two protocols are therefore reported:
- **Blocked temporal split (all models).** Each stream is cut into contiguous 1-hour blocks; blocks
  containing attacks and attack-free blocks are assigned separately to train / val_calib /
  val_policy / test (60/10/10/20), and the first W rows of every block are embargoed so no window
  spans two splits. Training windows are capped at 60,000 (random sample within train blocks).
- **Chronological novelty protocol (label-free models).** Isolation Forest and LSTM-AE are trained
  on the attack-free first 60 %; calibration and threshold on [60 %, 80 %); test on the final 20 %.

**Edge-IIoTset** (`ML-EdgeIIoT-dataset.csv`): leakage fields dropped and duplicates removed before a
stratified 60/20/20 split; XGBoost (binary, multiclass) and Isolation Forest only (non-temporal
records). Public-dataset results address RQ1 only; they carry no financial labels.

## 10. Ledger evaluation (PureChain PoA²)
**Network.** PureChain PoA² (Geth-based, chain ID 900520900520, zero gas price, on-demand block
sealing), RPC `https://purechainnode.com`.
**Contract.** `contracts/ATFAEvidenceAnchor.sol` (Solidity 0.8.24, optimiser 200 runs) stores, per
decision digest, the anchoring time and decision; `anchor` (single) and `anchorBatch` (k digests per
transaction); `isSettleable(digest)` returns true only for an anchored APPROVE, and is the
pre-settlement check. Governance: an admin wallet manages the authoriser list; the ATFA engine key
(generated locally, stored only in `.env`) is the initial authoriser. Deployed at
`0x6592cBD3CE1303EAfBfDE9f65301DD428844Ed5E` (block 1,814,387); an on-chain functional check
confirmed that approved records verify and are settleable, while held and tampered records are not.
**Evidence record.** device ID, day, sequence number, SHA-256 of the device report, claimed amount,
T, s, F, R, decision, policy version; its SHA-256 digest is anchored.
**Measurements** (`scripts/bench_ledger.py`): E1 confirmation latency of single anchors (sequential);
E2 batching (k = 1, 10, 50, 100 records per transaction): latency and gas per record; E3 sustained
offered load (5–50 tx/s, 20 s each): achieved throughput, p50/p95/p99 confirmation latency, failures;
E4 latency of the `isSettleable` read. Because PoA² seals blocks on demand, a transaction is final
once included; finality latency equals inclusion latency. Gas is reported in EVM units (the fee is
zero on this network).

## 11. Security analysis

**Assumptions.** (A1) Devices are attack-free during the 120-day commissioning period (the reference
for expected usage and for label-free models). (A2) PureChain PoA² authority nodes are honest, so
anchored records are immutable. (A3) Verification of held claims is independent of the device.
(A4) Fewer than half of the working assets at a site are compromised at once (median-based peer
reference). **Adversary.** Controls a device's firmware or reporting path: it can alter telemetry,
replay past reports, forge an identity (with or without a stolen key) and adapt its behaviour to
stay inside normal noise; it cannot alter anchored records or the contract.

| Threat | ATFA mechanism | Evidence |
|---|---|---|
| Usage inflation (naive / consistent / adaptive) | detector with cross-channel and long-horizon features; adaptive trust | recall 0.94 / 0.78 / 0.29; fraud settled 7.3 % (inflation) |
| Gradual drift | commissioning-anchored baseline, worked-day CUSUM | fraud settled 5.8 % vs 8.1 % detector-only |
| Trust farming (on-off) | asymmetric evidence, verification feedback, forgetting | fraud settled 7.3 % |
| Stale replay | duplicate sequence number and timestamp-window hard rules | all naive replays rejected (unit test) |
| Refreshed replay | peer ambient/usage deviation in the detector; trust | fraud settled 11.2 % (hardest family) |
| Forged identity, no key | signature hard rule | all rejected (unit test) |
| Forged identity, stolen key | asset-profile consistency features | fraud settled 1.9 % |
| Altering a decision after the fact | SHA-256 evidence digest anchored on PureChain; `isSettleable` | tampered record not settleable (on-chain check) |
| Settling a held or rejected claim | only APPROVE digests are settleable | held record not settleable (on-chain check) |
| Unauthorised anchoring | `onlyAuthoriser`; admin governs authorisers | contract access control |
| ATFA engine key compromise | admin revokes the key (`setAuthoriser(false)`); new key authorised | governance path; residual risk until revocation |
| Ledger flooding / overload | per-sender limit; multiple authorisers; batching | no losses at 100 tx/s offered; 60 tx/s with 4 senders |

**Out of scope / residual risks.** Collusion of a majority of devices at one site (breaks A4);
attacks during commissioning (breaks A1); under-reporting by the lessee; the blockchain oracle
problem: the ledger guarantees the integrity of *decisions*, not the truth of the telemetry, which is
what the detector and trust layers address.

## 12. Computational complexity
Per report: feature update O(1) amortised (rolling statistics); TCN inference O(L·K·C²·W) for L = 4
blocks, kernel K = 3, C = 32 channels, window W = 40; XGBoost O(trees × depth); trust, risk and
decision O(1). Per-asset state O(W·F): 3.3 KB. Measured on one CPU thread
(`results/overhead/`): 4.1 ms per claim end to end for the TCN + XGBoost ensemble (0.10 ms per claim
when a day's claims are batched); < 1 µs per claim for trust + risk + decision even for 10,000
assets; 0.013 ms per evidence digest; models 0.10 MB (TCN) + 0.69 MB (XGBoost). Ledger: one
32-byte digest per decision, 54.7k gas single or 24.1k per record batched.

## 13. Development history (v1 → v2)
The protocol was first run with the v1 design (seeds 0–9; `results/full/`). Weaknesses found there
were addressed on selection worlds only (seeds 100–105) and the v2 design was then evaluated once on
fresh seeds 20–39 under a plan fixed in advance (`docs/confirmatory_plan.md`). Primary hypotheses
(ATFA vs detector-only, vs fixed amount threshold, vs Beta-reputation trust) are tested with Holm
correction across those three comparisons; everything else is secondary.

## 14. Limitations
Synthetic financial data (mitigated by the usage model, documented assumptions, OOD scenarios and
public benchmarks); a single daily report per asset; an idealised verification process; cost
parameters are assumptions; under-reporting and collusion among many devices at one site are out of scope.
