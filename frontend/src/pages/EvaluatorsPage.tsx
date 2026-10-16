import React, { useEffect, useState, useMemo } from 'react';
import { CheckSquare, RefreshCw, Cpu, Code2, Bot, Layers } from 'lucide-react';
import { api } from '../api/client';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { SearchBar } from '../components/ui/Input';
import './EvaluatorsPage.css';

interface EvaluatorCategorySection {
  title: string;
  icon: React.ReactNode;
  description: string;
  items: Array<{
    id: string;
    name: string;
    isModelBased: boolean;
    description: string;
    requiresExpected: boolean;
    taskType: string;
    outputMetric: string;
    status: 'active' | 'planned';
  }>;
}

export const EvaluatorsPage: React.FC = () => {
  const [registeredCount, setRegisteredCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await api.listMetrics();
      setRegisteredCount(data.length);
    } catch {
      setRegisteredCount(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const catalog: EvaluatorCategorySection[] = useMemo(() => {
    return [
      {
        title: 'Exact Match & Deterministic Equivalence',
        icon: <Code2 size={16} color="var(--accent-primary)" />,
        description: 'Zero-hallucination string and token equivalence algorithms.',
        items: [
          {
            id: 'exact_match',
            name: 'Exact Match',
            isModelBased: false,
            description: 'Strict character-for-character equivalence check against reference ground truth.',
            requiresExpected: true,
            taskType: 'Extraction, QA, Mathematical Proofs',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
          {
            id: 'normalized_match',
            name: 'Normalized Match',
            isModelBased: false,
            description: 'Whitespace, punctuation, and case-normalized equivalence comparison.',
            requiresExpected: true,
            taskType: 'General QA, Classification',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
          {
            id: 'token_f1',
            name: 'Token-Level F1 Score',
            isModelBased: false,
            description: 'Harmonic mean of unigram precision and recall across model output tokens.',
            requiresExpected: true,
            taskType: 'Summarization, Reading Comprehension',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
          {
            id: 'classification_accuracy',
            name: 'Classification Accuracy',
            isModelBased: false,
            description: 'Exact label match after stripping surrounding discursive artifacts.',
            requiresExpected: true,
            taskType: 'Sentiment, Intent, Topic Classification',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
        ],
      },
      {
        title: 'Schema & Structural Validation',
        icon: <CheckSquare size={16} />,
        description: 'Enforces structural invariants, parsing validity, and length constraints.',
        items: [
          {
            id: 'json_validity',
            name: 'JSON Validity',
            isModelBased: false,
            description: 'Validates whether model response parses into well-formed JSON syntax.',
            requiresExpected: false,
            taskType: 'Structured Outputs, Function Calling',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
          {
            id: 'json_schema',
            name: 'JSON Schema Validity',
            isModelBased: false,
            description: 'Enforces strict JSON Schema property types, required keys, and bounds.',
            requiresExpected: false,
            taskType: 'Tool Calls, Form Extraction',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
          {
            id: 'response_completeness',
            name: 'Response Completeness',
            isModelBased: false,
            description: 'Verifies minimum word counts, sentence boundary terminations, and truncation.',
            requiresExpected: false,
            taskType: 'Long-form Generation, Chat',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
        ],
      },
      {
        title: 'Model-Based Evaluators (LLM-as-Judge)',
        icon: <Cpu size={16} color="var(--accent-primary)" />,
        description: 'Semantic evaluations scored via verified local Ollama judge instances.',
        items: [
          {
            id: 'ollama_judge_answer_relevance',
            name: 'Answer Relevance',
            isModelBased: true,
            description: 'Evaluates prompt adherence, directness, and absence of tangential fluff.',
            requiresExpected: false,
            taskType: 'Open-ended QA, Dialogue',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
          {
            id: 'ollama_judge_factual_correctness',
            name: 'Factual Correctness',
            isModelBased: true,
            description: 'Verifies factual claims against reference ground truth using local judge.',
            requiresExpected: true,
            taskType: 'Knowledge Retrieval, Technical QA',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
          {
            id: 'ollama_judge_explanation_quality',
            name: 'Explanation Quality',
            isModelBased: true,
            description: 'Evaluates logical step coherence, reasoning completeness, and didactic clarity.',
            requiresExpected: false,
            taskType: 'Chain-of-Thought, Reasoning',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
        ],
      },
      {
        title: 'RAG & Retrieval Evaluation',
        icon: <Layers size={16} />,
        description: 'Specialized metrics for grounded retrieval-augmented generation pipelines.',
        items: [
          {
            id: 'ollama_judge_context_faithfulness',
            name: 'Context Faithfulness',
            isModelBased: true,
            description: 'Measures groundedness and penalizes hallucinations against retrieved context passages.',
            requiresExpected: false,
            taskType: 'RAG, Document Search',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'active',
          },
          {
            id: 'context_precision',
            name: 'Context Precision',
            isModelBased: true,
            description: 'Measures whether retrieved documents are ranked with relevant context at top.',
            requiresExpected: true,
            taskType: 'Vector Search, Reranking',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'planned',
          },
        ],
      },
      {
        title: 'AI Agent & Tool-Use Evaluation',
        icon: <Bot size={16} />,
        description: 'Telemetry and verification for autonomous agents and tool orchestration.',
        items: [
          {
            id: 'agent_tool_selection',
            name: 'Tool Selection Accuracy',
            isModelBased: false,
            description: 'Validates that the agent selected the appropriate tool for the assigned goal.',
            requiresExpected: true,
            taskType: 'Agent Tool Invocation',
            outputMetric: 'Binary (0.0 or 1.0)',
            status: 'active',
          },
          {
            id: 'agent_task_completion',
            name: 'Task Completion Rate',
            isModelBased: true,
            description: 'Determines whether agent execution sequence accomplished user target state.',
            requiresExpected: true,
            taskType: 'Autonomous Agents, Multi-Turn Workflow',
            outputMetric: 'Continuous [0.0, 1.0]',
            status: 'planned',
          },
        ],
      },
    ];
  }, []);

  const filteredCatalog = catalog
    .map((cat) => ({
      ...cat,
      items: cat.items.filter((item) => {
        const q = searchQuery.toLowerCase().trim();
        return (
          !q ||
          item.name.toLowerCase().includes(q) ||
          item.id.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.taskType.toLowerCase().includes(q)
        );
      }),
    }))
    .filter((cat) => cat.items.length > 0);

  return (
    <div className="evaluators-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Evaluator Catalog</h1>
          <p className="page-header-subtitle">
            Inspect {registeredCount > 0 ? `${registeredCount} verified registry scoring metrics` : 'registered metrics'}, required inputs, task applicability, and judge architectures.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchMetrics}
          >
            Sync Registry
          </Button>
        </div>
      </div>

      <SearchBar
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onClear={() => setSearchQuery('')}
        placeholder="Filter evaluators by metric ID, description, or task type..."
      />

      {filteredCatalog.map((cat) => (
        <div key={cat.title} className="category-section">
          <div className="category-section-header">
            <div className="category-section-title">
              {cat.icon}
              <span>{cat.title}</span>
            </div>
            <span className="font-mono text-label">{cat.items.length} evaluators</span>
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
            {cat.description}
          </p>

          <div className="evaluators-catalog-grid">
            {cat.items.map((item) => (
              <div key={item.id} className="evaluator-catalog-card">
                <div className="evaluator-card-header">
                  <div className="flex-row gap-xs">
                    <span className="evaluator-title">{item.name}</span>
                    <Badge variant={item.isModelBased ? 'accent' : 'neutral'}>
                      {item.isModelBased ? 'Model-Based' : 'Deterministic'}
                    </Badge>
                  </div>
                  {item.status === 'active' ? (
                    <Badge variant="success" showDot>
                      Active
                    </Badge>
                  ) : (
                    <Badge variant="warning">Planned</Badge>
                  )}
                </div>

                <div className="evaluator-card-desc">{item.description}</div>

                <div className="evaluator-meta-specs">
                  <div className="evaluator-spec-item">
                    <span className="evaluator-spec-label">Metric ID</span>
                    <span className="evaluator-spec-value">{item.id}</span>
                  </div>
                  <div className="evaluator-spec-item">
                    <span className="evaluator-spec-label">Output Metric</span>
                    <span className="evaluator-spec-value">{item.outputMetric}</span>
                  </div>
                  <div className="evaluator-spec-item">
                    <span className="evaluator-spec-label">Requires Ground Truth</span>
                    <span className="evaluator-spec-value">
                      {item.requiresExpected ? 'Yes (expected_output)' : 'No (Reference-Free)'}
                    </span>
                  </div>
                  <div className="evaluator-spec-item">
                    <span className="evaluator-spec-label">Applicable Tasks</span>
                    <span className="evaluator-spec-value">{item.taskType}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
