import React, { useState, useEffect } from 'react';
import type { ModelCatalogItem, BenchmarkDefinition, EvaluationRun } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

interface LocalEvaluationPageProps {
  initialModelId?: string | null;
  onNavigateToHistory?: () => void;
}

export const LocalEvaluationPage: React.FC<LocalEvaluationPageProps> = ({
  initialModelId,
  onNavigateToHistory,
}) => {
  const [models, setModels] = useState<ModelCatalogItem[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkDefinition[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>(initialModelId || '');
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>('coding_basics');
  const [limit, setLimit] = useState<number>(3);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRun, setCurrentRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [modelsData, benchmarksData] = await Promise.all([
          api.getModels(),
          api.getBenchmarks(),
        ]);
        setModels(modelsData);
        setBenchmarks(benchmarksData);

        if (!selectedModelId && modelsData.length > 0) {
          // Default to first local model or first available model
          const localModel = modelsData.find(m => m.is_local) || modelsData[0];
          setSelectedModelId(localModel.id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load models and benchmarks');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [initialModelId]);

  const handleRunEvaluation = async () => {
    if (!selectedModelId || !selectedBenchmarkId) {
      setError('Please select both a model and a benchmark.');
      return;
    }

    try {
      setRunning(true);
      setError(null);
      const run = await api.runEvaluation({
        model_id: selectedModelId,
        benchmark_id: selectedBenchmarkId,
        limit,
      });
      setCurrentRun(run);
    } catch (err: any) {
      setError(err.message || 'Evaluation failed to complete.');
    } finally {
      setRunning(false);
    }
  };

  const selectedModel = models.find(m => m.id === selectedModelId);
  const selectedBenchmark = benchmarks.find(b => b.id === selectedBenchmarkId);

  if (loading) {
    return (
      <div className="py-16 text-center text-[#A5A59A]">
        Loading evaluation configuration...
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-[#393A33] pb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F0EEE6] tracking-tight">Evaluate Locally</h1>
          <p className="text-sm text-[#A5A59A] mt-1">
            Execute reproducible, deterministic test cases against local Ollama models or verified catalog test-doubles.
          </p>
        </div>
        {onNavigateToHistory && (
          <Button variant="secondary" onClick={onNavigateToHistory}>
            View Evaluation History &rarr;
          </Button>
        )}
      </div>

      {/* Execution Form Card */}
      <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-6 space-y-6">
        <h2 className="text-base font-semibold text-[#F0EEE6]">Run Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Model Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              Select Model
            </label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              disabled={running}
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            >
              <optgroup label="Local Models">
                {models.filter(m => m.is_local).map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider}) [Installed Local]
                  </option>
                ))}
              </optgroup>
              <optgroup label="Hosted & Catalog Models">
                {models.filter(m => !m.is_local).map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider})
                  </option>
                ))}
              </optgroup>
            </select>
            {selectedModel && (
              <div className="mt-2 flex items-center gap-2">
                <Badge variant={selectedModel.is_local ? 'success' : 'neutral'}>
                  {selectedModel.is_local ? 'Ollama Local' : 'Hosted/Catalog'}
                </Badge>
                <span className="text-xs text-[#A5A59A]">
                  Params: {selectedModel.parameter_count || 'N/A'}
                </span>
              </div>
            )}
          </div>

          {/* Benchmark Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              Select Benchmark Task
            </label>
            <select
              value={selectedBenchmarkId}
              onChange={(e) => setSelectedBenchmarkId(e.target.value)}
              disabled={running}
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            >
              {benchmarks.map(b => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.task})
                </option>
              ))}
            </select>
            {selectedBenchmark && (
              <p className="mt-2 text-xs text-[#A5A59A] line-clamp-2">
                {selectedBenchmark.description}
              </p>
            )}
          </div>

          {/* Test Case Limit */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              Sample Count (Cases)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min="1"
                max="10"
                value={limit}
                onChange={(e) => setLimit(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                disabled={running}
                className="w-24 bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
              />
              <span className="text-xs text-[#A5A59A]">
                1 to {selectedBenchmark?.total_cases || 5} cases
              </span>
            </div>
            <p className="mt-2 text-xs text-[#A5A59A]">
              Keeps execution reproducible and responsive.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/60 rounded text-xs text-red-300">
            {error}
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-[#A5A59A]">
            {running ? (
              <span className="inline-flex items-center gap-2 text-[#E58B45]">
                <span className="inline-block w-2 h-2 rounded-full bg-[#E58B45] animate-ping" />
                Executing test suite against {selectedModel?.name}...
              </span>
            ) : (
              <span>Ready to execute {limit} test cases with exact verification.</span>
            )}
          </div>
          <Button
            variant="primary"
            onClick={handleRunEvaluation}
            disabled={running || !selectedModelId}
          >
            {running ? 'Running Evaluation...' : 'Execute Evaluation'}
          </Button>
        </div>
      </div>

      {/* Results View */}
      {currentRun && (
        <div className="space-y-6">
          <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-[#393A33] gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-[#F0EEE6]">{currentRun.benchmark_name} Results</h3>
                  <Badge variant={currentRun.status === 'completed' ? 'success' : 'error'}>
                    {currentRun.status.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-[#A5A59A] mt-1">
                  Model: <span className="text-[#F0EEE6] font-mono">{currentRun.model_id}</span> &bull; Run ID: <span className="font-mono">{currentRun.id}</span>
                </p>
              </div>

              {/* Metrics Pills */}
              <div className="flex items-center gap-4">
                <div className="bg-[#171816] px-4 py-2 rounded border border-[#393A33] text-center">
                  <span className="block text-xs uppercase text-[#A5A59A]">Pass Rate</span>
                  <span className="text-lg font-bold text-[#E58B45]">
                    {((currentRun.metrics.pass_rate || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="bg-[#171816] px-4 py-2 rounded border border-[#393A33] text-center">
                  <span className="block text-xs uppercase text-[#A5A59A]">Passed / Total</span>
                  <span className="text-lg font-bold text-[#F0EEE6]">
                    {currentRun.metrics.passed_cases || 0} / {currentRun.metrics.total_cases || 0}
                  </span>
                </div>
                <div className="bg-[#171816] px-4 py-2 rounded border border-[#393A33] text-center">
                  <span className="block text-xs uppercase text-[#A5A59A]">Mean Latency</span>
                  <span className="text-lg font-bold text-[#F0EEE6]">
                    {currentRun.metrics.avg_latency_ms ? `${currentRun.metrics.avg_latency_ms.toFixed(0)}ms` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Test Cases Table */}
            <div className="mt-6">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-3">
                Individual Case Assertions
              </h4>
              <div className="overflow-x-auto border border-[#393A33] rounded">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-[#171816] text-[#A5A59A] border-b border-[#393A33]">
                    <tr>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Case ID</th>
                      <th className="py-2.5 px-3">Prompt</th>
                      <th className="py-2.5 px-3">Expected Output</th>
                      <th className="py-2.5 px-3">Actual Response</th>
                      <th className="py-2.5 px-3">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#393A33]">
                    {currentRun.case_results.map((c: any) => (
                      <tr key={c.case_id} className="hover:bg-[#171816]/50">
                        <td className="py-3 px-3 align-top">
                          <Badge variant={c.passed ? 'success' : 'error'}>
                            {c.passed ? 'PASS' : 'FAIL'}
                          </Badge>
                        </td>
                        <td className="py-3 px-3 font-mono text-[#A5A59A] align-top">{c.case_id}</td>
                        <td className="py-3 px-3 text-[#F0EEE6] max-w-xs truncate align-top" title={c.prompt || undefined}>
                          {c.prompt}
                        </td>
                        <td className="py-3 px-3 font-mono text-emerald-400 max-w-xs truncate align-top" title={c.expected_output || undefined}>
                          {c.expected_output}
                        </td>
                        <td className="py-3 px-3 font-mono text-[#F0EEE6] max-w-sm truncate align-top" title={c.actual_output || undefined}>
                          {c.actual_output || '<empty>'}
                        </td>
                        <td className="py-3 px-3 text-[#A5A59A] align-top whitespace-nowrap">
                          {c.latency_ms ? `${c.latency_ms.toFixed(0)} ms` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
