import React, { useEffect, useState } from 'react';
import { GitCompare, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary, ComparisonResult } from '../api/types';
import { Button } from '../components/ui/Button';
import { CompareSelector } from '../components/compare/CompareSelector';
import { CompareMetricsTable } from '../components/compare/CompareMetricsTable';
import { RegressionInspector } from '../components/compare/RegressionInspector';

export const ComparePage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [baselineId, setBaselineId] = useState<string>('');
  const [candidateId, setCandidateId] = useState<string>('');
  const [allowDifferentDatasets, setAllowDifferentDatasets] = useState<boolean>(false);

  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRunsAndCompare = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listEvaluations({ limit: 100 });
      setRuns(data);

      if (data.length >= 2) {
        const base = data[0].run_id;
        const cand = data[1].run_id;
        setBaselineId(base);
        setCandidateId(cand);
        executeComparison(base, cand, false);
      } else if (data.length === 1) {
        setBaselineId(data[0].run_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to list evaluation runs');
    } finally {
      setIsLoading(false);
    }
  };

  const executeComparison = async (base: string, cand: string, allowDiff: boolean) => {
    if (!base || !cand || base === cand) {
      setComparison(null);
      return;
    }

    setIsComparing(true);
    setError(null);
    try {
      const res = await api.compareRuns({
        baseline_run_id: base,
        candidate_run_id: cand,
        allow_different_datasets: allowDiff,
      });
      setComparison(res);
    } catch (err: any) {
      setComparison(null);
      setError(err.message || 'Failed to generate evaluation run comparison');
    } finally {
      setIsComparing(false);
    }
  };

  useEffect(() => {
    fetchRunsAndCompare();
  }, []);

  const handleBaselineChange = (id: string) => {
    setBaselineId(id);
    executeComparison(id, candidateId, allowDifferentDatasets);
  };

  const handleCandidateChange = (id: string) => {
    setCandidateId(id);
    executeComparison(baselineId, id, allowDifferentDatasets);
  };

  const handleToggleAllowDiff = (allow: boolean) => {
    setAllowDifferentDatasets(allow);
    executeComparison(baselineId, candidateId, allow);
  };

  return (
    <div className="compare-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Compare Runs & Regression Analysis</h1>
          <p className="page-header-subtitle">
            Benchmark two model evaluations head-to-head, measure score and latency deltas, and inspect case disagreements.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading || isComparing}
            onClick={() => executeComparison(baselineId, candidateId, allowDifferentDatasets)}
          >
            Re-compare
          </Button>
        </div>
      </div>

      {runs.length < 2 ? (
        <div
          style={{
            padding: 'var(--space-2xl)',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-xs)',
            textAlign: 'center',
          }}
        >
          <GitCompare size={32} style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-sm)' }} />
          <div style={{ fontWeight: 600 }}>At least two evaluation runs are required to compare</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)', marginTop: '4px' }}>
            Run at least two benchmarks against different models or configurations to inspect regression metrics.
          </p>
        </div>
      ) : (
        <>
          <CompareSelector
            runs={runs}
            baselineId={baselineId}
            candidateId={candidateId}
            onBaselineChange={handleBaselineChange}
            onCandidateChange={handleCandidateChange}
            allowDifferentDatasets={allowDifferentDatasets}
            onToggleAllowDifferentDatasets={handleToggleAllowDiff}
            isCompatible={!error || !error.includes('dataset')}
          />

          {error && (
            <div className="toast-item error" style={{ marginBottom: 'var(--space-md)' }} role="alert">
              <AlertCircle size={15} className="toast-icon" />
              <div className="toast-content">
                <div className="toast-title">Comparison Incompatible</div>
                <div className="toast-message">{error}</div>
              </div>
            </div>
          )}

          {isComparing ? (
            <div style={{ padding: 'var(--space-2xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
              Calculating comparative metric matrix and regression deltas...
            </div>
          ) : (
            comparison && (
              <>
                <CompareMetricsTable comparison={comparison} />
                <RegressionInspector comparison={comparison} />
              </>
            )
          )}
        </>
      )}
    </div>
  );
};
