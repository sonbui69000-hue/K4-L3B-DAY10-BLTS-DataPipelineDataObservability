# Corruption and Repair Report

## Performance comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| retrieval_hit_rate | 1.0 | 1.0 | 1.0 |
| mean_token_f1 | 1.0 | 0.874074074074074 | 1.0 |
| judge_accuracy | 1.0 | 0.9 | 1.0 |
| mean_judge_score | 5 | 4.4 | 5 |

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality gate | True | False | True |
| Freshness | True | True | True |
| Stale ratio | 4.17% | 14.29% | 4.17% |

## Interpretation

- Corruption is expected to reduce quality-gate signals through blank summaries, truncated titles, and duplicate paper IDs.
- Repair rebuilds the dataset from the preserved raw snapshot and re-evaluates it on the same benchmark.
