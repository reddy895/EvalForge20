import asyncio
import os
import sys
from typing import Any, Dict, List

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.evalforge.schemas.dataset import DatasetCreate, TestCaseCreate
from src.evalforge.services.dataset_service import DatasetService
from src.evalforge.storage.database import close_db, get_session_factory, init_db

SEED_DATASETS: List[Dict[str, Any]] = [
    {
        "name": "Python Algorithmic Synthesis",
        "description": "Tests code synthesis for algorithmic functions: palindromes, two-sum, and recursion.",
        "tags": ["coding", "python", "algorithms"],
        "cases": [
            {
                "prompt": "Write a Python function named `is_palindrome(s: str) -> bool` that returns True if s is a palindrome.",
                "expected_output": "def is_palindrome(s: str) -> bool:\n    clean = ''.join(c.lower() for c in s if c.isalnum())\n    return clean == clean[::-1]",
                "tags": ["strings", "palindrome"],
                "evaluator_config": {
                    "required_keywords": ["def is_palindrome", "return"],
                    "prohibited_keywords": ["syntax error", "TODO"],
                },
            },
            {
                "prompt": "Write a Python function `two_sum(nums: list[int], target: int) -> list[int]` returning indices of two numbers adding up to target.",
                "expected_output": "def two_sum(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in seen:\n            return [seen[diff], i]\n        seen[n] = i\n    return []",
                "tags": ["arrays", "hashmap"],
                "evaluator_config": {
                    "required_keywords": ["def two_sum", "return"],
                },
            },
            {
                "prompt": "Write a Python recursive function `factorial(n: int) -> int`.",
                "expected_output": "def factorial(n: int) -> int:\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                "tags": ["recursion", "math"],
                "evaluator_config": {
                    "required_keywords": ["def factorial", "factorial(n - 1)"],
                },
            },
        ],
    },
    {
        "name": "Constrained JSON Schema Extraction",
        "description": "Verifies structured JSON output adhering to typed schemas without hallucination.",
        "tags": ["json", "structured_output", "extraction"],
        "cases": [
            {
                "prompt": "Extract person details from text: 'Dr. Jane Watson is a 38-year-old neurologist based in Edinburgh, UK.' Output JSON with name, age, specialty, location.",
                "expected_output": '{"name": "Dr. Jane Watson", "age": 38, "specialty": "neurologist", "location": "Edinburgh, UK"}',
                "tags": ["entity_extraction", "json"],
                "evaluator_config": {
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                            "specialty": {"type": "string"},
                            "location": {"type": "string"},
                        },
                        "required": ["name", "age", "specialty"],
                    }
                },
            },
            {
                "prompt": "Extract server status from log: 'Server node-42 reported CPU usage 87% and memory usage 64% at status OK.' Output JSON.",
                "expected_output": '{"node_id": "node-42", "cpu_percent": 87, "memory_percent": 64, "status": "OK"}',
                "tags": ["sysadmin", "json"],
                "evaluator_config": {
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "node_id": {"type": "string"},
                            "cpu_percent": {"type": "integer"},
                            "memory_percent": {"type": "integer"},
                            "status": {"type": "string"},
                        },
                        "required": ["node_id", "status"],
                    }
                },
            },
        ],
    },
    {
        "name": "Mathematical Word Logic",
        "description": "Multi-step arithmetic word problems requiring verified numerical deduction.",
        "tags": ["math", "reasoning", "logic"],
        "cases": [
            {
                "prompt": "A train travels at 60 km/h for 2.5 hours, then speeds up to 90 km/h for 1.5 hours. What is the total distance traveled in kilometers?",
                "expected_output": "285 kilometers. (60 * 2.5 = 150 km; 90 * 1.5 = 135 km; 150 + 135 = 285 km)",
                "tags": ["arithmetic", "distance"],
                "evaluator_config": {
                    "required_keywords": ["285"],
                },
            },
            {
                "prompt": "A bakery had 240 baguettes. They sold 75% in the morning and 15 baguettes in the afternoon. How many baguettes remain?",
                "expected_output": "45 baguettes. (240 * 0.75 = 180 sold in morning; 240 - 180 = 60; 60 - 15 = 45 remain)",
                "tags": ["percentages", "arithmetic"],
                "evaluator_config": {
                    "required_keywords": ["45"],
                },
            },
        ],
    },
    {
        "name": "Needle-in-a-Haystack Fact Recall",
        "description": "Evaluates precision retrieval inside dense context documents.",
        "tags": ["rag", "retrieval", "recall"],
        "cases": [
            {
                "prompt": "According to the system manual, what is the secret maintenance code for Vault 101?",
                "context": "Facility Security Protocols 2026. All gates operate under keycards. Vault 101 maintenance override code is 'BLUE-ORION-77'. Ensure doors remain locked during routine maintenance cycles.",
                "expected_output": "The secret maintenance code is BLUE-ORION-77.",
                "tags": ["retrieval", "precision"],
                "evaluator_config": {
                    "required_keywords": ["BLUE-ORION-77"],
                },
            }
        ],
    },
]


async def seed() -> None:
    """Populate default datasets and test cases."""
    print("Initializing database...")
    await init_db()

    session_factory = get_session_factory()
    async with session_factory() as session:
        service = DatasetService(session)

        for ds_def in SEED_DATASETS:
            # Check if dataset already exists
            existing = await service.repo.get_by_name(ds_def["name"])
            if existing:
                print(f"Dataset '{ds_def['name']}' already exists, skipping.")
                continue

            cases_create = [
                TestCaseCreate(
                    prompt=c["prompt"],
                    expected_output=c.get("expected_output"),
                    context=c.get("context"),
                    tags=c.get("tags", []),
                    evaluator_config=c.get("evaluator_config", {}),
                )
                for c in ds_def["cases"]
            ]

            ds_create = DatasetCreate(
                name=ds_def["name"],
                description=ds_def["description"],
                tags=ds_def["tags"],
                cases=cases_create,
            )

            created = await service.create_dataset(ds_create)
            print(f"Seeded dataset '{created.name}' with {len(cases_create)} test cases.")

        await session.commit()

    await close_db()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
