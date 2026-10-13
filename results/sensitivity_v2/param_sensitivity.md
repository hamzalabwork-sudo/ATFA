# One-at-a-time parameter sensitivity (cached confirmatory worlds: id 10 % and 20 %, seeds 20-29)

| parameter                 | value       |   ATFA fraud settled % |   B3 fraud settled % |   ATFA legit held % |   ATFA cost k |   B3 cost k |   ATFA fraud <= B3 |   ATFA budgets met |
|:--------------------------|:------------|-----------------------:|---------------------:|--------------------:|--------------:|------------:|-------------------:|-------------------:|
| default                   | default     |                  2.796 |                4.033 |               4.337 |        24.847 |      26.751 |               0.8  |               1    |
| verification p_detect     | 0.8         |                  4.134 |                4.97  |               3.92  |        28.197 |      30.376 |               0.7  |               1    |
| verification p_detect     | 0.9         |                  3.271 |                4.322 |               4.356 |        26.661 |      28.661 |               0.75 |               1    |
| verification p_detect     | 1.0         |                  2.479 |                3.334 |               4.316 |        22.39  |      22.828 |               0.8  |               1    |
| verification delay (days) | 1           |                  2.788 |                4.033 |               4.405 |        24.808 |      26.751 |               0.8  |               1    |
| verification delay (days) | 14          |                  3.608 |                4.033 |               4.112 |        24.78  |      26.751 |               0.5  |               1    |
| verification delay (days) | 7           |                  3.467 |                4.033 |               4.199 |        24.804 |      26.751 |               0.75 |               1    |
| legit hold budget         | 0.025       |                  4.339 |                5.459 |               2.619 |        22.582 |      25.562 |               0.7  |               0.8  |
| legit hold budget         | 0.1         |                  1.774 |                3.211 |               7.764 |        29.801 |      31.965 |               0.85 |               1    |
| legit reject budget       | 0.005       |                  3.04  |                4.264 |               4.242 |        22.608 |      24.06  |               0.7  |               1    |
| legit reject budget       | 0.02        |                  2.547 |                3.622 |               4.268 |        29.233 |      34.231 |               0.7  |               1    |
| trust forgetting gamma    | 0.95        |                  2.876 |                4.033 |               4.3   |        25.109 |      26.751 |               0.8  |               1    |
| trust forgetting gamma    | 0.99        |                  3.074 |                4.033 |               4.402 |        24.452 |      26.751 |               0.8  |               1    |
| trust asymmetry kappa     | 1.0         |                  2.677 |                4.033 |               4.37  |        24.796 |      26.751 |               0.85 |               1    |
| trust asymmetry kappa     | 4.0         |                  3.538 |                4.033 |               4.886 |        24.585 |      26.751 |               0.65 |               0.8  |
| verification weight       | 10.0        |                  2.561 |                4.033 |               4.279 |        23.598 |      26.751 |               0.9  |               1    |
| verification weight       | 2.0         |                  3.715 |                4.033 |               4.312 |        26.693 |      26.751 |               0.55 |               1    |
| trust prior (a0, b0)      | [16.0, 2.0] |                  3.07  |                4.033 |               4.191 |        25.44  |      26.751 |               0.85 |               1    |
| trust prior (a0, b0)      | [4.0, 1.0]  |                  3.015 |                4.033 |               4.347 |        24.857 |      26.751 |               0.8  |               1    |
| low-trust threshold       | 0.5         |                  2.796 |                4.033 |               4.327 |        24.822 |      26.751 |               0.8  |               1    |
| low-trust threshold       | 0.7         |                  3.106 |                4.033 |               4.717 |        25.978 |      26.751 |               0.75 |               0.95 |
