"""CSV per-case evaluation results exporter for EvalForge20."""

import csv
import io
import json
from pathlib import Path

from app.domain.results import CaseResult
from app.pricing.calculator import CostCalculator
from app.runner.config import EvaluationRunRecord
from app.security import validate_safe_path


def generate_csv_report(
    record: EvaluationRunRecord,
    case_results: list[CaseResult],
    redact_inputs: bool = False,
    redact_outputs: bool = False,
) -> str:
    """Generate a tabular CSV export of per-case evaluation results with metric scores and costs."""
    cost_calc = CostCalculator()

    # Discover all distinct metric IDs across case results
    metric_ids = sorted({m.metric_id for c in case_results for m in c.metrics})

    base_headers = [
        "case_id",
        "run_id",
        "model_identifier",
        "input",
        "expected_output",
        "actual_output",
        "passed",
        "latency_ms",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost_usd",
        "error_category",
        "error_message",
    ]

    metric_headers: list[str] = []
    for m_id in metric_ids:
        metric_headers.append(f"{m_id}_score")
        metric_headers.append(f"{m_id}_passed")

    all_headers = base_headers + metric_headers

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(all_headers)

    provider = record.config.target.provider_name
    model_id = record.config.target.model_identifier

    for c in case_results:
        # Format complex payload types to string with optional redaction
        if redact_inputs:
            inp_str = "[REDACTED_PROMPT]"
        else:
            inp_str = (
                json.dumps(c.input, ensure_ascii=False)
                if isinstance(c.input, (dict, list))
                else str(c.input or "")
            )

        exp_str = (
            json.dumps(c.expected_output, ensure_ascii=False)
            if isinstance(c.expected_output, (dict, list))
            else str(c.expected_output or "")
        )

        if redact_outputs:
            act_str = "[REDACTED_OUTPUT]"
        else:
            act_str = (
                json.dumps(c.actual_output, ensure_ascii=False)
                if isinstance(c.actual_output, (dict, list))
                else str(c.actual_output or "")
            )

        usage = c.token_usage or {}
        p_tokens = usage.get("prompt_tokens", "")
        c_tokens = usage.get("completion_tokens", "")
        tot_tokens = usage.get("total_tokens", "")

        case_cost = cost_calc.calculate_case_cost(c, provider=provider, model_identifier=model_id)
        cost_str = (
            f"{case_cost.total_estimated_cost_usd:.6f}"
            if case_cost.is_cost_known and case_cost.total_estimated_cost_usd is not None
            else ""
        )

        # Map metric values by metric_id
        metric_map = {m.metric_id: m for m in c.metrics}

        row = [
            c.case_id,
            c.run_id,
            model_id,
            inp_str,
            exp_str,
            act_str,
            c.passed,
            round(c.latency_ms, 2) if c.latency_ms is not None else "",
            p_tokens,
            c_tokens,
            tot_tokens,
            cost_str,
            c.error_category or "",
            c.error_message or "",
        ]

        for m_id in metric_ids:
            if m_id in metric_map:
                m_res = metric_map[m_id]
                score_str = f"{m_res.score:.4f}" if m_res.score is not None else ""
                row.append(score_str)
                row.append(m_res.passed if m_res.passed is not None else "")
            else:
                row.append("")
                row.append("")

        writer.writerow(row)

    return output.getvalue()


def export_csv_report_to_file(path: Path | str, csv_content: str) -> Path:
    """Write CSV report string to file on disk."""
    dest = validate_safe_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
    return dest
