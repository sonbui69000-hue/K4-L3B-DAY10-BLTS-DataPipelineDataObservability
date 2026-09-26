from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build and persist a deterministic ten-question benchmark set."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "published",
        "categories_joined",
    }
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Clean dataframe is missing required columns: {sorted(missing)}")

    documents = (
        df.drop_duplicates(subset=["paper_id"])
        .sort_values(["published", "paper_id"], kind="stable")
        .reset_index(drop=True)
    )
    if len(documents) < 10:
        raise ValueError(f"At least 10 unique papers are required; received {len(documents)}.")

    question_types = [
        "summary",
        "summary",
        "summary",
        "authors",
        "authors",
        "authors",
        "date",
        "date",
        "categories",
        "categories",
    ]
    questions: list[dict[str, Any]] = []

    for index, question_type in enumerate(question_types):
        row = documents.iloc[index]
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = str(row["authors_joined"])
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(row["published"])
        else:
            question = f"What categories describe the paper '{title}'?"
            ground_truth = str(row["categories_joined"])

        questions.append(
            {
                "id": f"eval_{index + 1:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    write_json(Path(output_path), questions)
    return questions
