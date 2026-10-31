import type { TestCaseResult } from '../types';

export interface BenchmarkTestCase {
  id: string;
  benchmark_id: string;
  prompt: string;
  expected_output: string;
  assertion_type: 'exact_match' | 'json_schema' | 'code_execution' | 'numeric_tolerance';
  simulated_response: string;
  simulated_latency_ms: number;
}

export const SAMPLE_TEST_CASES: Record<string, BenchmarkTestCase[]> = {
  coding_basics: [
    {
      id: 'code-01',
      benchmark_id: 'coding_basics',
      prompt: 'Write a Python function `reverse_string(s: str) -> str` that returns the reversed string.',
      expected_output: 'def reverse_string(s: str) -> str:\n    return s[::-1]',
      assertion_type: 'exact_match',
      simulated_response: 'def reverse_string(s: str) -> str:\n    return s[::-1]',
      simulated_latency_ms: 18.4,
    },
    {
      id: 'code-02',
      benchmark_id: 'coding_basics',
      prompt: 'Write a Python function `is_palindrome(s: str) -> bool` ignoring spaces and case.',
      expected_output: 'def is_palindrome(s: str) -> bool:\n    clean = s.lower().replace(" ", "")\n    return clean == clean[::-1]',
      assertion_type: 'code_execution',
      simulated_response: 'def is_palindrome(s: str) -> bool:\n    clean = s.lower().replace(" ", "")\n    return clean == clean[::-1]',
      simulated_latency_ms: 22.1,
    },
    {
      id: 'code-03',
      benchmark_id: 'coding_basics',
      prompt: 'Write a Python function `fibonacci(n: int) -> int` returning the nth Fibonacci number.',
      expected_output: 'def fibonacci(n: int) -> int:\n    if n <= 0: return 0\n    if n == 1: return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b',
      assertion_type: 'code_execution',
      simulated_response: 'def fibonacci(n: int) -> int:\n    if n <= 0: return 0\n    if n == 1: return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b',
      simulated_latency_ms: 25.8,
    },
  ],
  reasoning_math: [
    {
      id: 'math-01',
      benchmark_id: 'reasoning_math',
      prompt: 'A train travels 240 miles at 60 mph. How many minutes does the journey take?',
      expected_output: '240 minutes',
      assertion_type: 'numeric_tolerance',
      simulated_response: 'Time = Distance / Speed = 240 / 60 = 4 hours. 4 hours * 60 minutes/hour = 240 minutes.',
      simulated_latency_ms: 29.4,
    },
    {
      id: 'math-02',
      benchmark_id: 'reasoning_math',
      prompt: 'If a rectangle has perimeter 48 and length 16, what is its area?',
      expected_output: '128',
      assertion_type: 'numeric_tolerance',
      simulated_response: 'Perimeter = 2*(L + W) = 48. 16 + W = 24, so W = 8. Area = L * W = 16 * 8 = 128.',
      simulated_latency_ms: 31.2,
    },
    {
      id: 'math-03',
      benchmark_id: 'reasoning_math',
      prompt: 'Compute the value of 25 * 14 - 85.',
      expected_output: '265',
      assertion_type: 'numeric_tolerance',
      simulated_response: '25 * 14 = 350. 350 - 85 = 265.',
      simulated_latency_ms: 24.0,
    },
  ],
  structured_json: [
    {
      id: 'json-01',
      benchmark_id: 'structured_json',
      prompt: 'Extract the person details into valid JSON with keys: name (str), age (int), role (str). Input: "Alice is a 28-year-old software architect."',
      expected_output: '{"name": "Alice", "age": 28, "role": "software architect"}',
      assertion_type: 'json_schema',
      simulated_response: '{"name": "Alice", "age": 28, "role": "software architect"}',
      simulated_latency_ms: 19.8,
    },
    {
      id: 'json-02',
      benchmark_id: 'structured_json',
      prompt: 'Convert the status report to JSON schema: { service: str, healthy: bool, latency_ms: float }. Input: "Auth service is operational with 42.5ms response time."',
      expected_output: '{"service": "Auth", "healthy": true, "latency_ms": 42.5}',
      assertion_type: 'json_schema',
      simulated_response: '{"service": "Auth", "healthy": true, "latency_ms": 42.5}',
      simulated_latency_ms: 20.4,
    },
    {
      id: 'json-03',
      benchmark_id: 'structured_json',
      prompt: 'Return a JSON array of the top 3 prime numbers above 10.',
      expected_output: '[11, 13, 17]',
      assertion_type: 'json_schema',
      simulated_response: '[11, 13, 17]',
      simulated_latency_ms: 17.6,
    },
  ],
  rag_retrieval: [
    {
      id: 'rag-01',
      benchmark_id: 'rag_retrieval',
      prompt: 'Context: "The Artemis IV mission is scheduled to launch in 2028 and will deliver the I-Hab module to Lunar Gateway." Question: Which module will Artemis IV deliver to Lunar Gateway?',
      expected_output: 'I-Hab module',
      assertion_type: 'exact_match',
      simulated_response: 'Artemis IV will deliver the I-Hab module.',
      simulated_latency_ms: 26.5,
    },
    {
      id: 'rag-02',
      benchmark_id: 'rag_retrieval',
      prompt: 'Context: "Protocol version 3.4 requires TLS 1.3 with AES-256-GCM cipher suite." Question: What minimum TLS version is required?',
      expected_output: 'TLS 1.3',
      assertion_type: 'exact_match',
      simulated_response: 'TLS 1.3 is required.',
      simulated_latency_ms: 21.0,
    },
  ],
};

export function simulateEvaluationRun(
  modelId: string,
  modelName: string,
  benchmarkId: string,
  sampleLimit: number = 3
): {
  id: string;
  model_id: string;
  model_name: string;
  benchmark_id: string;
  benchmark_name: string;
  status: 'completed';
  is_demo: boolean;
  pass_rate: number;
  passed_cases: number;
  total_cases: number;
  avg_latency_ms: number;
  case_results: TestCaseResult[];
  created_at: string;
} {
  const cases = SAMPLE_TEST_CASES[benchmarkId] || SAMPLE_TEST_CASES.coding_basics;
  const selectedCases = cases.slice(0, Math.min(sampleLimit, cases.length));

  const case_results: TestCaseResult[] = selectedCases.map((tc) => ({
    case_id: tc.id,
    prompt: tc.prompt,
    expected_output: tc.expected_output,
    actual_output: tc.simulated_response,
    passed: true,
    latency_ms: tc.simulated_latency_ms,
    assertion_type: tc.assertion_type,
  }));

  const total_cases = case_results.length;
  const passed_cases = case_results.filter((c) => c.passed).length;
  const pass_rate = total_cases > 0 ? passed_cases / total_cases : 1;
  const avg_latency_ms =
    case_results.reduce((sum, c) => sum + (c.latency_ms ?? 0), 0) / (total_cases || 1);

  const benchmarkNames: Record<string, string> = {
    coding_basics: 'Python Algorithmic Synthesis',
    reasoning_math: 'Mathematical Word Logic',
    structured_json: 'Constrained JSON Schema Extraction',
    rag_retrieval: 'Needle-in-a-Haystack Fact Recall',
  };

  return {
    id: `demo-${Date.now().toString(36)}`,
    model_id: modelId,
    model_name: modelName,
    benchmark_id: benchmarkId,
    benchmark_name: benchmarkNames[benchmarkId] || 'Custom Benchmark',
    status: 'completed',
    is_demo: true,
    pass_rate,
    passed_cases,
    total_cases,
    avg_latency_ms: Math.round(avg_latency_ms * 10) / 10,
    case_results,
    created_at: new Date().toISOString(),
  };
}
