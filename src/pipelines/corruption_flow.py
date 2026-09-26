from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    """Rebuild the clean dataframe from the preserved raw snapshot."""
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    return repaired_df


def _evaluate_state(
    df: pd.DataFrame,
    settings: Settings,
    embeddings_path,
    metrics_path,
    answers_path,
    quality_stage: str,
):
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=embeddings_path)
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=metrics_path,
        answers_output_path=answers_path,
    )
    quality = run_data_quality_checks(df, settings, quality_stage)
    freshness_path = settings.paths.quality_dir / f"{quality_stage}_freshness_report.json"
    freshness = build_freshness_report(df, settings, freshness_path)
    return evaluation, quality, freshness


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Run corruption, impact measurement, raw-snapshot repair, and comparison."""
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality = (
        read_json(settings.paths.baseline_quality_report)
        if settings.paths.baseline_quality_report.exists()
        else {}
    )
    baseline_freshness = (
        read_json(settings.paths.freshness_report)
        if settings.paths.freshness_report.exists()
        else {}
    )

    clean_df = pd.read_json(settings.paths.clean_json)
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    corrupted_evaluation, corrupted_quality, corrupted_freshness = _evaluate_state(
        corrupted_df,
        settings,
        settings.paths.corrupted_embeddings_json,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
        "corrupted",
    )

    repaired_df = repair_from_raw_snapshot(settings)
    repaired_evaluation, repaired_quality, repaired_freshness = _evaluate_state(
        repaired_df,
        settings,
        settings.paths.repaired_embeddings_json,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
        "repaired",
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_evaluation.summary,
        repaired_metrics=repaired_evaluation.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    return {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_evaluation.summary,
        "repaired_metrics": repaired_evaluation.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_freshness": corrupted_freshness,
        "repaired_freshness": repaired_freshness,
    }


def main() -> None:
    run_corruption_flow_pipeline(load_settings())
