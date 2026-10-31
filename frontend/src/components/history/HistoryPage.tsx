import React, { useState } from 'react';
import { EvaluationRun, NavRoute } from '../../types';
import { api } from '../../services/api';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Modal } from '../ui/Modal';
import { useToast } from '../ui/Toast';
import { EvaluationResultCharts } from '../../charts';
import {
  History,
  Download,
  Trash2,
  Play,
  ArrowRight,
  Eye,
} from 'lucide-react';

interface HistoryPageProps {
  historyRuns: EvaluationRun[];
  onClearHistory: () => void;
  onRouteChange: (route: NavRoute) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  historyRuns,
  onClearHistory,
  onRouteChange,
}) => {
  const { info, success } = useToast();
  const [inspectRun, setInspectRun] = useState<EvaluationRun | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);

  const handleInspect = async (run: EvaluationRun) => {
    if (run.case_results && run.case_results.length > 0) {
      setInspectRun(run);
      return;
    }
    setInspectLoading(true);
    try {
      const details = await api.getEvaluationDetails(run.id);
      const fullRun: EvaluationRun = {
        ...run,
        pass_rate: details.pass_rate !== undefined ? details.pass_rate : run.pass_rate,
        passed_cases: details.passed_cases || run.passed_cases,
        total_cases: details.total_cases || run.total_cases,
        avg_latency_ms: details.avg_latency_ms || run.avg_latency_ms,
        median_latency_ms: details.median_latency_ms,
        p95_latency_ms: details.p95_latency_ms,
        tokens_per_second: details.tokens_per_second,
        load_duration_ms: details.load_duration_ms,
        case_results: (details.case_results || []).map((c: any) => ({
          case_id: c.case_id,
          prompt: c.prompt,
          expected_output: c.expected_output || '',
          actual_output: c.actual_output || '',
          passed: Boolean(c.passed),
          latency_ms: Number((c.latency_ms || 0).toFixed(1)),
          assertion_type: c.assertion_type || 'exact_match',
        })),
      };
      setInspectRun(fullRun);
    } catch {
      setInspectRun(run);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleExportAll = () => {
    if (historyRuns.length === 0) return;
    const dataStr =
      'data:text/json;charset=utf-8,' +
      encodeURIComponent(JSON.stringify(historyRuns, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `evalforge20-full-audit-log.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    success('Exported History', `Saved ${historyRuns.length} runs to JSON`);
  };

  const handleExportSingle = (run: EvaluationRun) => {
    const dataStr =
      'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(run, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `evalforge20-run-${run.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    info('Exported Single Run', `Saved ${run.id}.json`);
  };

  const handleExportAllCsv = () => {
    if (historyRuns.length === 0) return;
    const headers = ['run_id', 'created_at', 'model_name', 'benchmark_name', 'pass_rate', 'passed_cases', 'total_cases', 'avg_latency_ms', 'status'];
    const rows = historyRuns.map((r) => [
      r.id,
      r.created_at,
      `"${r.model_name}"`,
      `"${r.benchmark_name}"`,
      r.pass_rate,
      r.passed_cases,
      r.total_cases,
      r.avg_latency_ms,
      r.status,
    ]);
    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', url);
    downloadAnchor.setAttribute('download', 'evalforge20-runs-summary.csv');
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    success('Exported History CSV', `Saved ${historyRuns.length} runs to CSV`);
  };

  // Aggregated Stats
  const totalRuns = historyRuns.length;
  const totalCases = historyRuns.reduce((sum, r) => sum + r.total_cases, 0);
  const totalPassed = historyRuns.reduce((sum, r) => sum + r.passed_cases, 0);
  const avgPassRate = totalCases > 0 ? (totalPassed / totalCases) * 100 : 0;
  const runsWithLatency = historyRuns.filter((r) => r.avg_latency_ms !== undefined && r.avg_latency_ms > 0);
  const avgLatency =
    runsWithLatency.length > 0
      ? (runsWithLatency.reduce((sum, r) => sum + (r.avg_latency_ms || 0), 0) / runsWithLatency.length).toFixed(1)
      : 'N/A';

  return (
    <div className="py-10 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#41413B]">
        <div className="flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#14B8A6]">
            <History size={14} />
            <span>AUDIT & REPRODUCIBILITY TRAIL</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Run History
          </h1>
          <p className="text-sm text-[#A6A49D] max-w-xl">
            Audit logs for all evaluation runs executed in this session. Review test case assertions,
            reproduce past runs, and export structured benchmark telemetry.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-3">
          {historyRuns.length > 0 && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportAll}
                iconLeft={<Download size={14} />}
              >
                Export JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportAllCsv}
                iconLeft={<Download size={14} />}
              >
                Export CSV
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={onClearHistory}
                iconLeft={<Trash2 size={14} />}
              >
                Clear History
              </Button>
            </>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={() => onRouteChange('evaluate')}
            iconLeft={<Play size={14} className="fill-current" />}
          >
            New Run
          </Button>
        </div>
      </div>

      {/* Aggregate Statistics */}
      {historyRuns.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 rounded-3xl bg-[#242522] border border-[#41413B] shadow-sm font-mono text-xs">
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1 font-sans">Total Test Runs</span>
            <span className="text-xl font-bold text-[#F5F0E7]">{totalRuns}</span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1 font-sans">Overall Pass Rate</span>
            <span className="text-xl font-bold text-[#14B8A6]">{avgPassRate.toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1 font-sans">
              Test Cases Evaluated
            </span>
            <span className="text-xl font-bold text-[#F5F0E7]">
              {totalPassed} / {totalCases}
            </span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1 font-sans">Mean Latency</span>
            <span className="text-xl font-bold text-[#F5F0E7]">{avgLatency} ms</span>
          </div>
        </div>
      )}

      {/* Runs List */}
      {historyRuns.length === 0 ? (
        <div className="py-20 px-6 rounded-3xl bg-[#242522] border border-[#41413B] text-center flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#191A18] border border-[#41413B] flex items-center justify-center text-[#14B8A6]">
            <History size={20} />
          </div>
          <h3 className="text-lg font-semibold text-[#F5F0E7]">No evaluation history recorded</h3>
          <p className="text-sm text-[#A6A49D] max-w-sm">
            You haven't executed any benchmark suites yet. Launch an evaluation to start recording
            empirical metrics.
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onRouteChange('evaluate')}
            iconRight={<ArrowRight size={14} />}
          >
            Launch Evaluation Studio
          </Button>
        </div>
      ) : (

        <div className="rounded-3xl bg-[#242522] border border-[#41413B] overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#191A18] text-[#A6A49D] font-mono border-b border-[#41413B]">
                <tr>
                  <th className="p-4">Run ID / Timestamp</th>
                  <th className="p-4">Model</th>
                  <th className="p-4">Benchmark Suite</th>
                  <th className="p-4">Pass Rate</th>
                  <th className="p-4">Latency</th>
                  <th className="p-4">Mode</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#41413B]/60 font-mono">
                {historyRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-4">
                      <div className="flex flex-col">
                        <span className="font-bold text-[#F5F0E7]">{run.id}</span>
                        <span className="text-[11px] text-[#78766F] font-sans">
                          {new Date(run.created_at).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 font-semibold text-[#F5F0E7] font-sans">
                      {run.model_name}
                    </td>
                    <td className="p-4 text-[#A6A49D] font-sans">{run.benchmark_name}</td>
                    <td className="p-4">
                      {run.pass_rate === 0 ? (
                        <span className="text-[#A6A49D] font-bold" title="Completed with genuine 0% pass rate">
                          0% <span className="text-[10px] text-[#A6A49D] font-normal font-sans">(Genuine 0)</span>
                        </span>
                      ) : (
                        <span className="text-[#14B8A6] font-bold">
                          {(run.pass_rate * 100).toFixed(0)}%
                        </span>
                      )}{' '}
                      <span className="text-[11px] text-[#A6A49D]">
                        ({run.passed_cases}/{run.total_cases})
                      </span>
                    </td>
                    <td className="p-4 text-[#F5F0E7]">{run.avg_latency_ms} ms</td>
                    <td className="p-4">
                      <Badge variant={run.is_demo ? "demo" : "installed"} size="sm">
                        {run.is_demo ? "Demo" : "Ollama"}
                      </Badge>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleInspect(run)}
                          loading={inspectLoading}
                          iconLeft={<Eye size={12} />}
                        >
                          Inspect
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleExportSingle(run)}
                          title="Export JSON"
                        >
                          <Download size={13} className="text-[#A6A49D]" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Inspect Past Run Modal */}
      {inspectRun && (
        <Modal
          isOpen={true}
          onClose={() => setInspectRun(null)}
          title={`Audit Run: ${inspectRun.id}`}
          subtitle={`${inspectRun.model_name} — ${inspectRun.benchmark_name}`}
          size="lg"
        >
          <div className="flex flex-col gap-4 max-h-[70vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-3 gap-3 p-3.5 rounded-2xl bg-[#191A18] border border-[#41413B] font-mono text-xs">
              <div>
                <span className="text-[#A6A49D] block text-[11px]">Pass Rate:</span>
                <span className="text-[#14B8A6] font-bold">
                  {(inspectRun.pass_rate * 100).toFixed(0)}% ({inspectRun.passed_cases}/
                  {inspectRun.total_cases})
                </span>
              </div>
              <div>
                <span className="text-[#A6A49D] block text-[11px]">Average Latency:</span>
                <span className="text-[#F5F0E7] font-bold">{inspectRun.avg_latency_ms} ms</span>
              </div>
              <div>
                <span className="text-[#A6A49D] block text-[11px]">Executed:</span>
                <span className="text-[#F5F0E7] text-[11px]">
                  {new Date(inspectRun.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>

            {/* Graphical Performance & Accuracy Telemetry */}
            <EvaluationResultCharts run={inspectRun} />

            <div className="flex flex-col gap-3">

              {inspectRun.case_results.map((c, i) => (
                <div
                  key={c.case_id}
                  className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-2 text-xs font-mono"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[#14B8A6] font-semibold">
                      #{i + 1} {c.case_id} ({c.assertion_type})
                    </span>
                    <span className={c.passed ? "text-[#14B8A6] font-bold" : "text-[#E06C75] font-bold"}>
                      {c.passed ? "PASSED" : "FAILED"} ({c.latency_ms} ms)
                    </span>
                  </div>
                  <div className="text-[#A6A49D]">
                    <span className="text-[#78766F] block text-[10px]">PROMPT:</span>
                    <p className="bg-[#242522] p-2 rounded-xl border border-[#41413B]/60 text-[#F5F0E7]">
                      {c.prompt}
                    </p>
                  </div>
                  <div className="text-[#14B8A6]">
                    <span className="text-[#78766F] block text-[10px]">OUTPUT:</span>
                    <pre className="bg-[#242522] p-2 rounded-xl border border-[#41413B]/60 text-xs whitespace-pre-wrap">
                      {c.actual_output}
                    </pre>
                  </div>
                </div>
              ))}
            </div>


            <div className="flex justify-end pt-3 border-t border-[#41413B]">
              <Button variant="secondary" size="sm" onClick={() => setInspectRun(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
