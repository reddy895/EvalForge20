import React, { useState } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  BarChart3,
  Grid3X3,
  ListFilter,
  ArrowLeft,
  Loader2,
  GitCompare,
} from 'lucide-react';
import { useEvaluationResults } from '../hooks/useEvaluationResults';
import { TestCaseResult } from '../types/evaluationResults';
import { EvaluationSummaryHeader } from '../components/results/EvaluationSummaryHeader';
import { LiveExecutionBanner } from '../components/results/LiveExecutionBanner';
import { AccuracyComparisonChart } from '../components/results/AccuracyComparisonChart';
import { ExactMatchComparisonChart } from '../components/results/ExactMatchComparisonChart';
import { LatencyComparisonChart } from '../components/results/LatencyComparisonChart';
import { ThroughputComparisonChart } from '../components/results/ThroughputComparisonChart';
import { GroupedMetricComparisonChart } from '../components/results/GroupedMetricComparisonChart';
import { EvaluationDistributionChart } from '../components/results/EvaluationDistributionChart';
import { MultiModelComparisonTable } from '../components/results/MultiModelComparisonTable';
import { TestCasePerformanceMatrix } from '../components/results/TestCasePerformanceMatrix';
import { TestCaseExplorer } from '../components/results/TestCaseExplorer';
import { TestCaseDetailModal } from '../components/results/TestCaseDetailModal';

interface EvaluationResultsWorkspaceProps {
  runId?: string | null;
  onBackToPlayground?: () => void;
}

type TabKey = 'all' | 'charts' | 'matrix' | 'cases';

export const EvaluationResultsWorkspace: React.FC<EvaluationResultsWorkspaceProps> = ({
  runId,
  onBackToPlayground = () => window.history.back(),
}) => {
  const [activeTab, setActiveTab] = useState<TabKey>('all');
  const [selectedCase, setSelectedCase] = useState<TestCaseResult | null>(null);

  const {
    data,
    loading,
    error,
    isLive,
    progress,
    refresh,
    cancel,
  } = useEvaluationResults(runId);

  // Loading state
  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-slate-800">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col items-center max-w-md w-full text-center">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
          <h2 className="text-lg font-semibold text-slate-900">Loading Evaluation Results</h2>
          <p className="text-xs text-slate-500 mt-1 mb-6">
            Fetching benchmark metrics, test cases, and model telemetry for run:
          </p>
          <div className="font-mono text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 break-all w-full">
            {runId || 'Initializing...'}
          </div>
          <button
            onClick={onBackToPlayground}
            className="mt-6 inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 font-medium"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Playground
          </button>
        </div>
      </div>
    );
  }

  // Error state without data
  if (error && !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-slate-800">
        <div className="bg-white p-8 rounded-2xl border border-rose-200 shadow-sm flex flex-col items-center max-w-md w-full text-center">
          <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-semibold text-slate-900">Failed to Load Run</h2>
          <p className="text-xs text-rose-600 mt-2 mb-6 bg-rose-50 p-3 rounded-lg border border-rose-100 w-full text-left break-words">
            {error}
          </p>
          <div className="flex items-center gap-3 w-full">
            <button
              onClick={refresh}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
            <button
              onClick={onBackToPlayground}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Return
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Empty state when no data and not loading
  if (!data) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-slate-800">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col items-center max-w-md w-full text-center">
          <BarChart3 className="w-12 h-12 text-slate-300 mb-3" />
          <h2 className="text-base font-semibold text-slate-800">No Evaluation Data Found</h2>
          <p className="text-xs text-slate-500 mt-1 mb-6">
            The requested evaluation run could not be found or has not yielded results.
          </p>
          <button
            onClick={onBackToPlayground}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Playground
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans pb-16">
      {/* Top Header */}
      <EvaluationSummaryHeader
        data={data}
        isLive={isLive}
        onBackToPlayground={onBackToPlayground}
        onRefresh={refresh}
        onCancel={cancel}
      />

      {/* Main Container */}
      <main className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
        {/* Live Execution Stream Banner */}
        <LiveExecutionBanner progress={progress} isLive={isLive} />

        {/* View Section Tabs */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <div className="flex items-center gap-2 bg-slate-200/70 p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('all')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'all'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Full Analytics
            </button>
            <button
              onClick={() => setActiveTab('charts')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'charts'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <GitCompare className="w-3.5 h-3.5" />
              Charts & Comparison
            </button>
            <button
              onClick={() => setActiveTab('matrix')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'matrix'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Grid3X3 className="w-3.5 h-3.5" />
              Case Matrix
            </button>
            <button
              onClick={() => setActiveTab('cases')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'cases'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              Case Explorer
              <span className="ml-1 text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full font-mono">
                {data.case_results.length}
              </span>
            </button>
          </div>

          <div className="text-xs text-slate-500 hidden sm:block">
            {data.models.length} model{data.models.length !== 1 ? 's' : ''} &bull; {data.total_cases} test cases
          </div>
        </div>

        {/* Charts Grid */}
        {(activeTab === 'all' || activeTab === 'charts') && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Accuracy Comparison */}
              <AccuracyComparisonChart modelSummaries={data.model_summaries} />

              {/* Exact-Match Comparison */}
              <ExactMatchComparisonChart modelSummaries={data.model_summaries} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Latency Comparison (ms) */}
              <LatencyComparisonChart modelSummaries={data.model_summaries} />

              {/* Throughput Comparison (tok/s) */}
              <ThroughputComparisonChart modelSummaries={data.model_summaries} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Grouped Metric Comparison */}
              <GroupedMetricComparisonChart
                modelSummaries={data.model_summaries}
                evaluators={data.evaluators}
              />

              {/* Evaluation Outcome Distribution */}
              <EvaluationDistributionChart
                distribution={data.distribution}
                totalCases={data.total_cases}
              />
            </div>

            {/* Multi-Model Comparison Scorecard & Disagreements */}
            <MultiModelComparisonTable
              modelSummaries={data.model_summaries}
              disagreements={data.disagreements}
            />
          </div>
        )}

        {/* Per-Test-Case Heatmap Matrix */}
        {(activeTab === 'all' || activeTab === 'matrix') && (
          <div className="pt-2">
            <TestCasePerformanceMatrix
              modelSummaries={data.model_summaries}
              cases={data.case_results}
              onSelectCase={(c) => setSelectedCase(c)}
            />
          </div>
        )}

        {/* Individual Test-Case Explorer */}
        {(activeTab === 'all' || activeTab === 'cases') && (
          <div className="pt-2">
            <TestCaseExplorer
              cases={data.case_results}
              models={data.models}
              evaluators={data.evaluators}
              onSelectCase={(c) => setSelectedCase(c)}
            />
          </div>
        )}
      </main>

      {/* Test Case Detail Inspection Modal */}
      {selectedCase && (
        <TestCaseDetailModal
          testCase={selectedCase}
          onClose={() => setSelectedCase(null)}
        />
      )}
    </div>
  );
};
export default EvaluationResultsWorkspace;

