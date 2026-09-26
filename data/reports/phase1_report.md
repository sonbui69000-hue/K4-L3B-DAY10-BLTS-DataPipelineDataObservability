# Phase 1 Baseline Report

## Run summary

| Field | Value |
| --- | --- |
| Source | Crossref REST API |
| Query | agentic retrieval augmented generation large language model |
| Filter | from-pub-date:2026-03-30,has-abstract:true |
| Raw records | 24 |
| Clean rows | 24 |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Chroma collection | papers-baseline |
| Run time | 2026-09-26T05:58:52.066248+00:00 |

## Baseline metrics

| Metric | Value |
| --- | ---: |
| Samples | 10 |
| Retrieval hit rate | 100.00% |
| Mean token F1 | 100.00% |
| Judge accuracy | 100.00% |
| Mean judge score | 5 |

## Data quality gate

Overall status: PASS

| Expectation | Result |
| --- | --- |
| expect_table_row_count_to_be_between | PASS |
| expect_column_values_to_not_be_null | PASS |
| expect_column_values_to_not_be_null | PASS |
| expect_column_values_to_not_be_null | PASS |
| expect_column_values_to_be_unique | PASS |
| expect_column_value_lengths_to_be_between | PASS |

## Freshness SLA

| Field | Value |
| --- | --- |
| Latest published | 2026-07-22 |
| Oldest published | 2026-03-28 |
| Stale rows | 1 |
| Stale ratio | 4.17% |
| Threshold days | 180 |
| Freshness status | FRESH |
