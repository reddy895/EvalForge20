"""Dataset loader supporting CSV, JSON, and JSONL formats with column mapping."""

import csv
import io
import json
from typing import Any

from pydantic import BaseModel, Field

INPUT_ALIASES = ["input", "prompt", "question", "query", "text", "instruction", "problem"]
REFERENCE_ALIASES = ["expected_output", "expected_answer", "reference", "target", "ground_truth", "answer", "solution"]
CONTEXT_ALIASES = ["context", "documents", "retrieved_context", "passages"]


class ParsedDatasetRecord(BaseModel):
    input: str
    expected_output: str | None = None
    context: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetLoader:
    """Loads and standardizes dataset records from CSV, JSON, and JSONL streams or strings."""

    @classmethod
    def load_from_text(cls, content: str, filename_or_ext: str = "json") -> list[ParsedDatasetRecord]:
        ext = filename_or_ext.lower().split(".")[-1]
        clean_content = content.strip()

        if ext in ("csv", "tsv"):
            delimiter = "\t" if ext == "tsv" else ","
            return cls.load_csv(clean_content, delimiter=delimiter)
        elif ext in ("jsonl", "ndjson"):
            return cls.load_jsonl(clean_content)
        else:
            # Try JSON first; if it looks like JSONL, fall back
            if clean_content.startswith("[") or clean_content.startswith("{"):
                try:
                    return cls.load_json(clean_content)
                except Exception:
                    return cls.load_jsonl(clean_content)
            return cls.load_jsonl(clean_content)

    @classmethod
    def load_csv(cls, csv_content: str, delimiter: str = ",") -> list[ParsedDatasetRecord]:
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        records: list[ParsedDatasetRecord] = []

        for row in reader:
            normalized_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            inp = cls._find_key_value(normalized_row, INPUT_ALIASES)
            if not inp:
                continue

            ref = cls._find_key_value(normalized_row, REFERENCE_ALIASES)
            ctx = cls._find_key_value(normalized_row, CONTEXT_ALIASES)

            # Metadata is remaining unused fields
            meta = {k: v for k, v in normalized_row.items() if k not in INPUT_ALIASES + REFERENCE_ALIASES + CONTEXT_ALIASES}

            records.append(ParsedDatasetRecord(
                input=inp,
                expected_output=ref,
                context=ctx,
                metadata=meta,
            ))

        return records

    @classmethod
    def load_json(cls, json_content: str) -> list[ParsedDatasetRecord]:
        data = json.loads(json_content)
        items = data
        if isinstance(data, dict):
            for k in ("test_cases", "cases", "data", "records", "items", "dataset"):
                if k in data and isinstance(data[k], list):
                    items = data[k]
                    break
            if items == data:
                items = [data]

        records: list[ParsedDatasetRecord] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            norm = {k.lower(): v for k, v in item.items()}
            inp = cls._find_key_value(norm, INPUT_ALIASES)
            if not inp:
                continue
            ref = cls._find_key_value(norm, REFERENCE_ALIASES)
            ctx = cls._find_key_value(norm, CONTEXT_ALIASES)
            meta = {k: v for k, v in norm.items() if k not in INPUT_ALIASES + REFERENCE_ALIASES + CONTEXT_ALIASES}
            records.append(ParsedDatasetRecord(
                input=str(inp),
                expected_output=str(ref) if ref is not None else None,
                context=str(ctx) if ctx is not None else None,
                metadata=meta,
            ))
        return records

    @classmethod
    def load_jsonl(cls, jsonl_content: str) -> list[ParsedDatasetRecord]:
        records: list[ParsedDatasetRecord] = []
        for line in jsonl_content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    norm = {k.lower(): v for k, v in item.items()}
                    inp = cls._find_key_value(norm, INPUT_ALIASES)
                    if not inp:
                        continue
                    ref = cls._find_key_value(norm, REFERENCE_ALIASES)
                    ctx = cls._find_key_value(norm, CONTEXT_ALIASES)
                    meta = {k: v for k, v in norm.items() if k not in INPUT_ALIASES + REFERENCE_ALIASES + CONTEXT_ALIASES}
                    records.append(ParsedDatasetRecord(
                        input=str(inp),
                        expected_output=str(ref) if ref is not None else None,
                        context=str(ctx) if ctx is not None else None,
                        metadata=meta,
                    ))
            except Exception:
                continue
        return records

    @staticmethod
    def _find_key_value(data_dict: dict[str, Any], aliases: list[str]) -> Any | None:
        for alias in aliases:
            if alias in data_dict and data_dict[alias] not in (None, ""):
                return data_dict[alias]
        return None


__all__ = [
    "DatasetLoader",
    "ParsedDatasetRecord",
]
