"""Standard versioned scoring rubrics for LLM-as-Judge evaluations."""

from app.evaluators.llm_judge.models import JudgeRubric

ANSWER_RELEVANCE_RUBRIC = JudgeRubric(
    rubric_id="answer_relevance",
    name="Answer Relevance Rubric",
    version="1.0.0",
    criteria="Evaluate how directly and helpfully the response addresses the prompt without extraneous tangents.",
    scale_min=1,
    scale_max=5,
    pass_threshold=3.0,
    score_definitions={
        1: "Completely irrelevant or unresponsive to the prompt.",
        2: "Tangentially related, but fails to answer the main question.",
        3: "Partially answers the question but misses important aspects or constraints.",
        4: "Mostly relevant and addresses the prompt directly with minor extraneous detail.",
        5: "Perfectly relevant, focused, concise, and complete answer.",
    },
)

FACTUAL_CORRECTNESS_RUBRIC = JudgeRubric(
    rubric_id="factual_correctness",
    name="Factual Correctness Rubric",
    version="1.0.0",
    criteria="Evaluate whether the actual output is factually accurate and consistent with the reference answer.",
    scale_min=1,
    scale_max=5,
    pass_threshold=3.0,
    score_definitions={
        1: "Completely false, contradictory, or misleading compared to reference.",
        2: "Major factual errors that invalidate the core response.",
        3: "Partially correct; contains some accurate facts but also noticeable errors.",
        4: "Factually accurate with minor omissions that do not alter the conclusion.",
        5: "Completely accurate and fully consistent with reference ground truth.",
    },
)

CONTEXT_FAITHFULNESS_RUBRIC = JudgeRubric(
    rubric_id="context_faithfulness",
    name="Context Faithfulness / Groundedness Rubric",
    version="1.0.0",
    criteria="Evaluate whether all claims in the response are strictly supported by the supplied context.",
    scale_min=1,
    scale_max=5,
    pass_threshold=3.0,
    score_definitions={
        1: "Entirely hallucinated or contradicts the supplied context.",
        2: "Relies heavily on unsupported external claims with minimal context usage.",
        3: "Partially grounded in context, but introduces unverified assumptions.",
        4: "Almost entirely faithful; claims can be readily inferred from context.",
        5: "Strictly grounded; every factual claim is directly evidenced in the context.",
    },
)

EXPLANATION_QUALITY_RUBRIC = JudgeRubric(
    rubric_id="explanation_quality",
    name="Reasoning & Explanation Quality Rubric",
    version="1.0.0",
    criteria="Evaluate clarity, logical coherence, and step-by-step reasoning quality.",
    scale_min=1,
    scale_max=5,
    pass_threshold=3.0,
    score_definitions={
        1: "Incoherent, illogical, or confusing reasoning.",
        2: "Hard to follow with frequent non-sequiturs.",
        3: "Acceptable reasoning with some logical leaps or awkward flow.",
        4: "Clear and logical explanation with coherent reasoning steps.",
        5: "Exceptionally clear, structured, and compelling step-by-step explanation.",
    },
)

BUILTIN_RUBRICS: dict[str, JudgeRubric] = {
    "answer_relevance": ANSWER_RELEVANCE_RUBRIC,
    "factual_correctness": FACTUAL_CORRECTNESS_RUBRIC,
    "context_faithfulness": CONTEXT_FAITHFULNESS_RUBRIC,
    "explanation_quality": EXPLANATION_QUALITY_RUBRIC,
}
