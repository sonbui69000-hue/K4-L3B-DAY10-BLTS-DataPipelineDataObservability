from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd
from great_expectations.expectations.core import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectTableRowCountToBeBetween,
)

from great_expectations.expectations.core.expect_column_values_to_not_be_null import ExpectColumnValuesToNotBeNull

from core.config import Settings
from core.utils import write_json


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Evaluate the freshness SLA using the configured age threshold."""
    total_rows = int(len(df))
    if "age_days" not in df.columns or total_rows == 0:
        return {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": total_rows,
            "stale_ratio": 0.0 if total_rows == 0 else None,
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio": 0.25,
            "is_fresh": False if total_rows == 0 else None,
        }

    ages = pd.to_numeric(df["age_days"], errors="coerce")
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows
    published = pd.to_datetime(df.get("published"), errors="coerce", utc=True)
    valid_published = published.dropna()

    return {
        "latest_published": valid_published.max().strftime("%Y-%m-%d") if not valid_published.empty else None,
        "oldest_published": valid_published.min().strftime("%Y-%m-%d") if not valid_published.empty else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": stale_ratio <= 0.25,
    }


def _report_path(settings: Settings, report_name: str) -> Path:
    known_paths = {
        "baseline": settings.paths.baseline_quality_report,
        "corrupted": settings.paths.corrupted_quality_report,
    }
    return known_paths.get(report_name, settings.paths.quality_dir / f"{report_name}_quality_report.json")


def _serialize_validation(result: Any) -> dict[str, Any]:
    payload = result.to_json_dict()
    expectation = payload.get("expectation_config", {})
    return {
        "expectation_type": expectation.get("type"),
        "kwargs": expectation.get("kwargs", {}),
        "success": bool(payload.get("success", False)),
        "result": payload.get("result", {}),
        "exception_info": payload.get("exception_info", {}),
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the Great Expectations 1.x quality gate and freshness SLA."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        ExpectColumnValuesToNotBeNull(column="paper_id"),
        ExpectColumnValuesToNotBeNull(column="title"),
        ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        ExpectColumnValuesToBeUnique(column="paper_id"),
        ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    validation_results = [_serialize_validation(batch.validate(expectation)) for expectation in expectations]
    freshness = evaluate_freshness_sla(df, settings)
    success = all(item["success"] for item in validation_results) and freshness["is_fresh"] is True

    result: dict[str, Any] = {
        "success": success,
        "stage": report_name,
        "row_count": int(len(df)),
        "expectations": validation_results,
        "freshness": freshness,
    }
    write_json(_report_path(settings, report_name), result)
    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist a standalone freshness report."""
    report = evaluate_freshness_sla(df, settings)
    write_json(Path(report_path), report)
    return report
