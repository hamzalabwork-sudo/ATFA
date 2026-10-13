# ATFA results (robustness_v2)

Mean ± std over seeds. Values are measured on the test split with thresholds frozen on validation data.

### Simulated worlds

| scenario     |   level |   worlds |   claims |   anomaly_rate |   fraud_claim_rate |   hard_violation_rate |   runtime_s |
|:-------------|--------:|---------:|---------:|---------------:|-------------------:|----------------------:|------------:|
| rob_noisy    |     0.2 |        5 |  47246.8 |         0.0407 |             0.0566 |                0.0033 |     427.179 |
| rob_scale500 |     0.2 |        3 | 244273   |         0.0405 |             0.0549 |                0.0044 |    1282.45  |

### Detection - rob_noisy

|   level | detector   | pr_auc        | f1            | precision     | recall        | fpr           | episode_detect_rate   | infer_ms_per_window   | n_params   |
|--------:|:-----------|:--------------|:--------------|:--------------|:--------------|:--------------|:----------------------|:----------------------|:-----------|
|     0.2 | rules      | 0.497 ± 0.159 | 0.514 ± 0.144 | 0.676 ± 0.109 | 0.420 ± 0.151 | 0.011 ± 0.003 | 0.486 ± 0.121         | 0.001 ± 0.000         | 0 ± 0      |
|     0.2 | iforest    | 0.354 ± 0.101 | 0.434 ± 0.097 | 0.384 ± 0.093 | 0.501 ± 0.109 | 0.048 ± 0.010 | 0.545 ± 0.071         | 0.011 ± 0.001         | 0 ± 0      |
|     0.2 | xgboost    | 0.825 ± 0.096 | 0.746 ± 0.097 | 0.801 ± 0.111 | 0.707 ± 0.112 | 0.011 ± 0.008 | 0.753 ± 0.106         | 0.004 ± 0.002         | 0 ± 0      |
|     0.2 | lstm       | 0.799 ± 0.122 | 0.727 ± 0.116 | 0.811 ± 0.078 | 0.666 ± 0.144 | 0.009 ± 0.004 | 0.697 ± 0.130         | 0.035 ± 0.007         | 21825 ± 0  |
|     0.2 | tcn        | 0.804 ± 0.126 | 0.739 ± 0.120 | 0.831 ± 0.085 | 0.677 ± 0.150 | 0.008 ± 0.005 | 0.707 ± 0.123         | 0.036 ± 0.008         | 24257 ± 0  |
|     0.2 | lstm_ae    | 0.613 ± 0.086 | 0.592 ± 0.068 | 0.609 ± 0.093 | 0.595 ± 0.121 | 0.024 ± 0.015 | 0.616 ± 0.100         | 0.030 ± 0.007         | 15859 ± 0  |
|     0.2 | tcn_xgb    | 0.850 ± 0.094 | 0.778 ± 0.092 | 0.823 ± 0.106 | 0.741 ± 0.093 | 0.010 ± 0.007 | 0.774 ± 0.083         | 0.040 ± 0.007         | 24257 ± 0  |
|     0.2 | hybrid     | 0.816 ± 0.115 | 0.749 ± 0.120 | 0.860 ± 0.051 | 0.675 ± 0.162 | 0.006 ± 0.002 | 0.702 ± 0.132         | 0.066 ± 0.015         | 40116 ± 0  |

### Detection - rob_scale500

|   level | detector   | pr_auc        | f1            | precision     | recall        | fpr           | episode_detect_rate   | infer_ms_per_window   | n_params   |
|--------:|:-----------|:--------------|:--------------|:--------------|:--------------|:--------------|:----------------------|:----------------------|:-----------|
|     0.2 | rules      | 0.510 ± 0.056 | 0.532 ± 0.042 | 0.839 ± 0.019 | 0.391 ± 0.048 | 0.005 ± 0.001 | 0.425 ± 0.051         | 0.001 ± 0.000         | 0 ± 0      |
|     0.2 | iforest    | 0.309 ± 0.051 | 0.386 ± 0.046 | 0.330 ± 0.043 | 0.471 ± 0.078 | 0.059 ± 0.012 | 0.562 ± 0.066         | 0.014 ± 0.001         | 0 ± 0      |
|     0.2 | xgboost    | 0.822 ± 0.045 | 0.771 ± 0.042 | 0.857 ± 0.050 | 0.702 ± 0.054 | 0.007 ± 0.003 | 0.765 ± 0.056         | 0.005 ± 0.003         | 0 ± 0      |
|     0.2 | lstm       | 0.820 ± 0.046 | 0.770 ± 0.046 | 0.897 ± 0.015 | 0.676 ± 0.064 | 0.005 ± 0.001 | 0.713 ± 0.053         | 0.029 ± 0.007         | 21825 ± 0  |
|     0.2 | tcn        | 0.835 ± 0.058 | 0.787 ± 0.059 | 0.892 ± 0.034 | 0.705 ± 0.074 | 0.005 ± 0.001 | 0.740 ± 0.058         | 0.040 ± 0.008         | 24257 ± 0  |
|     0.2 | lstm_ae    | 0.551 ± 0.038 | 0.514 ± 0.037 | 0.549 ± 0.087 | 0.491 ± 0.052 | 0.026 ± 0.010 | 0.570 ± 0.030         | 0.022 ± 0.002         | 15859 ± 0  |
|     0.2 | tcn_xgb    | 0.848 ± 0.049 | 0.800 ± 0.053 | 0.915 ± 0.022 | 0.713 ± 0.084 | 0.004 ± 0.001 | 0.757 ± 0.074         | 0.045 ± 0.006         | 24257 ± 0  |
|     0.2 | hybrid     | 0.836 ± 0.057 | 0.784 ± 0.061 | 0.910 ± 0.031 | 0.690 ± 0.080 | 0.004 ± 0.001 | 0.726 ± 0.066         | 0.061 ± 0.009         | 40116 ± 0  |

### Detection recall by attack family / attacker knowledge (id, all levels)

| detector   | recall[inflation]   | recall[replay]   | recall[forged_identity]   | recall[gradual]   | recall[on_off]   | recall[naive]   | recall[consistent]   | recall[adaptive]   |
|------------|---------------------|------------------|---------------------------|-------------------|------------------|-----------------|----------------------|--------------------|

### False-positive rate by benign event type (id)

| detector   | fpr[delay]   | fpr[dropout]   | fpr[stuck_sensor]   | fpr[overtime]   | fpr[maintenance]   | fpr[none]   |
|------------|--------------|----------------|---------------------|-----------------|--------------------|-------------|

### Financial protection - baselines vs ATFA - rob_noisy (percentages for rates)

|   level | system                               | fvs_pct     | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost     |
|--------:|:-------------------------------------|:------------|:-------------------|:------------------|:--------------------|:-----------------|:---------------|
|     0.2 | B0 approve all (smart contract only) | 100.0 ± 0.0 | 0.0 ± 0.0          | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 253263 ± 47679 |
|     0.2 | B1 hard rules only                   | 88.1 ± 4.7  | 8.7 ± 0.9          | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 224893 ± 53405 |
|     0.2 | B2 fixed amount threshold            | 62.0 ± 9.7  | 23.6 ± 6.7         | 4.2 ± 0.2         | 0.0 ± 0.0           | 51.694 ± 4.329   | 168213 ± 34833 |
|     0.2 | B3 detector only                     | 7.1 ± 2.9   | 85.3 ± 9.2         | 4.1 ± 0.6         | 0.4 ± 0.2           | 49.475 ± 4.953   | 35376 ± 8051   |
|     0.2 | B4 trust only                        | 28.7 ± 9.2  | 67.4 ± 11.6        | 4.3 ± 1.4         | 0.0 ± 0.0           | 55.008 ± 15.309  | 84649 ± 17345  |
|     0.2 | Oracle                               | 0.0 ± 0.0   | 100.0 ± 0.0        | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 0 ± 0          |
|     0.2 | ATFA                                 | 5.9 ± 2.5   | 87.8 ± 7.2         | 4.8 ± 1.3         | 0.4 ± 0.2           | 55.060 ± 14.008  | 33359 ± 5605   |
|     0.2 | ATFA (provisional thresholds)        | 3.8 ± 1.3   | 92.5 ± 4.4         | 7.7 ± 1.0         | 1.0 ± 0.3           | 81.269 ± 13.595  | 42390 ± 5133   |

### Financial protection - baselines vs ATFA - rob_scale500 (percentages for rates)

|   level | system                               | fvs_pct     | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost       |
|--------:|:-------------------------------------|:------------|:-------------------|:------------------|:--------------------|:-----------------|:-----------------|
|     0.2 | B0 approve all (smart contract only) | 100.0 ± 0.0 | 0.0 ± 0.0          | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 1293411 ± 133473 |
|     0.2 | B1 hard rules only                   | 85.5 ± 1.2  | 10.0 ± 0.6         | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 1106572 ± 127680 |
|     0.2 | B2 fixed amount threshold            | 58.1 ± 2.6  | 26.7 ± 2.2         | 3.7 ± 0.4         | 0.0 ± 0.0           | 47.739 ± 3.644   | 809946 ± 97713   |
|     0.2 | B3 detector only                     | 4.1 ± 0.9   | 87.6 ± 2.9         | 3.9 ± 0.8         | 0.8 ± 0.1           | 43.356 ± 6.871   | 164544 ± 20235   |
|     0.2 | B4 trust only                        | 26.1 ± 1.6  | 67.7 ± 1.8         | 4.8 ± 0.8         | 0.1 ± 0.2           | 64.360 ± 11.240  | 422217 ± 35309   |
|     0.2 | Oracle                               | 0.0 ± 0.0   | 100.0 ± 0.0        | 0.0 ± 0.0         | 0.0 ± 0.0           | 0.000 ± 0.000    | 0 ± 0            |
|     0.2 | ATFA                                 | 3.7 ± 0.4   | 89.7 ± 1.1         | 4.4 ± 0.1         | 0.4 ± 0.4           | 51.634 ± 6.912   | 144895 ± 30355   |
|     0.2 | ATFA (provisional thresholds)        | 3.0 ± 0.7   | 91.3 ± 1.7         | 6.6 ± 0.3         | 0.6 ± 0.2           | 67.420 ± 4.253   | 170388 ± 12349   |

### Trust models - rob_noisy (percentages for rates)

|   level | system            | fvs_pct   | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost   |
|--------:|:------------------|:----------|:-------------------|:------------------|:--------------------|:-----------------|:-------------|
|     0.2 | ATFA              | 5.9 ± 2.5 | 87.8 ± 7.2         | 4.8 ± 1.3         | 0.4 ± 0.2           | 55.060 ± 14.008  | 33359 ± 5605 |
|     0.2 | ATFA trust=none   | 7.1 ± 2.9 | 85.3 ± 9.2         | 4.1 ± 0.6         | 0.4 ± 0.2           | 49.475 ± 4.953   | 35376 ± 8051 |
|     0.2 | ATFA trust=static | 6.2 ± 3.2 | 86.4 ± 10.0        | 4.6 ± 1.4         | 0.7 ± 0.4           | 53.621 ± 10.295  | 38945 ± 8331 |
|     0.2 | ATFA trust=ewma   | 6.4 ± 2.7 | 86.4 ± 9.2         | 5.2 ± 1.3         | 0.5 ± 0.3           | 60.101 ± 10.122  | 36884 ± 8475 |
|     0.2 | ATFA trust=beta   | 6.5 ± 3.0 | 86.2 ± 9.8         | 4.5 ± 2.0         | 0.5 ± 0.2           | 52.118 ± 17.464  | 35149 ± 4234 |

### Trust models - rob_scale500 (percentages for rates)

|   level | system            | fvs_pct   | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost     |
|--------:|:------------------|:----------|:-------------------|:------------------|:--------------------|:-----------------|:---------------|
|     0.2 | ATFA              | 3.7 ± 0.4 | 89.7 ± 1.1         | 4.4 ± 0.1         | 0.4 ± 0.4           | 51.634 ± 6.912   | 144895 ± 30355 |
|     0.2 | ATFA trust=none   | 4.1 ± 0.9 | 87.6 ± 2.9         | 3.9 ± 0.8         | 0.8 ± 0.1           | 43.356 ± 6.871   | 164544 ± 20235 |
|     0.2 | ATFA trust=static | 4.2 ± 0.9 | 87.5 ± 3.1         | 3.7 ± 0.7         | 0.8 ± 0.2           | 42.193 ± 5.021   | 164309 ± 25016 |
|     0.2 | ATFA trust=ewma   | 4.6 ± 0.9 | 86.9 ± 2.8         | 3.9 ± 0.5         | 0.7 ± 0.1           | 42.336 ± 6.577   | 165002 ± 19111 |
|     0.2 | ATFA trust=beta   | 4.4 ± 0.9 | 87.1 ± 2.8         | 3.9 ± 1.0         | 0.5 ± 0.1           | 44.141 ± 8.056   | 153594 ± 18559 |

### Detector choice inside ATFA - rob_noisy (percentages for rates)

|   level | system                | fvs_pct    | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost    |
|--------:|:----------------------|:-----------|:-------------------|:------------------|:--------------------|:-----------------|:--------------|
|     0.2 | ATFA                  | 5.9 ± 2.5  | 87.8 ± 7.2         | 4.8 ± 1.3         | 0.4 ± 0.2           | 55.060 ± 14.008  | 33359 ± 5605  |
|     0.2 | ATFA detector=rules   | 19.8 ± 7.0 | 68.4 ± 13.8        | 4.2 ± 1.2         | 0.3 ± 0.1           | 52.333 ± 13.413  | 63595 ± 10689 |
|     0.2 | ATFA detector=iforest | 24.9 ± 8.6 | 67.8 ± 9.4         | 4.5 ± 1.3         | 0.7 ± 0.5           | 57.355 ± 11.516  | 82770 ± 17334 |
|     0.2 | ATFA detector=xgboost | 6.5 ± 2.9  | 87.0 ± 7.4         | 4.7 ± 0.1         | 0.5 ± 0.3           | 55.242 ± 5.485   | 36587 ± 5865  |
|     0.2 | ATFA detector=lstm    | 9.1 ± 4.2  | 85.3 ± 9.3         | 4.7 ± 0.9         | 0.4 ± 0.1           | 59.368 ± 6.118   | 41679 ± 9325  |
|     0.2 | ATFA detector=tcn     | 6.8 ± 2.3  | 86.8 ± 6.9         | 4.7 ± 0.9         | 0.3 ± 0.2           | 58.543 ± 10.110  | 34838 ± 5828  |
|     0.2 | ATFA detector=lstm_ae | 18.1 ± 5.7 | 73.4 ± 9.9         | 4.9 ± 0.3         | 0.2 ± 0.3           | 64.013 ± 12.705  | 60504 ± 6168  |
|     0.2 | ATFA detector=hybrid  | 6.8 ± 3.4  | 86.1 ± 7.8         | 4.8 ± 1.0         | 0.4 ± 0.2           | 57.539 ± 8.202   | 35301 ± 4019  |

### Detector choice inside ATFA - rob_scale500 (percentages for rates)

|   level | system                | fvs_pct    | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost     |
|--------:|:----------------------|:-----------|:-------------------|:------------------|:--------------------|:-----------------|:---------------|
|     0.2 | ATFA                  | 3.7 ± 0.4  | 89.7 ± 1.1         | 4.4 ± 0.1         | 0.4 ± 0.4           | 51.634 ± 6.912   | 144895 ± 30355 |
|     0.2 | ATFA detector=rules   | 22.9 ± 5.2 | 66.1 ± 7.6         | 4.5 ± 0.7         | 0.2 ± 0.0           | 54.034 ± 6.787   | 374593 ± 77969 |
|     0.2 | ATFA detector=iforest | 28.7 ± 6.9 | 62.1 ± 7.9         | 4.3 ± 0.4         | 0.4 ± 0.0           | 58.819 ± 3.487   | 455466 ± 59889 |
|     0.2 | ATFA detector=xgboost | 4.3 ± 0.9  | 89.0 ± 1.6         | 4.6 ± 0.3         | 0.6 ± 0.2           | 51.805 ± 1.108   | 163088 ± 7018  |
|     0.2 | ATFA detector=lstm    | 4.6 ± 0.4  | 89.3 ± 1.1         | 4.3 ± 0.3         | 0.5 ± 0.2           | 51.313 ± 1.641   | 155891 ± 15148 |
|     0.2 | ATFA detector=tcn     | 4.1 ± 0.7  | 89.3 ± 1.8         | 4.6 ± 0.6         | 0.5 ± 0.1           | 51.913 ± 3.047   | 147610 ± 9048  |
|     0.2 | ATFA detector=lstm_ae | 17.6 ± 3.0 | 71.9 ± 6.2         | 5.1 ± 0.2         | 0.3 ± 0.3           | 70.168 ± 12.740  | 324964 ± 39007 |
|     0.2 | ATFA detector=hybrid  | 4.1 ± 0.8  | 89.1 ± 2.3         | 4.8 ± 0.3         | 0.4 ± 0.1           | 54.913 ± 2.586   | 145560 ± 6601  |

### Ablations - rob_noisy (percentages for rates)

|   level | system                                               | fvs_pct     | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost     |
|--------:|:-----------------------------------------------------|:------------|:-------------------|:------------------|:--------------------|:-----------------|:---------------|
|     0.2 | ATFA                                                 | 5.9 ± 2.5   | 87.8 ± 7.2         | 4.8 ± 1.3         | 0.4 ± 0.2           | 55.060 ± 14.008  | 33359 ± 5605   |
|     0.2 | ATFA -detector (s=0)                                 | 50.6 ± 19.4 | 45.0 ± 23.0        | 2.7 ± 0.6         | 0.1 ± 0.1           | 34.017 ± 10.072  | 134064 ± 39710 |
|     0.2 | ATFA -exposure-weighted trust                        | 5.1 ± 2.1   | 89.3 ± 6.9         | 5.4 ± 1.2         | 0.5 ± 0.2           | 61.258 ± 11.337  | 34190 ± 5845   |
|     0.2 | ATFA -verification feedback                          | 8.0 ± 3.1   | 83.7 ± 9.6         | 5.7 ± 1.3         | 0.5 ± 0.5           | 63.963 ± 15.753  | 40798 ± 7616   |
|     0.2 | ATFA -asymmetric evidence                            | 5.4 ± 2.4   | 88.5 ± 7.2         | 5.0 ± 1.2         | 0.5 ± 0.2           | 56.323 ± 12.075  | 34436 ± 5051   |
|     0.2 | ATFA -low-trust gate                                 | 5.9 ± 2.4   | 87.8 ± 7.0         | 4.5 ± 1.6         | 0.4 ± 0.2           | 51.950 ± 16.642  | 32773 ± 6288   |
|     0.2 | ATFA -hard rules                                     | 4.9 ± 2.1   | 89.7 ± 6.5         | 5.4 ± 1.3         | 0.5 ± 0.1           | 62.014 ± 11.070  | 33827 ± 5019   |
|     0.2 | ATFA weighted-sum risk                               | 6.6 ± 2.7   | 86.6 ± 7.3         | 4.6 ± 0.7         | 0.6 ± 0.5           | 55.530 ± 7.195   | 38669 ± 9220   |
|     0.2 | ATFA +exposure term F (noisy-OR)                     | 6.2 ± 2.0   | 86.9 ± 6.2         | 4.6 ± 0.9         | 0.5 ± 0.3           | 53.950 ± 12.900  | 35867 ± 7249   |
|     0.2 | ATFA expected-loss risk (lambda=0.7)                 | 5.6 ± 2.1   | 88.4 ± 6.7         | 4.9 ± 1.0         | 0.6 ± 0.5           | 58.475 ± 15.306  | 37726 ± 8660   |
|     0.2 | ATFA +random audits                                  | 5.7 ± 2.1   | 88.3 ± 6.5         | 4.8 ± 1.0         | 0.4 ± 0.3           | 55.495 ± 9.853   | 37537 ± 6205   |
|     0.2 | ATFA v1 authorisation (noisy-OR+F, rolling exposure) | 7.2 ± 2.7   | 85.3 ± 7.9         | 4.4 ± 0.9         | 0.5 ± 0.4           | 51.158 ± 8.943   | 37735 ± 8343   |

### Ablations - rob_scale500 (percentages for rates)

|   level | system                                               | fvs_pct    | fraud_block_rate   | legit_hold_rate   | legit_reject_rate   | holds_per_1000   | total_cost      |
|--------:|:-----------------------------------------------------|:-----------|:-------------------|:------------------|:--------------------|:-----------------|:----------------|
|     0.2 | ATFA                                                 | 3.7 ± 0.4  | 89.7 ± 1.1         | 4.4 ± 0.1         | 0.4 ± 0.4           | 51.634 ± 6.912   | 144895 ± 30355  |
|     0.2 | ATFA -detector (s=0)                                 | 63.6 ± 5.2 | 32.9 ± 8.5         | 3.3 ± 0.3         | 0.1 ± 0.1           | 39.224 ± 5.369   | 873396 ± 127987 |
|     0.2 | ATFA -exposure-weighted trust                        | 3.7 ± 0.5  | 89.9 ± 1.3         | 4.5 ± 0.7         | 0.4 ± 0.2           | 51.139 ± 11.766  | 140861 ± 14393  |
|     0.2 | ATFA -verification feedback                          | 6.2 ± 1.2  | 84.1 ± 3.4         | 6.5 ± 0.8         | 0.4 ± 0.5           | 71.076 ± 10.533  | 190422 ± 28603  |
|     0.2 | ATFA -asymmetric evidence                            | 3.4 ± 0.6  | 90.4 ± 1.3         | 4.7 ± 0.2         | 0.5 ± 0.3           | 51.639 ± 1.558   | 144142 ± 11398  |
|     0.2 | ATFA -low-trust gate                                 | 3.7 ± 0.4  | 89.7 ± 1.1         | 4.4 ± 0.1         | 0.4 ± 0.4           | 51.634 ± 6.912   | 144895 ± 30355  |
|     0.2 | ATFA -hard rules                                     | 3.3 ± 0.5  | 90.6 ± 1.1         | 4.6 ± 0.5         | 0.5 ± 0.1           | 49.794 ± 3.035   | 143226 ± 13336  |
|     0.2 | ATFA weighted-sum risk                               | 4.6 ± 0.6  | 88.3 ± 1.3         | 3.8 ± 0.5         | 0.4 ± 0.3           | 45.889 ± 6.469   | 146712 ± 14699  |
|     0.2 | ATFA +exposure term F (noisy-OR)                     | 4.2 ± 0.4  | 88.7 ± 1.3         | 4.0 ± 0.5         | 0.5 ± 0.2           | 46.232 ± 7.455   | 148888 ± 17638  |
|     0.2 | ATFA expected-loss risk (lambda=0.7)                 | 3.5 ± 0.4  | 90.1 ± 1.1         | 4.5 ± 0.4         | 0.6 ± 0.2           | 49.191 ± 2.606   | 157723 ± 20794  |
|     0.2 | ATFA +random audits                                  | 3.6 ± 0.4  | 90.0 ± 0.8         | 4.7 ± 0.6         | 0.6 ± 0.4           | 51.731 ± 7.824   | 173573 ± 30395  |
|     0.2 | ATFA v1 authorisation (noisy-OR+F, rolling exposure) | 4.0 ± 0.4  | 89.3 ± 1.0         | 4.8 ± 0.1         | 0.5 ± 0.2           | 54.074 ± 4.806   | 161638 ± 23159  |

### Trust behaviour (id)

| level   | system   | honest_low_trust_rate   | low_trust_reach_rate   | median_days_to_low   | mean_trust_on_fraud   | mean_trust_on_legit   |
|---------|----------|-------------------------|------------------------|----------------------|-----------------------|-----------------------|

### Fraudulent value settled by attack family (%)

| scenario     | system           |   fvs_pct[forged_identity] |   fvs_pct[gradual] |   fvs_pct[inflation] |   fvs_pct[on_off] |   fvs_pct[replay] |
|:-------------|:-----------------|---------------------------:|-------------------:|---------------------:|------------------:|------------------:|
| rob_noisy    | ATFA             |                        4.7 |                2.1 |                 10.1 |              14.9 |              16.7 |
| rob_noisy    | B3 detector only |                        5.5 |                2.9 |                 17.1 |              16.9 |              16.6 |
| rob_scale500 | ATFA             |                        2.4 |                2.7 |                  6.7 |               3.6 |               7   |
| rob_scale500 | B3 detector only |                        1.8 |                4.6 |                  7.6 |               3.4 |               5.3 |

### PRIMARY (pre-registered) paired Wilcoxon tests, ATFA vs 3 comparators, Holm over 3

| scenario   |   level | metric     | comparator                |   atfa_mean |   comparator_mean |   mean_diff |   diff_ci95_lo |   diff_ci95_hi |   rank_biserial | atfa_better_in   |      p |   p_holm |
|:-----------|--------:|:-----------|:--------------------------|------------:|------------------:|------------:|---------------:|---------------:|----------------:|:-----------------|-------:|---------:|
| rob_noisy  |     0.2 | fvs        | ATFA trust=beta           |     13969.6 |           15486.1 |    -1516.47 |       -5428.96 |        1166.08 |            -0.2 | 3/5              | 0.8125 |   0.8125 |
| rob_noisy  |     0.2 | fvs        | B2 fixed amount threshold |     13969.6 |          156373   |  -142403    |     -170927    |     -113880    |            -1   | 5/5              | 0.0625 |   0.1875 |
| rob_noisy  |     0.2 | fvs        | B3 detector only          |     13969.6 |           17135.1 |    -3165.52 |       -7413.77 |         875.1  |            -0.6 | 3/5              | 0.3125 |   0.625  |
| rob_noisy  |     0.2 | total_cost | ATFA trust=beta           |     33359.3 |           35148.9 |    -1789.63 |       -4383.39 |         522.98 |            -0.6 | 4/5              | 0.3125 |   0.625  |
| rob_noisy  |     0.2 | total_cost | B2 fixed amount threshold |     33359.3 |          168213   |  -134854    |     -164455    |     -105253    |            -1   | 5/5              | 0.0625 |   0.1875 |
| rob_noisy  |     0.2 | total_cost | B3 detector only          |     33359.3 |           35376.2 |    -2016.86 |       -4260.18 |         356.75 |            -0.6 | 3/5              | 0.3125 |   0.625  |

### Secondary: paired Wilcoxon tests vs all comparators (Holm over all)

| scenario   |   level | metric     | comparator                                           |   atfa_mean |   comparator_mean |   mean_diff |   diff_ci95_lo |   diff_ci95_hi |   rank_biserial | atfa_better_in   |      p |   p_holm |
|:-----------|--------:|:-----------|:-----------------------------------------------------|------------:|------------------:|------------:|---------------:|---------------:|----------------:|:-----------------|-------:|---------:|
| rob_noisy  |     0.2 | fvs        | ATFA (provisional thresholds)                        |     13969.6 |           9255.17 |     4714.42 |        3357.06 |        6839.72 |          1      | 0/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA +exposure term F (noisy-OR)                     |     13969.6 |          15202.4  |    -1232.79 |       -4311.56 |        1845.98 |         -0.2    | 2/5              | 0.8125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA +random audits                                  |     13969.6 |          13618.7  |      350.87 |        -271.9  |        1264.11 |          0.3333 | 1/5              | 0.75   |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -asymmetric evidence                            |     13969.6 |          12984.7  |      984.92 |         -56.55 |        2027.52 |          0.6    | 1/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -detector (s=0)                                 |     13969.6 |         125056    |  -111086    |     -142900    |      -81325    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -exposure-weighted trust                        |     13969.6 |          12068.6  |     1900.97 |         435.17 |        2992.76 |          0.8667 | 1/5              | 0.125  |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -hard rules                                     |     13969.6 |          11606.9  |     2362.68 |        1396.74 |        3198.24 |          1      | 0/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -low-trust gate                                 |     13969.6 |          14056.2  |      -86.62 |        -453.15 |         193.29 |         -0.3333 | 1/5              | 1      |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA -verification feedback                          |     13969.6 |          19591    |    -5621.41 |      -10660.9  |       -1435.28 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=hybrid                                 |     13969.6 |          16115.3  |    -2145.69 |       -3945.89 |         306.07 |         -0.7333 | 4/5              | 0.1875 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=iforest                                |     13969.6 |          62278.5  |   -48308.9  |      -63614.2  |      -33473.8  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=lstm                                   |     13969.6 |          22000.1  |    -8030.52 |      -14413.5  |       -2436.18 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=lstm_ae                                |     13969.6 |          43837.9  |   -29868.3  |      -33296.2  |      -25662.3  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=rules                                  |     13969.6 |          48545.7  |   -34576.1  |      -44373.5  |      -24778.8  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=tcn                                    |     13969.6 |          16483.1  |    -2513.54 |       -5317.09 |        -149.55 |         -0.7333 | 4/5              | 0.1875 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA detector=xgboost                                |     13969.6 |          15509.1  |    -1539.49 |       -4047.3  |         940.14 |         -0.2    | 2/5              | 0.8125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA expected-loss risk (lambda=0.7)                 |     13969.6 |          13536    |      433.62 |       -1330.29 |        2197.53 |          0.2    | 2/5              | 0.8125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA trust=beta                                      |     13969.6 |          15486.1  |    -1516.47 |       -5428.96 |        1166.08 |         -0.2    | 3/5              | 0.8125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA trust=ewma                                      |     13969.6 |          15373.1  |    -1403.54 |       -5748.54 |        1552.34 |         -0.0667 | 3/5              | 1      |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA trust=none                                      |     13969.6 |          17135.1  |    -3165.52 |       -7413.77 |         875.1  |         -0.6    | 3/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA trust=static                                    |     13969.6 |          15124.1  |    -1154.5  |       -7348.99 |        3809.11 |         -0.0667 | 2/5              | 1      |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA v1 authorisation (noisy-OR+F, rolling exposure) |     13969.6 |          17498.9  |    -3529.35 |       -5736.29 |       -1439.4  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | ATFA weighted-sum risk                               |     13969.6 |          16090.5  |    -2120.96 |       -5490.98 |        1012.79 |         -0.3333 | 3/5              | 0.625  |        1 |
| rob_noisy  |     0.2 | fvs        | B0 approve all (smart contract only)                 |     13969.6 |         253263    |  -239293    |     -277506    |     -201080    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | B1 hard rules only                                   |     13969.6 |         224893    |  -210924    |     -253454    |     -168394    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | B2 fixed amount threshold                            |     13969.6 |         156373    |  -142403    |     -170927    |     -113880    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | fvs        | B3 detector only                                     |     13969.6 |          17135.1  |    -3165.52 |       -7413.77 |         875.1  |         -0.6    | 3/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | fvs        | B4 trust only                                        |     13969.6 |          71468.7  |   -57499.1  |      -69557    |      -39636.1  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA (provisional thresholds)                        |     33359.3 |          42390.1  |    -9030.74 |      -12092.3  |       -6478.34 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA +exposure term F (noisy-OR)                     |     33359.3 |          35867.2  |    -2507.93 |       -6178.6  |         552.65 |         -0.6    | 4/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA +random audits                                  |     33359.3 |          37537.3  |    -4178.01 |       -6209.66 |       -2758.67 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -asymmetric evidence                            |     33359.3 |          34436    |    -1076.72 |       -2771.4  |         867.93 |         -0.4667 | 3/5              | 0.4375 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -detector (s=0)                                 |     33359.3 |         134064    |  -100705    |     -131547    |      -70178.7  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -exposure-weighted trust                        |     33359.3 |          34189.8  |     -830.45 |       -3316    |        2058.13 |         -0.3333 | 3/5              | 0.625  |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -hard rules                                     |     33359.3 |          33827    |     -467.7  |       -3254.61 |        2690.29 |         -0.0667 | 3/5              | 1      |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -low-trust gate                                 |     33359.3 |          32773.5  |      585.82 |           0    |        1248.6  |          1      | 0/5              | 0.5    |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA -verification feedback                          |     33359.3 |          40798.1  |    -7438.77 |      -10133.8  |       -4874.9  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=hybrid                                 |     33359.3 |          35301    |    -1941.65 |       -3541.3  |        -359.84 |         -0.8667 | 4/5              | 0.125  |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=iforest                                |     33359.3 |          82769.9  |   -49410.6  |      -63445.6  |      -35459.9  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=lstm                                   |     33359.3 |          41679.4  |    -8320.06 |      -11431.8  |       -4661.63 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=lstm_ae                                |     33359.3 |          60503.7  |   -27144.4  |      -32363.7  |      -21140.8  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=rules                                  |     33359.3 |          63595.1  |   -30235.8  |      -36057.2  |      -23516.4  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=tcn                                    |     33359.3 |          34837.8  |    -1478.5  |       -2870.59 |        -309.13 |         -0.8667 | 4/5              | 0.125  |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA detector=xgboost                                |     33359.3 |          36587.4  |    -3228.11 |       -6263.57 |        -843.24 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA expected-loss risk (lambda=0.7)                 |     33359.3 |          37725.9  |    -4366.64 |       -9057.22 |        -249.65 |         -0.7333 | 4/5              | 0.1875 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA trust=beta                                      |     33359.3 |          35148.9  |    -1789.63 |       -4383.39 |         522.98 |         -0.6    | 4/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA trust=ewma                                      |     33359.3 |          36883.9  |    -3524.56 |       -7333.77 |        -848.32 |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA trust=none                                      |     33359.3 |          35376.2  |    -2016.86 |       -4260.18 |         356.75 |         -0.6    | 3/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA trust=static                                    |     33359.3 |          38944.7  |    -5585.4  |       -9742.39 |       -2088.5  |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA v1 authorisation (noisy-OR+F, rolling exposure) |     33359.3 |          37734.9  |    -4375.61 |       -8385.32 |        -953.42 |         -0.8667 | 4/5              | 0.125  |        1 |
| rob_noisy  |     0.2 | total_cost | ATFA weighted-sum risk                               |     33359.3 |          38669.4  |    -5310.12 |      -10304    |       -1079.07 |         -0.8667 | 4/5              | 0.125  |        1 |
| rob_noisy  |     0.2 | total_cost | B0 approve all (smart contract only)                 |     33359.3 |         253263    |  -219903    |     -258567    |     -181239    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | B1 hard rules only                                   |     33359.3 |         224893    |  -191534    |     -234514    |     -148554    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | B2 fixed amount threshold                            |     33359.3 |         168213    |  -134854    |     -164455    |     -105253    |         -1      | 5/5              | 0.0625 |        1 |
| rob_noisy  |     0.2 | total_cost | B3 detector only                                     |     33359.3 |          35376.2  |    -2016.86 |       -4260.18 |         356.75 |         -0.6    | 3/5              | 0.3125 |        1 |
| rob_noisy  |     0.2 | total_cost | B4 trust only                                        |     33359.3 |          84649    |   -51289.7  |      -64115.1  |      -33566.9  |         -1      | 5/5              | 0.0625 |        1 |

### Share of worlds where validation calibration met the hold/reject budgets

| system                                               |   calib_feasible |
|:-----------------------------------------------------|-----------------:|
| ATFA                                                 |            1     |
| ATFA (provisional thresholds)                        |            1     |
| ATFA +exposure term F (noisy-OR)                     |            1     |
| ATFA +random audits                                  |            1     |
| ATFA -asymmetric evidence                            |            1     |
| ATFA -detector (s=0)                                 |            1     |
| ATFA -exposure-weighted trust                        |            1     |
| ATFA -hard rules                                     |            1     |
| ATFA -low-trust gate                                 |            1     |
| ATFA -verification feedback                          |            0.375 |
| ATFA detector=hybrid                                 |            1     |
| ATFA detector=iforest                                |            1     |
| ATFA detector=lstm                                   |            1     |
| ATFA detector=lstm_ae                                |            1     |
| ATFA detector=rules                                  |            1     |
| ATFA detector=tcn                                    |            1     |
| ATFA detector=xgboost                                |            1     |
| ATFA expected-loss risk (lambda=0.7)                 |            1     |
| ATFA trust=beta                                      |            1     |
| ATFA trust=ewma                                      |            1     |
| ATFA trust=none                                      |            1     |
| ATFA trust=static                                    |            1     |
| ATFA v1 authorisation (noisy-OR+F, rolling exposure) |            1     |
| ATFA weighted-sum risk                               |            1     |
| B0 approve all (smart contract only)                 |            1     |
| B1 hard rules only                                   |            1     |
| B2 fixed amount threshold                            |            1     |
| B3 detector only                                     |            1     |
| B4 trust only                                        |            1     |
| Oracle                                               |            1     |
