from __future__ import annotations

from dataclasses import asdict, dataclass
from html import unescape
import json
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def _date_from_parts(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts", [[]])
    parts = parts[0] if parts and isinstance(parts[0], list) else []
    if not parts:
        return ""
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def _date_from_item(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        date = _date_from_parts(value)
        if date:
            return date
        if isinstance(value, dict) and value.get("date-time"):
            return str(value["date-time"])[:10]
    return ""


def _as_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [cleaned for value in values if (cleaned := _clean_text(value))]


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list payload into normalized PaperRecord objects."""
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = _clean_text(item.get("DOI") or item.get("doi"))
        title_values = item.get("title") or []
        title = _clean_text(title_values[0] if isinstance(title_values, list) and title_values else title_values)
        if not paper_id or not title:
            continue

        authors: list[str] = []
        for author in item.get("author") or []:
            if isinstance(author, dict):
                given = _clean_text(author.get("given"))
                family = _clean_text(author.get("family"))
                name = " ".join(part for part in (given, family) if part)
            else:
                name = _clean_text(author)
            if name:
                authors.append(name)

        categories = _as_string_list(item.get("subject") or item.get("categories"))
        published = _date_from_item(item, "published-print", "published-online", "published", "issued", "created")
        updated = _date_from_item(item, "updated", "created") or published
        url = _clean_text(item.get("URL") or item.get("url"))
        pdf_url = _clean_text(item.get("link", [{}])[0].get("URL")) if item.get("link") else url

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_clean_text(item.get("abstract") or item.get("summary")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=pdf_url,
                comment=_clean_text(item.get("comment")) or f"Crossref record {paper_id}",
            )
        )

    return records


def _load_snapshot_payload(settings: Settings) -> dict:
    snapshot_path = settings.paths.raw_api_response
    if not snapshot_path.exists():
        raise RuntimeError(f"Crossref unavailable and snapshot is missing: {snapshot_path}")
    payload = read_json(snapshot_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Crossref snapshot must contain a JSON object: {snapshot_path}")
    return payload


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref data, preserve raw artifacts, and fall back to the local snapshot."""
    payload: dict | None = None
    should_fetch = settings.refresh_source or not settings.paths.raw_api_response.exists()

    if should_fetch:
        endpoint = "https://api.crossref.org/works"
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {"User-Agent": "BLTS-Day10-DataObservability/0.1 (mailto:student@example.com)"}

        for attempt in range(3):
            try:
                response = requests.get(endpoint, params=params, headers=headers, timeout=20)
                if response.status_code == 200:
                    candidate = response.json()
                    if parse_crossref_payload(candidate):
                        payload = candidate
                        write_json(settings.paths.raw_api_response, payload)
                        break
                elif response.status_code not in {429, 500, 502, 503, 504}:
                    response.raise_for_status()
            except (OSError, requests.RequestException, ValueError):
                pass
            if attempt < 2:
                time.sleep(2**attempt)

    if payload is None:
        payload = _load_snapshot_payload(settings)

    records = parse_crossref_payload(payload)
    if not records:
        raise ValueError("Crossref payload contained no valid records.")

    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load normalized PaperRecord objects from a raw records JSON artifact."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Raw records must contain a JSON list: {path}")

    records: list[PaperRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        records.append(PaperRecord(**item))
    return records
