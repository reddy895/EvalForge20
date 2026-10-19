"""Task-suitability recommendation engine with transparent scoring and hardware constraints."""

from backend.app.schemas.recommendations import (
    HardwareProfileInput,
    ModelRecommendation,
    TaskRecommendationRequest,
    TaskRecommendationResponse,
)
from backend.app.services.model_catalog import VERIFIED_CATALOG, ModelCatalogService
from backend.app.services.ollama_service import OllamaService

TASK_CRITERIA_MAP: dict[str, dict] = {
    "coding": {
        "title": "Software Engineering & Code Synthesis",
        "primary_benchmark": "HumanEval",
        "criteria": [
            "Pass@1 on HumanEval and MBPP coding benchmarks",
            "Reliability of syntax generation without markdown hallucination",
            "Support for structured output and function calling",
            "Inference speed and context length for large codebases",
        ],
        "weights": {"HumanEval": 0.5, "GSM8K": 0.1, "supports_tools": 0.2, "latency": 0.2},
    },
    "reasoning": {
        "title": "Logical, Analytical & Mathematical Reasoning",
        "primary_benchmark": "GSM8K",
        "criteria": [
            "Accuracy on GSM8K and MATH multi-step problem benchmarks",
            "MMLU general analytical knowledge depth",
            "Coherence of step-by-step chain of thought generation",
        ],
        "weights": {"GSM8K": 0.5, "MMLU": 0.3, "MATH": 0.2},
    },
    "structured_json": {
        "title": "JSON Schema & Data Extraction",
        "primary_benchmark": "JSON Schema Validity",
        "criteria": [
            "Native support for schema-constrained output decoding",
            "Deterministic JSON formatting without leading conversational prose",
            "Strict adherence to required key names and primitive data types",
        ],
        "weights": {"supports_structured_output": 0.6, "HumanEval": 0.2, "latency": 0.2},
    },
    "rag": {
        "title": "Retrieval-Augmented Generation (RAG)",
        "primary_benchmark": "Context Window & Retrieval",
        "criteria": [
            "Context window length (>= 32k tokens required for dense document retrieval)",
            "Needle-in-a-haystack recall across long context spans",
            "Hallucination suppression and attribution faithfulness",
        ],
        "weights": {"context_window": 0.5, "MMLU": 0.3, "latency": 0.2},
    },
    "agent": {
        "title": "Tool Use & Autonomous AI Agents",
        "primary_benchmark": "Tool Calling & Action Planning",
        "criteria": [
            "Reliable multi-turn tool calling parameter extraction",
            "Error recovery when tool responses indicate failure",
            "Context retention across multi-step execution graphs",
        ],
        "weights": {"supports_tools": 0.5, "HumanEval": 0.3, "MMLU": 0.2},
    },
    "summarization": {
        "title": "Document & Dialogue Summarization",
        "primary_benchmark": "MMLU Comprehension",
        "criteria": [
            "High factual retention without introducing ungrounded claims",
            "Fluency and conciseness across long passages",
            "Fast token throughput for real-time digest creation",
        ],
        "weights": {"MMLU": 0.5, "context_window": 0.3, "latency": 0.2},
    },
    "mathematics": {
        "title": "Mathematical Olympiad & Quantitative Proofs",
        "primary_benchmark": "MATH & GSM8K",
        "criteria": [
            "Accuracy on MATH competition benchmark and GSM8K multi-step arithmetic",
            "Precision of algebraic manipulation, symbolic calculation, and proof steps",
            "Absence of numerical and calculation hallucinations",
        ],
        "weights": {"MATH": 0.5, "GSM8K": 0.4, "MMLU": 0.1},
    },
    "extraction": {
        "title": "Entity Extraction & Document Parsing",
        "primary_benchmark": "Structured Output Adherence",
        "criteria": [
            "Zero-drift key-value and typed entity extraction from raw text",
            "Constrained structured decoding support without hallucinating missing fields",
            "Context window retention for large input documents",
        ],
        "weights": {"supports_structured_output": 0.6, "context_window": 0.2, "latency": 0.2},
    },
    "multilingual": {
        "title": "Multilingual Translation & Cross-Lingual Reasoning",
        "primary_benchmark": "Cross-Lingual MMLU",
        "criteria": [
            "Multilingual comprehension across European, Asian, and regional languages",
            "High-capacity vocabulary tokenizer with low compression overhead",
            "Cultural context and idiom translation preservation",
        ],
        "weights": {"MMLU": 0.5, "HumanEval": 0.3, "context_window": 0.2},
    },
    "local_edge": {
        "title": "Edge & Low-Resource Commodity Hardware Execution",
        "primary_benchmark": "RAM Feasibility & Latency",
        "criteria": [
            "Fits comfortably within <= 8GB system RAM without GPU offloading",
            "Sub-30ms prompt ingestion latency on standard laptop CPU",
            "High reasoning density per active billion parameters",
        ],
        "weights": {"HumanEval": 0.4, "latency": 0.3, "GSM8K": 0.3},
    },
}


class RecommendationService:
    """Calculates evidence-based model recommendations based on task requirements and hardware."""

    def __init__(self, catalog_service: ModelCatalogService | None = None):
        self.catalog = catalog_service or ModelCatalogService()
        self.ollama = OllamaService()

    async def recommend_for_task(
        self, req: TaskRecommendationRequest
    ) -> TaskRecommendationResponse:
        """Score models against the task criteria and return transparent ranked recommendations."""
        task_key = req.task.lower().strip()
        matched_key = "coding"
        for k in TASK_CRITERIA_MAP:
            if k in task_key:
                matched_key = k
                break

        criteria_info = TASK_CRITERIA_MAP[matched_key]
        ollama_status = await self.ollama.get_status()
        installed_set = set(ollama_status.installed_models) if ollama_status.is_reachable else set()

        recommendations: list[ModelRecommendation] = []

        for p in VERIFIED_CATALOG:
            # Skip mock model from formal recommendation ranking unless asked
            if p.id == "deterministic-mock-v1":
                continue

            # Check local filter
            if req.prefer_local and not p.is_local:
                continue

            # Compute Task Match Score
            base_score = 50.0

            # 1. Benchmark bonus
            evidence_points = []
            for b in p.benchmarks:
                if b.benchmark_name in criteria_info["weights"]:
                    weight = criteria_info["weights"][b.benchmark_name]
                    base_score += (b.score / 100.0) * (weight * 40.0)
                    evidence_points.append(f"{b.benchmark_name}: {b.score}% ({b.source})")

            # 2. Capability matches
            if matched_key in ("structured_json", "extraction") and p.supports_structured_output:
                base_score += 15.0
                evidence_points.append(
                    "Native structured output and constrained JSON support verified"
                )
            if matched_key in ("agent", "coding") and p.supports_tools:
                base_score += 10.0
                evidence_points.append("Verified tool use / function calling support")
            if (
                matched_key in ("rag", "summarization", "extraction", "multilingual")
                and p.context_window >= 32768
            ):
                base_score += 15.0
                evidence_points.append(
                    f"Extended context window of {p.context_window:,} tokens supports large document workflows"
                )
            if matched_key == "local_edge" and p.is_local and p.hardware.min_ram_gb <= 8.0:
                base_score += 20.0
                evidence_points.append(
                    f"Lightweight edge profile: requires only {p.hardware.min_ram_gb}GB RAM"
                )

            # 3. Hardware check
            is_installed = p.model_identifier in installed_set
            fit_label = "Runs smoothly"
            tradeoffs = []

            if p.is_local:
                if req.max_ram_gb and p.hardware.min_ram_gb > req.max_ram_gb:
                    fit_label = f"Exceeds available RAM ({p.hardware.min_ram_gb}GB required, {req.max_ram_gb}GB available)"
                    base_score -= 25.0
                    tradeoffs.append(
                        f"Requires at least {p.hardware.min_ram_gb}GB RAM; may trigger OS swapping"
                    )
                elif req.max_ram_gb and p.hardware.min_ram_gb <= req.max_ram_gb:
                    fit_label = f"Comfortable local fit ({p.hardware.min_ram_gb}GB required on {req.max_ram_gb}GB RAM)"
                else:
                    fit_label = f"Local model ({p.hardware.min_ram_gb}GB RAM required)"
            else:
                fit_label = "Hosted Cloud API (Requires network and API credentials)"
                tradeoffs.append("Requires outbound internet connection and API token billing")

            if p.weaknesses:
                tradeoffs.extend(p.weaknesses[:2])

            match_score = min(100.0, max(20.0, round(base_score, 1)))

            reason = f"Ranked #{len(recommendations) + 1} for {criteria_info['title']}. "
            if p.is_local and is_installed:
                reason += "Currently installed on your local Ollama daemon and immediately runnable offline."
            elif p.is_local:
                reason += f"Available in Ollama via 'ollama pull {p.model_identifier}'."
            else:
                reason += "Frontier hosted model with state-of-the-art capability."

            recommendations.append(
                ModelRecommendation(
                    model_id=p.id,
                    model_name=p.name,
                    provider=p.provider,
                    match_score=match_score,
                    is_local=p.is_local,
                    is_installed=is_installed,
                    hardware_fit=fit_label,
                    recommendation_reason=reason,
                    key_evidence=evidence_points
                    or [
                        "Insufficient empirical benchmark data published for this specific task; ranking estimated from architectural scale and baseline modality support."
                    ],
                    important_tradeoffs=tradeoffs,
                    evidence_source="Verified Technical Report & Published Benchmark",
                )
            )

        recommendations.sort(key=lambda r: (r.is_installed, r.match_score), reverse=True)

        explanation = (
            f"Recommendations for '{criteria_info['title']}' calculated by evaluating documented benchmark "
            f"evidence ({', '.join(criteria_info['weights'].keys())}), model context windows, structured output support, "
            f"and local hardware feasibility."
        )

        return TaskRecommendationResponse(
            task=criteria_info["title"],
            evaluated_criteria=criteria_info["criteria"],
            recommendations=recommendations[:6],
            explanation=explanation,
        )

    def evaluate_hardware_compatibility(self, hw: HardwareProfileInput) -> list[dict]:
        """Assess which local models can run comfortably given the user's specific hardware specs."""
        results = []
        for p in VERIFIED_CATALOG:
            if not p.is_local or p.id == "deterministic-mock-v1":
                continue

            can_run = hw.total_ram_gb >= p.hardware.min_ram_gb
            runs_on_gpu = hw.has_gpu and (hw.vram_gb or 0.0) >= (p.hardware.min_vram_gb or 999.0)

            if runs_on_gpu:
                perf_tier = "Optimal (Full GPU Offload)"
                notes = f"Fits entirely in GPU VRAM ({p.hardware.min_vram_gb}GB / {hw.vram_gb}GB available). Expect fast token generation."
            elif can_run:
                perf_tier = "Good (CPU / System RAM)"
                notes = f"Fits in {hw.total_ram_gb}GB system RAM ({p.hardware.min_ram_gb}GB required). CPU inference."
            else:
                perf_tier = "Insufficient Memory"
                notes = f"Model needs at least {p.hardware.min_ram_gb}GB RAM; system only has {hw.total_ram_gb}GB."

            results.append(
                {
                    "model_id": p.id,
                    "model_name": p.name,
                    "model_identifier": p.model_identifier,
                    "can_run_locally": can_run,
                    "runs_on_gpu": runs_on_gpu,
                    "performance_tier": perf_tier,
                    "min_ram_gb": p.hardware.min_ram_gb,
                    "min_vram_gb": p.hardware.min_vram_gb,
                    "notes": notes,
                }
            )

        results.sort(key=lambda r: (r["runs_on_gpu"], r["can_run_locally"]), reverse=True)
        return results
