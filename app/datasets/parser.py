"""JSONL dataset parsing and serialization utilities."""

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any


class JSONLParseError(Exception):
    """Raised when a specific line in a JSONL file cannot be parsed as valid JSON."""

    def __init__(self, line_number: int, raw_line: str, error_detail: str):
        super().__init__(f"Line {line_number}: Invalid JSON - {error_detail}")
        self.line_number = line_number
        self.raw_line = raw_line
        self.error_detail = error_detail


def iter_jsonl_lines(source: str | Path) -> Generator[tuple[int, dict[str, Any]], None, None]:
    """Iterate over non-empty lines in a JSONL file or string, yielding (line_number, parsed_dict).

    Raises:
        FileNotFoundError: If source is a Path that does not exist.
        JSONLParseError: If any non-empty line fails JSON decoding.
    """
    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"Dataset file not found: {source}")
        lines = source.read_text(encoding="utf-8").splitlines()
    elif "\n" in source or "{" in source:
        lines = source.splitlines()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")
        lines = path.read_text(encoding="utf-8").splitlines()

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        try:
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise JSONLParseError(
                    line_number=line_number,
                    raw_line=stripped,
                    error_detail=f"Expected JSON object, got {type(payload).__name__}",
                )
            yield line_number, payload
        except json.JSONDecodeError as exc:
            raise JSONLParseError(
                line_number=line_number,
                raw_line=stripped,
                error_detail=str(exc),
            ) from exc


def write_jsonl(dest: Path | str, items: list[dict[str, Any]]) -> None:
    """Serialize a list of dictionaries into a JSONL file."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
