# Triage-Bench Benchmark Report

This report summarizes the fixed 200-case controlled benchmark snapshot used
by the paper.

- Cases: 200
- Fault families: 23
- Cases with prior same-family memory: 177
- Window: `anchor-30m to anchor`
- Retrieval: TF-IDF with cosine similarity
- Tie policy: fixed tie break after equal-score records

## Paper Table View

| Input condition | First-service@1 | Service-metric@1 | Tied rec. |
| --- | ---: | ---: | ---: |
| Alert message only | 71/200 | 61/200 | 13.19 |
| + maximum change | 155/200 | 146/200 | 12.38 |
| + earliest abnormal | 159/200 | 149/200 | 8.02 |
| + change order | 155/200 | 153/200 | 1.04 |

## Prior-Family View

| Input condition | First-service@1 | Service-metric@1 |
| --- | ---: | ---: |
| + change order | 143/177 | 141/177 |

## Scenarios

| Scenario | Cases |
| --- | ---: |
| S01_ad_high_cpu | 10 |
| S02_payment_failure | 14 |
| S03_checkout_pod_kill | 14 |
| S04_productcatalog_network_delay | 14 |
| S05_email_memory_leak | 11 |
| S06_reco_cache_growth | 11 |
| S07_homepage_flood | 10 |
| S08_kafka_queue_lag | 14 |
| S09_payment_dns_fault | 11 |
| S10_productcatalog_failure | 27 |
| S11_image_slow_load | 11 |
| S12_cart_failed_readiness | 11 |
| S13_payment_unreachable | 1 |
| S14_recommendation_network_loss | 1 |
| S15_email_pod_kill | 1 |
| S16_productcatalog_http_abort | 1 |
| S17_ad_pod_failure | 4 |
| S18_recommendation_pod_failure | 4 |
| S19_frontend_pod_failure | 6 |
| S20_email_pod_failure | 6 |
| S21_cart_pod_failure | 6 |
| S22_image_provider_memory_stress | 6 |
| S23_productcatalog_flag_mixed | 6 |
