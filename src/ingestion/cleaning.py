from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from ingestion.crossref import PaperRecord


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [cleaned for value in values if (cleaned := _clean_text(value))]


def _normalize_date(value: Any) -> str:
    if value is None or value == "":
        return ""
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def _run_date_as_date(run_date: datetime) -> date:
    if isinstance(run_date, datetime):
        return run_date.date()
    return run_date


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw PaperRecord values into a deduplicated embedding dataframe."""
    run_day = _run_date_as_date(run_date)
    rows: list[dict[str, Any]] = []

    for record in records:
        paper_id = _clean_text(record.paper_id)
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        published = _normalize_date(record.published)
        if not paper_id or not title or not summary or not published:
            continue

        authors = _clean_list(record.authors)
        categories = _clean_list(record.categories)
        updated = _normalize_date(record.updated) or published
        authors_joined = "; ".join(authors)
        categories_joined = ", ".join(categories)
        age_days = (run_day - date.fromisoformat(published)).days

        text_for_embedding = "\n".join(
            [
                f"Title: {title}",
                f"Authors: {authors_joined}",
                f"Published: {published}",
                f"Categories: {categories_joined}",
                f"Summary: {summary}",
            ]
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": _clean_text(record.primary_category),
                "published": published,
                "updated": updated,
                "abs_url": _clean_text(record.abs_url),
                "pdf_url": _clean_text(record.pdf_url),
                "comment": _clean_text(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    columns = [
        "paper_id",
        "title",
        "summary",
        "authors",
        "categories",
        "primary_category",
        "published",
        "updated",
        "abs_url",
        "pdf_url",
        "comment",
        "authors_joined",
        "categories_joined",
        "summary_chars",
        "age_days",
        "text_for_embedding",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows, columns=columns)
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    return df.sort_values(["published", "paper_id"], kind="stable").reset_index(drop=True)
