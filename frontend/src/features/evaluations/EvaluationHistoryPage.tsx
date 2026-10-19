import React, { useState, useEffect } from 'react';
import type { EvaluationRun } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

interface EvaluationHistoryPageProps {
  onNewEvaluation: () => void;
}

export const EvaluationHistoryPage: React.FC<EvaluationHistoryPageProps> = ({
  onNewEvaluation,
}) => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        const data = await api.getEvaluationRuns();
        setRuns(data);
        if (data.length > 0) {
          setSelectedRun(data[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load evaluation history');
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const handleExportJson = () => {
    if (!selectedRun) return;
    const blob = new Blob([JSON.stringify(selectedRun, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evalforge20-run-${selectedRun.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-[#A5A59A]">
        Loading persisted evaluation history...
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-[#393A33] pb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F0EEE6] tracking-tight">Evaluation History</h1>
          <p className="text-sm text-[#A5A59A] mt-1">
            Audit trail of all benchmark executions, exact test cases, latency measurements, and pass rates.
          </p>
        </div>
        <Button variant="primary" onClick={onNewEvaluation}>
          + Run New Evaluation
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded text-sm text-red-300">
          {error}
        </div>
      )}

      {runs.length === 0 ? (
        <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-12 text-center space-y-4">
          <p className="text-[#A5A59A]">No evaluations recorded in database yet.</p>
          <Button variant="primary" onClick={onNewEvaluation}>
            Launch First Local Evaluation
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Runs Sidebar List */}
          <div className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#A5A59A]">
              Historical Runs ({runs.length})
            </h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {runs.map((r) => {
                const isSelected = selectedRun?.id === r.id;
                const passRate = ((r.metrics?.pass_rate || 0) * 100).toFixed(0);
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRun(r)}
                    className={`p-4 rounded border transition-colors cursor-pointer text-left ${
                      isSelected
                        ? 'bg-[#20211E] border-[#E58B45]'
                        : 'bg-[#171816] border-[#393A33] hover:border-[#A5A59A]/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-[#F0EEE6] truncate max-w-[160px]">
                        {r.model_id}
                      </span>
                      <Badge variant={r.status === 'completed' ? 'success' : 'danger'}>
                        {passRate}%
                      </Badge>
                    </div>
                    <p className="text-xs text-[#A5A59A] mt-1 truncate">
                      {r.benchmark_name}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-[#A5A59A] mt-2 pt-2 border-t border-[#393A33]/50">
                      <span>{r.metrics?.total_cases || 0} cases</span>
                      <span>{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Run Detail Inspection */}
          <div className="lg:col-span-2">
            {selectedRun ? (
              <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-6 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#393A33] gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-[#F0EEE6]">
                      {selectedRun.benchmark_name}
                    </h3>
                    <p className="text-xs text-[#A5A59A] mt-1 font-mono">
                      Run ID: {selectedRun.id} &bull; Executed at: {new Date(selectedRun.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={handleExportJson}>
                    Export JSON
                  </Button>
                </div>

                {/* Score Summary Metrics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-[#171816] p-3 rounded border border-[#393A33]">
                    <span className="block text-xs uppercase text-[#A5A59A]">Pass Rate</span>
                    <span className="text-xl font-bold text-[#E58B45]">
                      {((selectedRun.metrics.pass_rate || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="bg-[#171816] p-3 rounded border border-[#393A33]">
                    <span className="block text-xs uppercase text-[#A5A59A]">Cases Passed</span>
                    <span className="text-xl font-bold text-[#F0EEE6]">
                      {selectedRun.metrics.passed_cases || 0} / {selectedRun.metrics.total_cases || 0}
                    </span>
                  </div>
                  <div className="bg-[#171816] p-3 rounded border border-[#393A33]">
                    <span className="block text-xs uppercase text-[#A5A59A]">Mean Latency</span>
                    <span className="text-xl font-bold text-[#F0EEE6]">
                      {selectedRun.metrics.avg_latency_ms ? `${selectedRun.metrics.avg_latency_ms.toFixed(0)}ms` : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Case Assertions */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-3">
                    Case Results ({selectedRun.case_results.length})
                  </h4>
                  <div className="overflow-x-auto border border-[#393A33] rounded">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-[#171816] text-[#A5A59A] border-b border-[#393A33]">
                        <tr>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Case ID</th>
                          <th className="py-2.5 px-3">Prompt</th>
                          <th className="py-2.5 px-3">Expected</th>
                          <th className="py-2.5 px-3">Actual</th>
                          <th className="py-2.5 px-3">Latency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#393A33]">
                        {selectedRun.case_results.map((c) => (
                          <tr key={c.case_id} className="hover:bg-[#171816]/50">
                            <td className="py-2.5 px-3">
                              <Badge variant={c.passed ? 'success' : 'danger'}>
                                {c.passed ? 'PASS' : 'FAIL'}
                              </Badge>
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[#A5A59A]">{c.case_id}</td>
                            <td className="py-2.5 px-3 text-[#F0EEE6] max-w-xs truncate" title={c.prompt}>
                              {c.prompt}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-emerald-400 max-w-xs truncate" title={c.expected_output || undefined}>
                              {c.expected_output}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[#F0EEE6] max-w-xs truncate" title={c.actual_output || undefined}>
                              {c.actual_output || '<empty>'}
                            </td>
                            <td className="py-2.5 px-3 text-[#A5A59A] whitespace-nowrap">
                              {c.latency_ms ? `${c.latency_ms.toFixed(0)} ms` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-12 text-center text-[#A5A59A]">
                Select a run from the list to view detailed case results.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
