# PureChain PoA² measurements

Contract `0x6592cBD3CE1303EAfBfDE9f65301DD428844Ed5E` (chain 900520900520, deployment gas 596387, block 1814387). Gas in EVM units; the fee is zero on this network. Finality = inclusion (on-demand authority-sealed blocks).


### E1 confirmation latency (sequential single anchors)

|   n_tx |   ok |   latency_ms_p50 |   latency_ms_p95 |   latency_ms_mean |   gas_per_record |   tx_bytes |
|-------:|-----:|-----------------:|-----------------:|------------------:|-----------------:|-----------:|
|    100 |  100 |           1981.6 |           2025.4 |            1979.2 |          54678.9 |        237 |

### E2 batching

|   records_per_tx |   n_tx |   ok |   latency_ms_p50 |   latency_ms_p95 |   gas_per_record |   records_per_s_sequential |
|-----------------:|-------:|-----:|-----------------:|-----------------:|-----------------:|---------------------------:|
|                1 |     10 |   10 |           1967.3 |           2054   |          54692   |                        0.5 |
|               10 |     10 |   10 |           1977.2 |           2321.6 |          26903.1 |                        5.1 |
|               50 |     10 |   10 |           1966.1 |           2316.9 |          24421.3 |                       25.3 |
|              100 |     10 |   10 |           1976.1 |           2009.3 |          24111.7 |                       50.8 |

### E3 sustained offered load (one authoriser account)

| experiment               |   records_per_tx |   offered_tps |   sent |   ok |   failed_or_timeout |   throughput_tps |   throughput_records_per_s |   latency_ms_p50 |   latency_ms_p95 |   latency_ms_p99 |   mean_tx_per_block |
|:-------------------------|-----------------:|--------------:|-------:|-----:|--------------------:|-----------------:|---------------------------:|-----------------:|-----------------:|-----------------:|--------------------:|
| E3 load                  |                1 |             5 |    100 |  100 |                   0 |              4.6 |                        4.6 |           1735.2 |           2478.3 |           2560.4 |                 4.8 |
| E3 load                  |                1 |            10 |    200 |  200 |                   0 |              9.2 |                        9.2 |           1839.7 |           2690.9 |           2991.7 |                 9.5 |
| E3 load                  |                1 |            20 |    400 |  400 |                   0 |             16.3 |                       16.3 |           4707.6 |           5955.1 |           6304.2 |                16.7 |
| E3 load                  |                1 |            50 |   1000 | 1000 |                   0 |             14.7 |                       14.7 |          24073.7 |          46537.1 |          48111.3 |                15.2 |
| E3 load                  |                1 |           100 |   2000 | 2000 |                   0 |             16   |                       16   |          51860.4 |          97390.8 |         102675   |                16.3 |
| E3b batched load (k=100) |              100 |             1 |     20 |   20 |                   0 |              0.9 |                       91.7 |           2246.9 |           2822.2 |           2826.7 |                 1.1 |
| E3b batched load (k=100) |              100 |             2 |     40 |   40 |                   0 |              1.8 |                      177.8 |           2510.5 |           3103.4 |           3107   |                 2   |
| E3b batched load (k=100) |              100 |             5 |    100 |  100 |                   0 |              2.9 |                      291.8 |           8582.6 |          13790.2 |          14468.1 |                 3.1 |

### E5 per-sender limit: 1 vs N authoriser accounts

| experiment                   |   offered_tps |   sent |   ok |   failed_or_timeout |   throughput_tps |   latency_ms_p50 |   latency_ms_p95 |   mean_tx_per_block |
|:-----------------------------|--------------:|-------:|-----:|--------------------:|-----------------:|-----------------:|-----------------:|--------------------:|
| E5 multi-account (1 senders) |            20 |    400 |  400 |                   0 |             14.7 |           5163.2 |           7555.9 |                15.4 |
| E5 multi-account (1 senders) |            50 |   1000 | 1000 |                   0 |             17.3 |          22761.4 |          37040.4 |                17.5 |
| E5 multi-account (1 senders) |           100 |   2000 | 1998 |                   2 |             17.3 |          47957.7 |          88714.6 |                17.4 |
| E5 multi-account (4 senders) |            20 |    400 |  400 |                   0 |             18.2 |           1696.9 |           2409.4 |                18.2 |
| E5 multi-account (4 senders) |            50 |   1000 | 1000 |                   0 |             45   |           2064.1 |           3069   |                45.5 |
| E5 multi-account (4 senders) |           100 |   2000 | 2000 |                   0 |             59.5 |           5923.5 |          11993.8 |                60.8 |

### E4 pre-settlement check (isSettleable eth_call)

|   n_tx |   latency_ms_p50 |   latency_ms_p95 |
|-------:|-----------------:|-----------------:|
|    100 |             55.3 |             91.3 |
