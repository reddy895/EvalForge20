import React, { useState, useMemo } from 'react';
import type { CaseResult } from '../../api/types';
import { Badge } from '../ui/Badge';
import { DataTable, type Column } from '../ui/DataTable';
import { InspectorDrawer } from '../ui/Modal';
import './CaseResultsTable.css';

interface CaseResultsTableProps {
  cases: CaseResult[];
  isLoading?: boolean;
}

export const CaseResultsTable: React.FC<CaseResultsTableProps> = ({ cases, isLoading }) => {
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');
  const [selectedCase, setSelectedCase] = useState<CaseResult | null>(null);

  const filteredCases = useMemo(() => {
    if (filter === 'passed') {
      return cases.filter((c) => {
        if (c.error_category || c.error_message) return false;
        return c.metrics.every((m) => m.passed !== false);
      });
    }
    if (filter === 'failed') {
      return cases.filter((c) => {
        if (c.error_category || c.error_message) return true;
        return c.metrics.some((m) => m.passed === false);
      });
    }
    return cases;
  }, [cases, filter]);

  const columns: Column<CaseResult>[] = [
    {
      key: 'case_id',
      header: 'Case ID',
      sortable: true,
      width: '120px',
      render: (c) => (
        <span className="font-mono" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
          {c.case_id}
        </span>
      ),
    },
    {
      key: 'input',
      header: 'Input Prompt',
      render: (c) => {
        const text = typeof c.input === 'object' ? JSON.stringify(c.input) : String(c.input);
        return (
          <div
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '260px',
            }}
            title={text}
          >
            {text}
          </div>
        );
      },
    },
    {
      key: 'expected_output',
      header: 'Expected Output',
      render: (c) => {
        if (!c.expected_output) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
        const text =
          typeof c.expected_output === 'object'
            ? JSON.stringify(c.expected_output)
            : String(c.expected_output);
        return (
          <div
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '200px',
              color: 'var(--text-secondary)',
            }}
            title={text}
          >
            {text}
          </div>
        );
      },
    },
    {
      key: 'actual_output',
      header: 'Actual Output',
      render: (c) => {
        if (c.error_message) {
          return (
            <span style={{ color: 'var(--status-error)', fontSize: '11px' }}>
              Error: {c.error_message}
            </span>
          );
        }
        if (!c.actual_output) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
        const text =
          typeof c.actual_output === 'object'
            ? JSON.stringify(c.actual_output)
            : String(c.actual_output);
        return (
          <div
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '220px',
            }}
            title={text}
          >
            {text}
          </div>
        );
      },
    },
    {
      key: 'verdict',
      header: 'Metric Verdicts',
      width: '180px',
      render: (c) => {
        if (c.error_category) {
          const label =
            c.error_category === 'authentication_error'
              ? 'AUTH ERROR'
              : c.error_category.replace(/_/g, ' ').toUpperCase();
          return (
            <Badge variant="error" title={c.error_message || undefined}>
              {label}
            </Badge>
          );
        }
        if (c.error_message) {
          return (
            <Badge variant="error" title={c.error_message}>
              ERROR
            </Badge>
          );
        }
        if (!c.metrics || c.metrics.length === 0) {
          return <Badge variant="neutral">No Metrics</Badge>;
        }

        return (
          <div className="flex-row gap-xs" style={{ flexWrap: 'wrap' }}>
            {c.metrics.map((m) => (
              <Badge
                key={m.metric_id}
                variant={m.passed === true ? 'success' : m.passed === false ? 'error' : 'neutral'}
                title={m.reason || undefined}
              >
                {m.metric_name}:{' '}
                {m.score !== null && m.score !== undefined
                  ? `${(m.score * 100).toFixed(0)}%`
                  : m.passed ? 'PASS' : 'FAIL'}
              </Badge>
            ))}
          </div>
        );
      },
    },
    {
      key: 'tokens',
      header: 'Tokens',
      sortable: true,
      align: 'right',
      width: '85px',
      render: (c) => {
        const total = c.token_usage?.total_tokens ?? c.token_usage?.total;
        return (
          <span className="font-mono tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            {total !== undefined && total !== null ? total.toLocaleString() : '—'}
          </span>
        );
      },
      sortValue: (c) => (c.token_usage?.total_tokens ?? c.token_usage?.total ?? -1),
    },
    {
      key: 'latency_ms',
      header: 'Latency',
      sortable: true,
      align: 'right',
      width: '90px',
      render: (c) => (
        <span className="font-mono tabular-nums">
          {c.latency_ms !== null && c.latency_ms !== undefined
            ? `${c.latency_ms.toFixed(0)} ms`
            : '—'}
        </span>
      ),
      sortValue: (c) => c.latency_ms ?? -1,
    },
  ];

  return (
    <div className="case-results-card">
      <div className="case-results-header">
        <div className="flex-row gap-sm">
          <span className="case-results-title">Per-Case Results</span>
          <span className="font-mono text-label" style={{ color: 'var(--text-muted)' }}>
            ({cases.length} cases evaluated)
          </span>
        </div>

        <div className="case-filter-pills">
          <button
            type="button"
            className={`case-filter-pill ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({cases.length})
          </button>
          <button
            type="button"
            className={`case-filter-pill ${filter === 'passed' ? 'active' : ''}`}
            onClick={() => setFilter('passed')}
          >
            Passed
          </button>
          <button
            type="button"
            className={`case-filter-pill ${filter === 'failed' ? 'active' : ''}`}
            onClick={() => setFilter('failed')}
          >
            Failed
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filteredCases}
        keyExtractor={(c) => c.case_id}
        isLoading={isLoading}
        onRowClick={(c) => setSelectedCase(c)}
        pageSize={15}
        emptyMessage="No test cases match the selected filter."
      />

      {/* Case Detailed Inspector Drawer */}
      <InspectorDrawer
        isOpen={Boolean(selectedCase)}
        onClose={() => setSelectedCase(null)}
        title={`Case Inspector — ${selectedCase?.case_id}`}
        subtitle="Prompt Input, Reference Output, Response, and Metric Verdicts"
      >
        {selectedCase && (
          <div>
            {/* Prompt Input */}
            <div className="inspector-section">
              <div className="inspector-section-title">Prompt / Input Payload</div>
              <div className="inspector-text-box">
                {typeof selectedCase.input === 'object'
                  ? JSON.stringify(selectedCase.input, null, 2)
                  : String(selectedCase.input)}
              </div>
            </div>

            {/* Expected Output */}
            {selectedCase.expected_output && (
              <div className="inspector-section">
                <div className="inspector-section-title">Expected Reference Ground Truth</div>
                <div className="inspector-text-box">
                  {typeof selectedCase.expected_output === 'object'
                    ? JSON.stringify(selectedCase.expected_output, null, 2)
                    : String(selectedCase.expected_output)}
                </div>
              </div>
            )}

            {/* Actual Output */}
            <div className="inspector-section">
              <div className="inspector-section-title">Model Actual Response</div>
              <div
                className="inspector-text-box font-mono"
                style={{
                  borderColor: selectedCase.error_message
                    ? 'var(--status-error-border)'
                    : 'var(--border-default)',
                }}
              >
                {selectedCase.error_message ? (
                  <span style={{ color: 'var(--status-error)' }}>
                    [Execution Error: {selectedCase.error_category || 'ProviderFailure'}]
                    {'\n'}
                    {selectedCase.error_message}
                  </span>
                ) : typeof selectedCase.actual_output === 'object' ? (
                  JSON.stringify(selectedCase.actual_output, null, 2)
                ) : (
                  String(selectedCase.actual_output || '—')
                )}
              </div>
            </div>

            {/* Evaluator Verdicts & Reasons */}
            <div className="inspector-section">
              <div className="inspector-section-title">Evaluator Verdicts & Rationale</div>
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
                        Score: {m.score !== null ? `${(m.score * 100).toFixed(1)}%` : '—'}
                      </span>
                    </div>
                    {m.reason && (
                      <div className="metric-verdict-reason">
                        <strong>Reason:</strong> {m.reason}
                      </div>
                    )}
                    {m.details && Object.keys(m.details).length > 0 && (
                      <pre style={{ marginTop: '4px', fontSize: '10px' }}>
                        {JSON.stringify(m.details, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Execution Telemetry */}
            <div className="inspector-section">
              <div className="inspector-section-title">Execution Telemetry</div>
              <div className="grid-2" style={{ gap: 'var(--space-sm)' }}>
                <div className="meta-field">
                  <span className="meta-label">Latency</span>
                  <span className="meta-val font-mono">
                    {selectedCase.latency_ms !== null ? `${selectedCase.latency_ms.toFixed(1)} ms` : '—'}
                  </span>
                </div>
                {(selectedCase.trace?.complexity_band || (selectedCase.input as any)?.complexity) && (
                  <div className="meta-field">
                    <span className="meta-label">Complexity Band</span>
                    <span className="meta-val">
                      <Badge variant="neutral">
                        {String(selectedCase.trace?.complexity_band || (selectedCase.input as any)?.complexity).toUpperCase()}
                      </Badge>
                    </span>
                  </div>
                )}
                {selectedCase.token_usage?.prompt_tokens !== undefined && (
                  <div className="meta-field">
                    <span className="meta-label">Prompt Tokens</span>
                    <span className="meta-val font-mono">
                      {selectedCase.token_usage.prompt_tokens.toLocaleString()}
                    </span>
                  </div>
                )}
                {selectedCase.token_usage?.completion_tokens !== undefined && (
                  <div className="meta-field">
                    <span className="meta-label">Completion Tokens</span>
                    <span className="meta-val font-mono">
                      {selectedCase.token_usage.completion_tokens.toLocaleString()}
                    </span>
                  </div>
                )}
                {(selectedCase.token_usage?.total_tokens !== undefined || selectedCase.token_usage?.total !== undefined) && (
                  <div className="meta-field">
                    <span className="meta-label">Total Tokens</span>
                    <span className="meta-val font-mono">
                      {(selectedCase.token_usage.total_tokens ?? selectedCase.token_usage.total ?? 0).toLocaleString()}
                    </span>
                  </div>
                )}
                {selectedCase.trace?.estimated_cost_usd !== undefined && (
                  <div className="meta-field">
                    <span className="meta-label">Estimated Cost</span>
                    <span className="meta-val font-mono">
                      ${Number(selectedCase.trace.estimated_cost_usd).toFixed(6)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Trace payload if present */}
            {selectedCase.trace && Object.keys(selectedCase.trace).length > 0 && (
              <div className="inspector-section">
                <div className="inspector-section-title">Diagnostic Execution Trace</div>
                <pre style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  {JSON.stringify(selectedCase.trace, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </InspectorDrawer>
    </div>
  );
};
