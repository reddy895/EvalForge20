import React, { useEffect, useState } from 'react';
import { SAMPLE_MODELS } from '../../data/models';
import { EvaluationRun, ModelProfile, NavRoute } from '../../types';
import { api } from '../../services/api';
import { useOllamaStatus } from '../../hooks/useOllamaStatus';
import { EvaluationResultCharts } from '../../charts';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { useToast } from '../ui/Toast';
import {
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Terminal,
  Zap,
  Code,
  FileCode,
  HardDrive,
  RotateCcw,
  Sparkles,
} from 'lucide-react';


interface EvaluatePageProps {
  initialModelId?: string;
  onSaveToHistory: (run: EvaluationRun) => void;
  onRouteChange: (route: NavRoute) => void;
}

export const EvaluatePage: React.FC<EvaluatePageProps> = ({
  initialModelId,
  onSaveToHistory,
  onRouteChange,
}) => {
  const { success, info, error: showError } = useToast();
  const ollamaStatus = useOllamaStatus();

  const [selectedModelId, setSelectedModelId] = useState<string>(
    initialModelId || 'qwen-2.5-1.5b-instruct'
  );
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>('coding_basics');
  const [sampleLimit, setSampleLimit] = useState<number>(3);

  const [availableModels, setAvailableModels] = useState<ModelProfile[]>(SAMPLE_MODELS);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentProgress, setCurrentProgress] = useState<number>(0);
  const [progressStatus, setProgressStatus] = useState<string>('');
  const [activeRunResult, setActiveRunResult] = useState<EvaluationRun | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    api.getModels({ limit: 50 }).then((res) => {
      if (res?.models && res.models.length > 0) {
        setAvailableModels(res.models);
        // Default to first installed model if available
        const installed = res.models.find((m: ModelProfile) => m.is_installed || m.is_local);
        if (installed && !initialModelId) {
          setSelectedModelId(installed.id);
        }
      }
    }).catch(() => {});
  }, [initialModelId]);

  const selectedModel =
    availableModels.find((m) => m.id === selectedModelId) || availableModels[0] || SAMPLE_MODELS[0];

  const isSelectedModelReady = React.useMemo(() => {
    if (!selectedModel) return true;
    if (selectedModel.id.startsWith('mock-')) return true;
    if (!selectedModel.is_local && !selectedModel.provider?.toLowerCase().includes('ollama')) return true;
    if (!ollamaStatus.reachable) return false;
    const tag = (selectedModel.model_identifier || selectedModel.id).toLowerCase();
    return (
      selectedModel.is_installed ||
      ollamaStatus.availableModels.some(
        (m) => m.toLowerCase() === tag || m.toLowerCase().startsWith(tag) || tag.startsWith(m.toLowerCase())
      )
    );
  }, [selectedModel, ollamaStatus.reachable, ollamaStatus.availableModels]);


  const benchmarksList = [
    {
      id: 'coding_basics',
      name: 'Python Algorithmic Synthesis',
      description: 'Tests function generation, string reversal, palindromes, and recursion.',
      icon: <Code size={16} />,
      cases: 3,
    },
    {
      id: 'structured_json',
      name: 'Constrained JSON Schema Extraction',
      description: 'Verifies entity extraction adhering to strict typed schemas without hallucination.',
      icon: <FileCode size={16} />,
      cases: 3,
    },
    {
      id: 'reasoning_math',
      name: 'Mathematical Word Logic',
      description: 'Multi-step algebraic word problems requiring verified arithmetic deduction.',
      icon: <Zap size={16} />,
      cases: 3,
    },
    {
      id: 'rag_retrieval',
      name: 'Needle-in-a-Haystack Fact Recall',
      description: 'Evaluates precision factual retrieval inside dense contextual documents.',
      icon: <HardDrive size={16} />,
      cases: 2,
    },
  ];

  const handleStartEvaluation = async () => {
    setIsRunning(true);
    setCurrentProgress(10);
    setProgressStatus('Submitting evaluation run to backend...');
    setActiveRunResult(null);
    setRunError(null);

    try {
      const payload = {
        model_id: selectedModel.model_identifier || selectedModel.id,
        provider: selectedModel.is_local ? 'ollama' : (selectedModel.provider ? selectedModel.provider.toLowerCase() : 'ollama'),
        dataset_id: selectedBenchmarkId,
        name: `Eval — ${selectedModel.name} on ${selectedBenchmarkId}`,
        max_cases: sampleLimit,
      };

      setCurrentProgress(20);
      setProgressStatus(`Starting local Ollama inference on ${payload.model_id}...`);

      const runResp = await api.createEvaluation(payload);
      if (!runResp?.id) {
        throw new Error('Backend failed to create evaluation run.');
      }

      // Poll until completed with live progress updates
      const runDetails = await api.pollEvaluation(runResp.id, (pct) => {
        setCurrentProgress(pct);
        setProgressStatus(`Executing test cases (${pct}% complete)...`);
      });

      const rawCases = runDetails.case_results || runDetails.results || [];
      const cases = rawCases.map((c: any) => ({
        case_id: c.case_id,
        prompt: c.prompt,
        expected_output: c.expected_output || '',
        actual_output: c.actual_output || '',
        passed: Boolean(c.passed),
        latency_ms: c.latency_ms !== undefined && c.latency_ms !== null ? Number(c.latency_ms.toFixed(1)) : 0,
        assertion_type: c.assertion_type || (c.metrics && c.metrics._assertion_type) || 'exact_match',
      }));

      const summary = runDetails.summary_metrics || {};
      const avgLat = runDetails.avg_latency_ms !== undefined ? runDetails.avg_latency_ms : summary.avg_latency_ms;
      const medLat = runDetails.median_latency_ms !== undefined ? runDetails.median_latency_ms : (summary.p50_latency_ms ?? summary.median_latency_ms);
      const p95Lat = runDetails.p95_latency_ms !== undefined ? runDetails.p95_latency_ms : summary.p95_latency_ms;
      const tps = runDetails.tokens_per_second !== undefined ? runDetails.tokens_per_second : (summary.avg_tokens_per_second ?? summary.avg_throughput_tok_s);
      const loadMs = runDetails.load_duration_ms !== undefined ? runDetails.load_duration_ms : summary.avg_load_duration_ms;

      const result: EvaluationRun = {
        id: runDetails.id,
        model_id: runDetails.model_id,
        model_name: selectedModel.name,
        benchmark_id: selectedBenchmarkId,
        benchmark_name: benchmarksList.find((b) => b.id === selectedBenchmarkId)?.name || 'Benchmark Suite',
        status: runDetails.status === 'completed' ? 'completed' : 'failed',
        is_demo: false,
        pass_rate: Number((runDetails.pass_rate || 0).toFixed(2)),
        passed_cases: runDetails.passed_cases || 0,
        total_cases: runDetails.total_cases || sampleLimit,
        avg_latency_ms: avgLat !== null && avgLat !== undefined ? Number(avgLat.toFixed(1)) : undefined,
        median_latency_ms: medLat !== null && medLat !== undefined ? Number(medLat.toFixed(1)) : undefined,
        p95_latency_ms: p95Lat !== null && p95Lat !== undefined ? Number(p95Lat.toFixed(1)) : undefined,
        tokens_per_second: tps !== null && tps !== undefined ? Number(tps.toFixed(1)) : undefined,
        load_duration_ms: loadMs !== null && loadMs !== undefined ? Number(loadMs.toFixed(1)) : undefined,
        case_results: cases,
        created_at: runDetails.created_at || new Date().toISOString(),
      };

      setCurrentProgress(100);
      setProgressStatus('Evaluation completed.');
      setActiveRunResult(result);
      setIsRunning(false);
      onSaveToHistory(result);

      if (result.status === 'completed') {
        success('Evaluation Complete', `Tested ${result.total_cases} cases: ${result.passed_cases} passed (${(result.pass_rate * 100).toFixed(0)}%).`);
      } else {
        showError('Evaluation Incomplete', 'Some test cases failed or encountered model timeout.');
      }
    } catch (err: any) {
      setIsRunning(false);
      const errMsg = err.message || 'Execution failed during model inference.';
      setRunError(errMsg);
      showError('Evaluation Failed', errMsg);
    }
  };

  const handleExportJson = () => {
    if (!activeRunResult) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(activeRunResult, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `evalforge20-run-${activeRunResult.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    info('Exported Run JSON', `Saved audit file for ${activeRunResult.model_name}`);
  };

  const handleExportCsv = () => {
    if (!activeRunResult) return;
    const headers = ['case_id', 'status', 'latency_ms', 'assertion_type', 'prompt', 'expected_output', 'actual_output'];
    const rows = (activeRunResult.case_results || []).map((c) => [
      c.case_id,
      c.passed ? 'PASSED' : 'FAILED',
      c.latency_ms,
      `"${c.assertion_type || ''}"`,
      `"${(c.prompt || '').replace(/"/g, '""')}"`,
      `"${(c.expected_output || '').replace(/"/g, '""')}"`,
      `"${(c.actual_output || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', url);
    downloadAnchor.setAttribute('download', `evalforge20-run-${activeRunResult.id}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    info('Exported Run CSV', `Saved CSV file for ${activeRunResult.model_name}`);
  };

  return (
    <div className="py-10 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#41413B]">
        <div className="flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#D9823B]">
            <Terminal size={14} />
            <span>INTERACTIVE TEST RUNNER</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Evaluation Studio
          </h1>
          <p className="text-sm text-[#A6A49D] max-w-xl">
            Execute deterministic test suites against local Ollama models with programmatic
            assertions, response diffing, and latency analysis.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {ollamaStatus.reachable ? (
            <Badge variant="installed" size="md">
              Ollama Online ({ollamaStatus.version || 'Local'}) • {ollamaStatus.installedModels} Models
            </Badge>
          ) : (
            <Badge variant="warning" size="md">
              Ollama Offline • {ollamaStatus.connectivityState.replace(/_/g, ' ')}
            </Badge>
          )}

          {selectedModel && !selectedModel.id.startsWith('mock-') && (
            isSelectedModelReady ? (
              <Badge variant="installed" size="md">
                Model Ready: {selectedModel.model_identifier || selectedModel.id}
              </Badge>
            ) : (
              <Badge variant="warning" size="md">
                Model Missing: Run `ollama pull {selectedModel.model_identifier || selectedModel.id}`
              </Badge>
            )
          )}
        </div>
      </div>

      {runError && (
        <div className="p-4 rounded-2xl bg-[#E26D5C]/10 border border-[#E26D5C]/40 text-[#E26D5C] text-xs flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} />
            <span><strong>Execution Error:</strong> {runError}</span>
          </div>
          <button
            onClick={() => setRunError(null)}
            className="text-xs underline hover:no-underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Studio Configuration Card */}
      <div className="p-6 rounded-3xl bg-[#242522] border border-[#41413B] shadow-md flex flex-col gap-6">
        <h3 className="text-base font-semibold text-[#F5F0E7] flex items-center gap-2">
          <Sparkles size={16} className="text-[#D9823B]" /> Configure Evaluation Workload
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Target Model Selector */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-[#A6A49D]">Target Model</label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="h-11 px-4 rounded-xl bg-[#191A18] border border-[#41413B] text-[#F5F0E7] text-sm outline-none focus:border-[#D9823B] cursor-pointer"
            >
              {availableModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider}) {m.is_local ? '• Ollama' : '• Cloud'}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-2 text-xs font-mono text-[#A6A49D]">
              <span>Architecture: {selectedModel.family}</span>
              <span>•</span>
              <span>Params: {selectedModel.parameter_count}</span>
            </div>
          </div>

          {/* Benchmark Suite Picker */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-[#A6A49D]">Benchmark Suite</label>
            <select
              value={selectedBenchmarkId}
              onChange={(e) => setSelectedBenchmarkId(e.target.value)}
              className="h-11 px-4 rounded-xl bg-[#191A18] border border-[#41413B] text-[#F5F0E7] text-sm outline-none focus:border-[#D9823B] cursor-pointer"
            >
              {benchmarksList.map((bm) => (
                <option key={bm.id} value={bm.id}>
                  {bm.name} ({bm.cases} test cases)
                </option>
              ))}
            </select>
            <span className="text-xs text-[#78766F] truncate">
              {benchmarksList.find((b) => b.id === selectedBenchmarkId)?.description}
            </span>
          </div>

          {/* Test Case Limit & Run Action */}
          <div className="flex flex-col justify-between gap-3">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-[#A6A49D]">Test Sample Limit</label>
              <div className="flex items-center gap-2">
                {[1, 2, 3].map((limit) => (
                  <button
                    key={limit}
                    onClick={() => setSampleLimit(limit)}
                    className={`flex-1 h-11 rounded-xl text-xs font-mono font-medium transition-all cursor-pointer ${
                      sampleLimit === limit
                        ? 'bg-[#D9823B] text-[#191A18] font-bold shadow-sm'
                        : 'bg-[#191A18] text-[#A6A49D] hover:text-[#F5F0E7] border border-[#41413B]'
                    }`}
                  >
                    {limit} {limit === 1 ? 'case' : 'cases'}
                  </button>
                ))}
              </div>
            </div>

            <Button
              size="md"
              variant="primary"
              onClick={handleStartEvaluation}
              loading={isRunning}
              iconLeft={<Play size={14} className="fill-current" />}
              className="w-full justify-center"
            >
              Execute Benchmark Suite
            </Button>
          </div>
        </div>
      </div>

      {/* Running State Indicator */}
      {isRunning && (
        <div className="p-8 rounded-3xl bg-[#242522] border border-[#41413B] flex flex-col items-center text-center gap-4 animate-in fade-in">
          <div className="w-12 h-12 rounded-full bg-[#191A18] border border-[#41413B] flex items-center justify-center text-[#D9823B]">
            <span className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
          </div>
          <h3 className="text-base font-semibold text-[#F5F0E7]">
            Executing Test Suite against {selectedModel.name}...
          </h3>
          <p className="text-xs font-mono text-[#D9823B]">
            {progressStatus || 'Running inference and computing metric assertions...'}
          </p>
          <div className="w-full max-w-md h-2 rounded-full bg-[#191A18] overflow-hidden mt-2">
            <div
              className="h-full bg-gradient-to-r from-[#D9823B] to-[#F5F0E7] transition-all duration-300 rounded-full"
              style={{ width: `${currentProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Active Run Results Display */}
      {activeRunResult && !isRunning && (
        <div className="rounded-3xl bg-[#242522] border border-[#41413B] shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b border-[#41413B] bg-[#191A18]/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="flex flex-col">
              <span className="text-xs font-mono text-[#A6A49D]">
                RUN ID: {activeRunResult.id} • {new Date(activeRunResult.created_at).toLocaleTimeString()}
              </span>
              <h3 className="text-lg font-bold text-[#F5F0E7]">
                {activeRunResult.benchmark_name} — {activeRunResult.model_name}
              </h3>
            </div>

            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant="outline"
                onClick={handleExportJson}
                iconLeft={<Download size={13} />}
              >
                Export JSON
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleExportCsv}
                iconLeft={<Download size={13} />}
              >
                Export CSV
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={handleStartEvaluation}
                iconLeft={<RotateCcw size={13} />}
              >
                Re-run
              </Button>
            </div>
          </div>

          {/* Metric Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-4 p-6 border-b border-[#41413B] bg-[#191A18]/30 font-mono text-xs">
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">Pass Rate</span>
              <span className="text-[#68B587] font-bold text-base">
                {(activeRunResult.pass_rate * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">Passed Cases</span>
              <span className="text-[#F5F0E7] font-bold text-base">
                {activeRunResult.passed_cases} / {activeRunResult.total_cases}
              </span>
            </div>
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">Mean Latency</span>
              <span className="text-[#F5F0E7] font-bold text-base">
                {activeRunResult.avg_latency_ms} ms
              </span>
            </div>
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">P95 Latency</span>
              <span className="text-[#F5F0E7] font-bold text-base">
                {activeRunResult.p95_latency_ms !== undefined ? `${activeRunResult.p95_latency_ms} ms` : '—'}
              </span>
            </div>
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">Generation Speed</span>
              <span className="text-[#D9823B] font-bold text-base">
                {activeRunResult.tokens_per_second !== undefined ? `${activeRunResult.tokens_per_second} tok/s` : '—'}
              </span>
            </div>
            <div>
              <span className="text-[#A6A49D] block text-[11px] mb-1">Status</span>
              <span className={`font-semibold uppercase flex items-center gap-1 ${
                activeRunResult.status === 'completed' ? 'text-[#68B587]' : 'text-[#E26D5C]'
              }`}>
                {activeRunResult.status === 'completed' ? (
                  <><CheckCircle2 size={14} /> Completed</>
                ) : (
                  <><XCircle size={14} /> Failed</>
                )}
              </span>
            </div>
          </div>

          {/* Graphical Representation of Performance, Accuracy & Capability Radar */}
          <div className="p-6 border-b border-[#41413B] bg-[#191A18]/40">
            <EvaluationResultCharts run={activeRunResult} />
          </div>

          {/* Test Case Inspection List */}
          <div className="p-6 flex flex-col gap-4">

            <span className="text-xs font-mono uppercase tracking-wider text-[#A6A49D]">
              Individual Case Breakdown ({activeRunResult.case_results.length})
            </span>

            <div className="flex flex-col gap-4">
              {activeRunResult.case_results.map((c, i) => (
                <div
                  key={c.case_id}
                  className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-4 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[#D9823B] font-semibold">
                        Case {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className="font-mono text-[#A6A49D]">({c.case_id})</span>
                      <span className="text-[10px] text-[#A6A49D] font-mono px-2 py-0.5 rounded bg-[#242522]">
                        {c.assertion_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="font-mono text-[#A6A49D]">{c.latency_ms} ms</span>
                      <Badge variant={c.passed ? "installed" : "error"} size="sm">
                        {c.passed ? 'PASSED' : 'FAILED'}
                      </Badge>
                    </div>
                  </div>

                  {/* Prompt */}
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-mono text-[#78766F]">Prompt:</span>
                    <pre className="font-mono text-xs text-[#F5F0E7] bg-[#242522] p-3 rounded-xl border border-[#41413B]/60 whitespace-pre-wrap leading-relaxed">
                      {c.prompt}
                    </pre>
                  </div>

                  {/* Expected vs Actual Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1.5">
                      <span className="text-[11px] font-mono text-[#78766F]">
                        Expected Standard Output:
                      </span>
                      <pre className="font-mono text-xs text-[#A6A49D] bg-[#242522] p-3 rounded-xl border border-[#41413B]/60 whitespace-pre-wrap">
                        {c.expected_output}
                      </pre>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <span className="text-[11px] font-mono text-[#68B587]">
                        Actual Model Response:
                      </span>
                      <pre className="font-mono text-xs text-[#68B587] bg-[#242522] p-3 rounded-xl border border-[#41413B]/60 whitespace-pre-wrap">
                        {c.actual_output}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Action Footer */}
          <div className="p-4 bg-[#191A18]/80 border-t border-[#41413B] flex items-center justify-between text-xs text-[#A6A49D]">
            <span>This run has been saved to your local audit history.</span>
            <button
              onClick={() => onRouteChange('history')}
              className="text-[#D9823B] hover:underline font-medium cursor-pointer"
            >
              View All Past Runs in History &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
