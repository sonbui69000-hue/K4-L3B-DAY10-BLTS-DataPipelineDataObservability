from __future__ import annotations

from typing import Any

from core.utils import write_text


def _percent(value: Any) -> str:
    return f"{float(value) * 100:.2f}%" if isinstance(value, (int, float)) else "N/A"


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the evidence-backed baseline pipeline report."""
    expectation_rows = []
    for item in quality.get("expectations", []):
        expectation_rows.append(
            f"| {item.get('expectation_type', 'unknown')} | "
            f"{'PASS' if item.get('success') else 'FAIL'} |"
        )
    expectations = "\n".join(expectation_rows) or "| No expectations | N/A |"
    markdown = f"""# Phase 1 Baseline Report

## Run summary

| Field | Value |
| --- | --- |
| Source | {source_summary.get("source", "N/A")} |
| Query | {source_summary.get("query", "N/A")} |
| Filter | {source_summary.get("filter", "N/A")} |
| Raw records | {source_summary.get("records", "N/A")} |
| Clean rows | {source_summary.get("clean_rows", "N/A")} |
| Embedding model | {source_summary.get("embedding_model", "N/A")} |
| Chroma collection | {source_summary.get("collection_name", "N/A")} |
| Run time | {source_summary.get("run_at", "N/A")} |

## Baseline metrics

| Metric | Value |
| --- | ---: |
| Samples | {metrics.get("samples", "N/A")} |
| Retrieval hit rate | {_percent(metrics.get("retrieval_hit_rate"))} |
| Mean token F1 | {_percent(metrics.get("mean_token_f1"))} |
| Judge accuracy | {_percent(metrics.get("judge_accuracy"))} |
| Mean judge score | {metrics.get("mean_judge_score", "N/A")} |

## Data quality gate

Overall status: {"PASS" if quality.get("success") else "FAIL"}

| Expectation | Result |
| --- | --- |
{expectations}

## Freshness SLA

| Field | Value |
| --- | --- |
| Latest published | {freshness.get("latest_published", "N/A")} |
| Oldest published | {freshness.get("oldest_published", "N/A")} |
| Stale rows | {freshness.get("stale_rows", "N/A")} |
| Stale ratio | {_percent(freshness.get("stale_ratio"))} |
| Threshold days | {freshness.get("threshold_days", "N/A")} |
| Freshness status | {"FRESH" if freshness.get("is_fresh") else "STALE"} |
"""
    write_text(report_path, markdown)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Write a three-state baseline/corrupted/repaired comparison report."""
    baseline_quality = baseline_quality or {}
    baseline_freshness = baseline_freshness or {}
    metric_rows = []
    for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        metric_rows.append(
            f"| {key} | {baseline_metrics.get(key, 'N/A')} | "
            f"{corrupted_metrics.get(key, 'N/A')} | {repaired_metrics.get(key, 'N/A')} |"
        )
    markdown = f"""# Corruption and Repair Report

## Performance comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
{chr(10).join(metric_rows)}

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality gate | {baseline_quality.get("success", "N/A")} | {corrupted_quality.get("success", "N/A")} | {repaired_quality.get("success", "N/A")} |
| Freshness | {baseline_freshness.get("is_fresh", "N/A")} | {corrupted_freshness.get("is_fresh", "N/A")} | {repaired_freshness.get("is_fresh", "N/A")} |
| Stale ratio | {_percent(baseline_freshness.get("stale_ratio"))} | {_percent(corrupted_freshness.get("stale_ratio"))} | {_percent(repaired_freshness.get("stale_ratio"))} |

## Interpretation

- Corruption is expected to reduce quality-gate signals through blank summaries, truncated titles, and duplicate paper IDs.
- Repair rebuilds the dataset from the preserved raw snapshot and re-evaluates it on the same benchmark.
"""
    write_text(report_path, markdown)
