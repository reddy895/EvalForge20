import React, { useEffect, useState } from 'react';
import { Bot } from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary, CaseResult } from '../api/types';
import { Badge } from '../components/ui/Badge';

export const AgentEvalPage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [cases, setCases] = useState<CaseResult[]>([]);
  const [selectedCase, setSelectedCase] = useState<CaseResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setIsLoading(true);
    api
      .listEvaluations({ limit: 50 })
      .then((data) => {
        setRuns(data);
        if (data.length > 0) {
          const runId = data[0].run_id;
          setSelectedRunId(runId);
          loadCases(runId);
        }
      })
      .catch(() => setRuns([]))
      .finally(() => setIsLoading(false));
  }, []);

  const loadCases = async (runId: string) => {
    try {
      const results = await api.getCaseResults(runId, 50, 0);
      setCases(results);
      if (results.length > 0) {
        setSelectedCase(results[0]);
      } else {
        setSelectedCase(null);
      }
    } catch {
      setCases([]);
      setSelectedCase(null);
    }
  };

  const handleRunChange = (id: string) => {
    setSelectedRunId(id);
    loadCases(id);
  };

  return (
    <div className="agent-eval-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">AI Agent & Tool Orchestration Evaluation</h1>
          <p className="page-header-subtitle">
            Inspect autonomous execution traces, tool call argument correctness, and task goal achievement.
          </p>
        </div>
      </div>

      <div className="report-controls-bar" style={{ marginBottom: 'var(--space-md)' }}>
        <div className="flex-row gap-sm">
          <Bot size={15} color="var(--accent-primary)" />
          <span className="text-label">Active Agent Run:</span>
          <select
            className="input-control font-mono"
            style={{ width: '280px' }}
            value={selectedRunId}
            onChange={(e) => handleRunChange(e.target.value)}
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.name} ({r.run_id.substring(0, 10)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div style={{ padding: 'var(--space-2xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading agent execution telemetry...
        </div>
      ) : cases.length === 0 ? (
        <div
          style={{
            padding: 'var(--space-2xl)',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-xs)',
            textAlign: 'center',
          }}
        >
          <Bot size={32} style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-sm)' }} />
          <div style={{ fontWeight: 600 }}>No Agent Cases Found</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)', marginTop: '4px' }}>
            Run an evaluation using <code>examples/datasets/agent_sample.jsonl</code> to inspect tool execution traces.
          </p>
        </div>
      ) : (
        <div className="datasets-grid-layout">
          {/* Agent Cases List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            <span className="text-label">Agent Task Cases</span>
            {cases.map((c) => {
              const isSelected = selectedCase?.case_id === c.case_id;
              const inputStr = typeof c.input === 'object' ? JSON.stringify(c.input) : String(c.input);

              return (
                <div
                  key={c.case_id}
                  className={`dataset-option-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedCase(c)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="dataset-option-info">
                    <div className="flex-row gap-xs">
                      <span className="font-mono" style={{ fontWeight: 600 }}>
                        {c.case_id}
                      </span>
                      {c.error_message ? (
                        <Badge variant="error">Failure</Badge>
                      ) : (
                        <Badge variant="success">Completed</Badge>
                      )}
                    </div>
                    <div className="dataset-option-desc">{inputStr}</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Agent Trace Inspector */}
          {selectedCase && (
            <div className="dataset-preview-panel">
              <div className="dataset-preview-header">
                <span className="dataset-preview-title">
                  Agent Trace: {selectedCase.case_id}
                </span>
                <span className="font-mono tabular-nums text-label">
                  {selectedCase.latency_ms ? `${selectedCase.latency_ms.toFixed(1)} ms` : '—'}
                </span>
              </div>

              <div className="dataset-preview-body">
                {/* Task Input */}
                <div className="inspector-section">
                  <div className="inspector-section-title">Task Goal & Instructions</div>
                  <div className="inspector-text-box">
                    {typeof selectedCase.input === 'object'
                      ? JSON.stringify(selectedCase.input, null, 2)
                      : String(selectedCase.input)}
                  </div>
                </div>

                {/* Expected Tool Invocations */}
                {selectedCase.expected_output && (
                  <div className="inspector-section">
                    <div className="inspector-section-title">Expected Tool Call / Outcome</div>
                    <div className="inspector-text-box">
                      {typeof selectedCase.expected_output === 'object'
                        ? JSON.stringify(selectedCase.expected_output, null, 2)
                        : String(selectedCase.expected_output)}
                    </div>
                  </div>
                )}

                {/* Execution Steps & Tool Calls */}
                <div className="inspector-section">
                  <div className="inspector-section-title">Execution Steps & Tool Calls</div>
                  {selectedCase.trace?.steps || selectedCase.trace?.tool_calls ? (
                    <div className="inspector-text-box font-mono">
                      {JSON.stringify(
                        selectedCase.trace?.steps || selectedCase.trace?.tool_calls,
                        null,
                        2
                      )}
                    </div>
                  ) : (
                    <div className="inspector-text-box" style={{ color: 'var(--text-muted)' }}>
                      No intermediate tool execution steps logged in trace metadata.
                    </div>
                  )}
                </div>

                {/* Final Response */}
                <div className="inspector-section">
                  <div className="inspector-section-title">Agent Final Response</div>
                  <div className="inspector-text-box font-mono">
                    {selectedCase.error_message ? (
                      <span style={{ color: 'var(--status-error)' }}>
                        {selectedCase.error_message}
                      </span>
                    ) : typeof selectedCase.actual_output === 'object' ? (
                      JSON.stringify(selectedCase.actual_output, null, 2)
                    ) : (
                      String(selectedCase.actual_output || '—')
                    )}
                  </div>
                </div>

                {/* Evaluator Verdicts */}
                <div className="inspector-section">
                  <div className="inspector-section-title">Tool Use & Completion Verdicts</div>
                  <div className="metrics-verdict-list">
                    {selectedCase.metrics.map((m) => (
                      <div
                        key={m.metric_id}
                        className={`metric-verdict-item ${
                          m.passed === true ? 'passed' : m.passed === false ? 'failed' : ''
                        }`}
                      >
                        <div className="metric-verdict-header">
                          <span className="metric-verdict-name">{m.metric_name}</span>
                          <span className="metric-verdict-score">
                            {m.score !== null ? `${(m.score * 100).toFixed(1)}%` : m.passed ? 'PASS' : 'FAIL'}
                          </span>
                        </div>
                        {m.reason && (
                          <div className="metric-verdict-reason">
                            <strong>Feedback:</strong> {m.reason}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
