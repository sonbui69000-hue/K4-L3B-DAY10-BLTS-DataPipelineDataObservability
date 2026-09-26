from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def _paper_ids(frame: pd.DataFrame) -> list[str]:
    return [str(value) for value in frame.get("paper_id", pd.Series(dtype=str)).tolist()]


def _detail(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    details = []
    for _, row in frame.iterrows():
        item = {"paper_id": str(row["paper_id"])}
        for column in columns:
            value = row.get(column)
            item[column] = None if pd.isna(value) else str(value)
        details.append(item)
    return details


def _rebuild_embedding_fields(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["title"] = result["title"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    result["summary"] = result["summary"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    result["authors_joined"] = result["authors_joined"].fillna("").astype(str)
    result["categories_joined"] = result["categories_joined"].fillna("").astype(str)
    result["published"] = pd.to_datetime(result["published"], errors="coerce").dt.strftime("%Y-%m-%d")
    run_day = datetime.now(UTC).date()
    published_dates = pd.to_datetime(result["published"], errors="coerce")
    result["age_days"] = (pd.Timestamp(run_day) - published_dates).dt.days
    result["summary_chars"] = result["summary"].str.len()
    result["text_for_embedding"] = (
        "Title: " + result["title"]
        + "\nAuthors: " + result["authors_joined"]
        + "\nPublished: " + result["published"].fillna("")
        + "\nCategories: " + result["categories_joined"]
        + "\nSummary: " + result["summary"]
    )
    return result.reset_index(drop=True)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Inject six deterministic data corruptions and write a detailed audit log."""
    if df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")
    required = {"paper_id", "title", "summary", "published", "text_for_embedding"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Clean dataframe is missing required columns: {sorted(missing)}")

    work = df.copy(deep=True).reset_index(drop=True)
    scenarios: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    ordered = work.assign(
        _published_sort=pd.to_datetime(work["published"], errors="coerce")
    ).sort_values(["_published_sort", "paper_id"], kind="stable")
    drop_count = max(1, int(len(work) * 0.20 + 0.999999))
    dropped = ordered.tail(drop_count)
    dropped_ids = _paper_ids(dropped)
    work = work.drop(index=dropped.index).reset_index(drop=True)
    scenarios.append(
        {
            "name": "drop_latest_records",
            "affected_rows": len(dropped),
            "affected_paper_ids": dropped_ids,
            "details": f"Dropped the {drop_count} newest records (20% rounded up).",
        }
    )

    if work.empty:
        raise ValueError("Dropping latest records removed every row.")

    blank_index = 0
    blank_before = work.loc[[blank_index], ["summary"]].copy()
    work.loc[blank_index, "summary"] = ""
    blank_after = work.loc[[blank_index], ["summary"]].copy()
    scenarios.append(
        {
            "name": "blank_summary",
            "affected_rows": 1,
            "affected_paper_ids": _paper_ids(work.loc[[blank_index]]),
            "details": _detail(blank_before.assign(paper_id=work.loc[blank_index, "paper_id"]), ["summary"]),
        }
    )
    changes.extend(
        [
            {
                "scenario": "blank_summary",
                "paper_id": str(work.loc[blank_index, "paper_id"]),
                "field": "summary",
                "before": str(blank_before.iloc[0]["summary"]),
                "after": str(blank_after.iloc[0]["summary"]),
            }
        ]
    )

    noise_index = min(1, len(work) - 1)
    noise_before = str(work.loc[noise_index, "summary"])
    noise_value = f"{noise_before} [NOISE_### CORRUPTED_TEXT]"
    work.loc[noise_index, "summary"] = noise_value
    scenarios.append(
        {
            "name": "inject_noise",
            "affected_rows": 1,
            "affected_paper_ids": _paper_ids(work.loc[[noise_index]]),
            "details": "Appended deterministic garbage marker to the summary.",
        }
    )
    changes.append(
        {
            "scenario": "inject_noise",
            "paper_id": str(work.loc[noise_index, "paper_id"]),
            "field": "summary",
            "before": noise_before,
            "after": noise_value,
        }
    )

    title_index = min(2, len(work) - 1)
    title_before = str(work.loc[title_index, "title"])
    work.loc[title_index, "title"] = "BAD"
    scenarios.append(
        {
            "name": "truncate_title",
            "affected_rows": 1,
            "affected_paper_ids": _paper_ids(work.loc[[title_index]]),
            "details": "Truncated title to three characters, below the eight-character threshold.",
        }
    )
    changes.append(
        {
            "scenario": "truncate_title",
            "paper_id": str(work.loc[title_index, "paper_id"]),
            "field": "title",
            "before": title_before,
            "after": "BAD",
        }
    )

    stale_index = min(3, len(work) - 1)
    stale_before = str(work.loc[stale_index, "published"])
    stale_date = (datetime.now(UTC).date() - timedelta(days=365)).isoformat()
    work.loc[stale_index, "published"] = stale_date
    scenarios.append(
        {
            "name": "stale_date",
            "affected_rows": 1,
            "affected_paper_ids": _paper_ids(work.loc[[stale_index]]),
            "details": f"Changed published date to {stale_date} (365 days before the run date).",
        }
    )
    changes.append(
        {
            "scenario": "stale_date",
            "paper_id": str(work.loc[stale_index, "paper_id"]),
            "field": "published",
            "before": stale_before,
            "after": stale_date,
        }
    )

    duplicate_count = max(1, min(2, len(work)))
    duplicated = work.head(duplicate_count).copy()
    work = pd.concat([work, duplicated], ignore_index=True)
    duplicate_ids = _paper_ids(duplicated)
    scenarios.append(
        {
            "name": "duplicate_rows",
            "affected_rows": duplicate_count,
            "affected_paper_ids": duplicate_ids,
            "details": f"Appended {duplicate_count} duplicated rows.",
        }
    )
    changes.extend(
        {
            "scenario": "duplicate_rows",
            "paper_id": paper_id,
            "field": "row",
            "before": "original",
            "after": "duplicated",
        }
        for paper_id in duplicate_ids
    )

    corrupted = _rebuild_embedding_fields(work)
    log = {
        "input_rows": int(len(df)),
        "output_rows": int(len(corrupted)),
        "scenarios": scenarios,
        "changes": changes,
    }
    write_json(Path(output_log_path), log)
    return corrupted
