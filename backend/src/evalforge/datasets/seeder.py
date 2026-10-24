"""Standard reproducible benchmark suite seeder for local evaluation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.core.logging import get_logger
from src.evalforge.storage.models.dataset import Dataset, TestCase

logger = get_logger("evalforge.datasets.seeder")

STANDARD_BENCHMARKS = [
    {
        "slug": "coding_basics",
        "name": "Python Algorithmic Synthesis",
        "description": "Tests function generation, string reversal, palindromes, and recursion.",
        "tags": ["coding", "python", "algorithms"],
        "cases": [
            {
                "id": "code-01",
                "prompt": "Write a Python function `reverse_string(s: str) -> str` that returns the reversed string. Do not include explanatory text, only the code.",
                "expected_output": "def reverse_string(s: str) -> str:\n    return s[::-1]",
                "evaluator_config": {
                    "assertion_type": "code_execution",
                    "keywords": ["reverse_string", "return"],
                },
            },
            {
                "id": "code-02",
                "prompt": "Write a Python function `is_palindrome(s: str) -> bool` ignoring spaces and case. Only return the code.",
                "expected_output": "def is_palindrome(s: str) -> bool:\n    clean = s.lower().replace(' ', '')\n    return clean == clean[::-1]",
                "evaluator_config": {
                    "assertion_type": "code_execution",
                    "keywords": ["is_palindrome"],
                },
            },
            {
                "id": "code-03",
                "prompt": "Write a Python function `fibonacci(n: int) -> int` returning the nth Fibonacci number. Only return the code.",
                "expected_output": "def fibonacci(n: int) -> int:\n    if n <= 0: return 0\n    if n == 1: return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b",
                "evaluator_config": {
                    "assertion_type": "code_execution",
                    "keywords": ["fibonacci"],
                },
            },
        ],
    },
    {
        "slug": "structured_json",
        "name": "Constrained JSON Schema Extraction",
        "description": "Verifies entity extraction adhering to strict typed schemas without hallucination.",
        "tags": ["structured_output", "json_schema", "extraction"],
        "cases": [
            {
                "id": "json-01",
                "prompt": "Extract person details into valid JSON with keys: name (str), age (int), role (str). Input: 'Alice is a 28-year-old software architect.' Return only JSON.",
                "expected_output": '{"name": "Alice", "age": 28, "role": "software architect"}',
                "evaluator_config": {
                    "assertion_type": "json_schema",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                            "role": {"type": "string"},
                        },
                        "required": ["name", "age", "role"],
                    },
                },
            },
            {
                "id": "json-02",
                "prompt": "Convert the status report to JSON: { service: str, healthy: bool, latency_ms: float }. Input: 'Auth service is operational with 42.5ms response time.' Return only JSON.",
                "expected_output": '{"service": "Auth", "healthy": true, "latency_ms": 42.5}',
                "evaluator_config": {
                    "assertion_type": "json_schema",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "service": {"type": "string"},
                            "healthy": {"type": "boolean"},
                            "latency_ms": {"type": "number"},
                        },
                        "required": ["service", "healthy", "latency_ms"],
                    },
                },
            },
            {
                "id": "json-03",
                "prompt": "Return a JSON array of the top 3 prime numbers strictly greater than 10. Return only JSON array.",
                "expected_output": "[11, 13, 17]",
                "evaluator_config": {
                    "assertion_type": "json_schema",
                    "json_schema": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
            },
        ],
    },
    {
        "slug": "reasoning_math",
        "name": "Mathematical Word Logic",
        "description": "Multi-step algebraic word problems requiring verified arithmetic deduction.",
        "tags": ["reasoning", "math", "word_problems"],
        "cases": [
            {
                "id": "math-01",
                "prompt": "A train travels 240 miles at 60 mph. How many minutes does the journey take? State the final number of minutes clearly.",
                "expected_output": "240",
                "evaluator_config": {
                    "assertion_type": "numeric_tolerance",
                    "keywords": ["240"],
                },
            },
            {
                "id": "math-02",
                "prompt": "If a rectangle has perimeter 48 and length 16, what is its area? State the final area.",
                "expected_output": "128",
                "evaluator_config": {
                    "assertion_type": "numeric_tolerance",
                    "keywords": ["128"],
                },
            },
            {
                "id": "math-03",
                "prompt": "Compute the value of 25 * 14 - 85. State the resulting number.",
                "expected_output": "265",
                "evaluator_config": {
                    "assertion_type": "numeric_tolerance",
                    "keywords": ["265"],
                },
            },
        ],
    },
    {
        "slug": "rag_retrieval",
        "name": "Needle-in-a-Haystack Fact Recall",
        "description": "Evaluates precision factual retrieval inside dense contextual documents.",
        "tags": ["rag", "retrieval", "precision"],
        "cases": [
            {
                "id": "rag-01",
                "prompt": "Based on the provided passage, what was the internal secret moniker of Project Aether?\nPassage: In the summer of 2024, the lab initiated Project Aether under the internal secret moniker 'Blue-Horizon-9'. The project concluded in December.",
                "expected_output": "Blue-Horizon-9",
                "context": "Project Aether secret moniker: Blue-Horizon-9.",
                "evaluator_config": {
                    "assertion_type": "exact_match",
                    "keywords": ["Blue-Horizon-9"],
                },
            },
            {
                "id": "rag-02",
                "prompt": "According to the system incident log, which specific node experienced the healthcheck failure?\nLog: [2026-10-21 04:12:00 UTC] High load detected. Node eu-west-core-03 failed healthcheck. Primary failover routed to node us-east-core-01.",
                "expected_output": "eu-west-core-03",
                "context": "Node eu-west-core-03 failed healthcheck.",
                "evaluator_config": {
                    "assertion_type": "exact_match",
                    "keywords": ["eu-west-core-03"],
                },
            },
        ],
    },
]


async def seed_standard_datasets(session: AsyncSession) -> dict[str, str]:
    """Seed standard evaluation benchmark datasets if not already present. Returns slug to UUID map."""
    slug_to_id: dict[str, str] = {}

    for bench in STANDARD_BENCHMARKS:
        slug = bench["slug"]
        name = bench["name"]

        # Check if dataset already exists by name or slug
        existing = await session.execute(
            select(Dataset).where(
                (Dataset.name == name) | (Dataset.tags_json.like(f"%{slug}%"))
            )
        )
        ds = existing.scalar_one_or_none()

        if not ds:
            tags = list(bench["tags"])
            if slug not in tags:
                tags.append(slug)
            ds = Dataset(
                name=name,
                description=bench["description"],
                version=1,
            )
            ds.tags = tags
            session.add(ds)
            await session.flush()

            # Add test cases
            for tc in bench["cases"]:
                case_obj = TestCase(
                    dataset_id=ds.id,
                    prompt=tc["prompt"],
                    expected_output=tc.get("expected_output"),
                    context=tc.get("context"),
                )
                case_obj.tags = [slug, tc["evaluator_config"].get("assertion_type", "exact_match")]
                case_obj.evaluator_config = tc["evaluator_config"]
                case_obj.metadata_dict = {"case_id": tc["id"], "assertion_type": tc["evaluator_config"].get("assertion_type", "exact_match")}
                session.add(case_obj)

            await session.commit()
            logger.info("Seeded standard evaluation dataset '%s' with %d cases", name, len(bench["cases"]))

        slug_to_id[slug] = ds.id
        slug_to_id[name.lower()] = ds.id

    return slug_to_id
