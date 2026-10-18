"""Markdown evaluation report exporter for EvalForge20."""

from pathlib import Path

from app.domain.results import AggregateMetrics, CaseResult
from app.pricing.calculator import CostCalculator
from app.runner.config import EvaluationRunRecord
from app.security import validate_safe_path


def generate_markdown_report(
    record: EvaluationRunRecord,
    case_results: list[CaseResult],
    aggregates: AggregateMetrics,
    redact_inputs: bool = False,
    redact_outputs: bool = False,
) -> str:
    """Generate a clean, structured Markdown evaluation report for human consumption."""
    duration_s = (
        round((record.completed_at - record.started_at).total_seconds(), 2)
        if record.started_at and record.completed_at
        else "N/A"
    )
    pass_pct = f"{aggregates.pass_rate * 100:.1f}%" if aggregates.pass_rate is not None else "N/A"
    mean_lat = (
        f"{aggregates.mean_latency_ms:.1f} ms" if aggregates.mean_latency_ms is not None else "N/A"
    )
    p95_lat = (
        f"{aggregates.p95_latency_ms:.1f} ms" if aggregates.p95_latency_ms is not None else "N/A"
    )

    cost_calc = CostCalculator()
    run_cost = cost_calc.calculate_run_cost(
        case_results,
        aggregates,
        provider=record.config.target.provider_name,
        model_identifier=record.config.target.model_identifier,
    )

    cost_str = (
        f"${run_cost.total_estimated_cost_usd:.6f}"
        if run_cost.is_cost_known and run_cost.total_estimated_cost_usd is not None
        else "$0.00 (Local / Unbilled)"
    )

    lines: list[str] = [
        f"# Evaluation Report: {record.name}",
        "",
        f"**Run ID:** `{record.run_id}`  ",
        f"**Status:** `{record.status.value}`  ",
        f"**Target Model:** `{record.config.target.model_identifier}`  ",
        f"**Provider:** `{record.config.target.provider_name}`  ",
        f"**Dataset Hash:** `{record.config.dataset_version_hash or 'N/A'}`  ",
        f"**Duration:** {duration_s} seconds  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Total Cases** | {record.total_cases} |",
        f"| **Completed Cases** | {record.completed_cases} |",
        f"| **Failed Cases** | {record.failed_cases} |",
        f"| **Overall Pass Rate** | {pass_pct} |",
        f"| **Mean Latency** | {mean_lat} |",
        f"| **P95 Latency** | {p95_lat} |",
        f"| **Total Tokens** | {aggregates.total_tokens if aggregates.total_tokens is not None else 'Unmeasured'} |",
        f"| **Estimated Cost** | {cost_str} |",
        "",
        "---",
        "",
        "## 2. Metric Performance Breakdown",
        "",
        "| Metric | Average Score | Pass Rate |",
        "|---|---|---|",
    ]

    all_metric_ids = sorted(
        set(aggregates.metric_averages.keys()) | set(aggregates.metric_pass_rates.keys())
    )
    if all_metric_ids:
        for m_id in all_metric_ids:
            avg_score = aggregates.metric_averages.get(m_id)
            score_str = f"{avg_score:.4f}" if avg_score is not None else "N/A"
            m_pass = aggregates.metric_pass_rates.get(m_id)
            pass_str = f"{m_pass * 100:.1f}%" if m_pass is not None else "N/A"
            title = m_id.replace("_", " ").title()
            lines.append(f"| **{title}** (`{m_id}`) | {score_str} | {pass_str} |")
    else:
        lines.append("| *No individual metrics recorded* | N/A | N/A |")

    # Category performance if present
    if aggregates.category_performance:
        lines.extend(
            [
                "",
                "### Category Performance",
                "",
                "| Category | Pass Rate | Cases |",
                "|---|---|---|",
            ]
        )
        for cat, stats in sorted(aggregates.category_performance.items()):
            c_rate = stats.get("pass_rate")
            rate_str = f"{c_rate * 100:.1f}%" if c_rate is not None else "N/A"
            c_count = int(stats.get("count", 0))
            lines.append(f"| **{cat}** | {rate_str} | {c_count} |")

    # Pricing & Economics section
    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Economics & Resource Projections",
            "",
        ]
    )
    if (
        record.config.target.provider_name.lower() in ("ollama", "local")
        or run_cost.cloud_cost_usd == 0.0
    ):
        lines.extend(
            [
                f"- **Inference Infrastructure:** Fully local evaluation using {record.config.target.provider_name.title()} and Python execution.",
                "- **External SaaS / API Costs:** $0.00 (Zero cloud API fees incurred).",
                f"- **Measured Runtime:** {duration_s}s end-to-end execution time.",
            ]
        )
    if (
        run_cost.is_cost_known
        and run_cost.total_estimated_cost_usd is not None
        and run_cost.total_estimated_cost_usd > 0
    ):
        lines.extend(
            [
                f"- **Total Measured Run Cost:** ${run_cost.total_estimated_cost_usd:.6f}",
                f"- **Cost per Successful Case:** ${run_cost.cost_per_successful_case_usd:.6f}"
                if run_cost.cost_per_successful_case_usd is not None
                else "- **Cost per Successful Case:** N/A",
                f"- **Projected Cost / 1k Tasks:** ${run_cost.cost_per_1k_tasks_usd:.4f}"
                if run_cost.cost_per_1k_tasks_usd is not None
                else "- **Projected Cost / 1k Tasks:** N/A",
                f"- **Pricing Source / Assumptions:** {run_cost.assumptions or run_cost.pricing_source or 'Standard API rates'}",
            ]
        )
    elif not (
        record.config.target.provider_name.lower() in ("ollama", "local")
        or run_cost.cloud_cost_usd == 0.0
    ):
        lines.extend(
            [
                f"- **Inference Infrastructure:** Private endpoint ({record.config.target.provider_name}).",
                f"- **Measured Runtime:** {duration_s}s end-to-end execution time.",
            ]
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Case Results Sample",
            "",
            "| Case ID | Input Preview | Latency | Passed | Primary Metric |",
            "|---|---|---|---|---|",
        ]
    )

    sample_cases = case_results[:20]
    for c in sample_cases:
        if redact_inputs:
            inp_preview = "[REDACTED_PROMPT]"
        else:
            inp_str = str(c.input).replace("\n", " ")
            inp_preview = (inp_str[:40] + "...") if len(inp_str) > 40 else inp_str

        lat_str = f"{c.latency_ms:.1f}ms" if c.latency_ms is not None else "N/A"
        pass_badge = "✅ Pass" if c.passed else "❌ Fail"

        # Find primary metric score
        primary_metric = "N/A"
        if c.metrics:
            first_m = c.metrics[0]
            val = f"{first_m.score:.2f}" if first_m.score is not None else str(first_m.passed)
            primary_metric = f"{first_m.metric_id}: {val}"

        lines.append(
            f"| `{c.case_id}` | {inp_preview} | {lat_str} | {pass_badge} | {primary_metric} |"
        )

    if len(case_results) > 20:
        lines.append(f"\n*... and {len(case_results) - 20} more test cases.*")

    lines.append("\n\n---\n*Report generated by EvalForge20 Local-First Evaluation Platform.*")
    return "\n".join(lines)


def export_markdown_report_to_file(path: Path | str, markdown_content: str) -> Path:
    """Write markdown report string to file on disk."""
    dest = validate_safe_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        f.write(markdown_content)
    return dest
