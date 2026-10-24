import React, { useState } from 'react';
import { simulateEvaluationRun } from '../../data/benchmarks';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Play, CheckCircle2, Terminal, ArrowRight, Zap, Code, FileCode } from 'lucide-react';
import { NavRoute, EvaluationRun } from '../../types';

interface EvaluationPreviewSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const EvaluationPreviewSection: React.FC<EvaluationPreviewSectionProps> = ({
  onRouteChange,
}) => {
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>('coding_basics');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<EvaluationRun>(() =>
    simulateEvaluationRun('qwen-2.5-7b-instruct', 'Qwen 2.5 7B Instruct', 'coding_basics', 3)
  );

  const handleRunEvaluation = () => {
    setIsRunning(true);
    setTimeout(() => {
      const result = simulateEvaluationRun(
        'qwen-2.5-7b-instruct',
        'Qwen 2.5 7B Instruct',
        selectedBenchmark,
        3
      );
      setRunResult(result);
      setIsRunning(false);
    }, 700);
  };

  const benchmarksList = [
    { id: 'coding_basics', name: 'Python Coding Basics', icon: <Code size={14} /> },
    { id: 'structured_json', name: 'JSON Schema Extraction', icon: <FileCode size={14} /> },
    { id: 'reasoning_math', name: 'Mathematical Word Logic', icon: <Zap size={14} /> },
  ];

  return (
    <section id="evaluation" className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full">
      <div className="w-full max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#D9823B]">
            <Terminal size={14} />
            <span>TEST SUITE EXECUTION</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Live Test Case Runner
          </h2>
          <p className="text-sm sm:text-base text-[#A6A49D] max-w-xl">
            Run deterministic validation test cases against prompt suites with programmatic
            assertions, response diffing, and millisecond latency timers.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => onRouteChange('evaluate')}
          iconRight={<ArrowRight size={14} />}
        >
          Launch Full Studio Workspace
        </Button>
      </div>

      {/* Main Runner Card */}
      <div className="rounded-3xl bg-[#242522] border border-[#41413B] shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden">
        {/* Top Control Bar */}
        <div className="p-6 border-b border-[#41413B] bg-[#191A18]/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#A6A49D] font-mono mr-1">Workload:</span>
            {benchmarksList.map((bm) => (
              <button
                key={bm.id}
                onClick={() => {
                  setSelectedBenchmark(bm.id);
                  const result = simulateEvaluationRun(
                    'qwen-2.5-7b-instruct',
                    'Qwen 2.5 7B Instruct',
                    bm.id,
                    3
                  );
                  setRunResult(result);
                }}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  selectedBenchmark === bm.id
                    ? 'bg-[#242522] text-[#F5F0E7] border border-[#D9823B] shadow-sm'
                    : 'bg-[#191A18] text-[#A6A49D] hover:text-[#F5F0E7] border border-[#41413B]'
                }`}
              >
                <span className={selectedBenchmark === bm.id ? 'text-[#D9823B]' : 'text-[#78766F]'}>
                  {bm.icon}
                </span>
                <span>{bm.name}</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="demo" size="md">
              Demo Mode
            </Badge>
            <Button
              size="sm"
              variant="primary"
              onClick={handleRunEvaluation}
              loading={isRunning}
              iconLeft={<Play size={13} className="fill-current" />}
            >
              Run Benchmark Suite
            </Button>
          </div>
        </div>

        {/* Results Overview Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 border-b border-[#41413B] bg-[#191A18]/30 font-mono text-xs">
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1">Target Model</span>
            <span className="text-[#F5F0E7] font-semibold">Qwen 2.5 7B Instruct</span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1">Pass Rate</span>
            <span className="text-[#68B587] font-bold text-sm">
              {(runResult.pass_rate * 100).toFixed(0)}% ({runResult.passed_cases}/{runResult.total_cases})
            </span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1">Average Latency</span>
            <span className="text-[#F5F0E7] font-semibold">{runResult.avg_latency_ms} ms</span>
          </div>
          <div>
            <span className="text-[#A6A49D] block text-[11px] mb-1">Status</span>
            <span className="text-[#68B587] font-semibold uppercase flex items-center gap-1">
              <CheckCircle2 size={13} /> Completed
            </span>
          </div>
        </div>

        {/* Case Results List */}
        <div className="p-6 flex flex-col gap-4">
          <span className="text-xs font-mono uppercase tracking-wider text-[#A6A49D]">
            Case-Level Execution Trace
          </span>

          <div className="flex flex-col gap-3">
            {runResult.case_results.map((caseItem, idx) => (
              <div
                key={caseItem.case_id}
                className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-3 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[#D9823B] font-semibold">
                      #{String(idx + 1).padStart(2, '0')}
                    </span>
                    <span className="font-mono text-[#F5F0E7] font-medium">{caseItem.case_id}</span>
                    <span className="text-[10px] text-[#A6A49D] font-mono px-2 py-0.5 rounded bg-[#242522]">
                      {caseItem.assertion_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[#A6A49D]">{caseItem.latency_ms} ms</span>
                    <Badge variant="installed" size="sm">
                      PASSED
                    </Badge>
                  </div>
                </div>

                <div className="flex flex-col gap-1 text-[#A6A49D]">
                  <span className="text-[11px] text-[#78766F] font-mono">Input Prompt:</span>
                  <p className="font-mono text-[#F5F0E7]/90 bg-[#242522] p-2.5 rounded-xl border border-[#41413B]/60 leading-relaxed whitespace-pre-wrap">
                    {caseItem.prompt}
                  </p>
                </div>

                <div className="flex flex-col gap-1">
                  <span className="text-[11px] text-[#78766F] font-mono">Actual Response:</span>
                  <pre className="font-mono text-xs text-[#68B587] bg-[#242522] p-2.5 rounded-xl border border-[#41413B]/60 overflow-x-auto whitespace-pre-wrap">
                    {caseItem.actual_output}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Banner inside runner */}
        <div className="p-4 bg-[#191A18]/80 border-t border-[#41413B] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#A6A49D]">
          <span className="flex items-center gap-2">
            <Zap size={14} className="text-[#D9823B]" />
            Connect your local Ollama instance to test with your custom weights and dataset files.
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onRouteChange('evaluate')}
            iconRight={<ArrowRight size={13} />}
          >
            Open Test Studio
          </Button>
        </div>
      </div>
      </div>
    </section>
  );
};
