import React, { useEffect, useState } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { RunDetailResponse, CaseResult } from '../api/types';
import { type NavRoute } from '../types/navigation';
import { Button } from '../components/ui/Button';
import { Breadcrumbs } from '../components/shell/Breadcrumbs';
import { RunDetailHeader } from '../components/runs/RunDetailHeader';
import { RunMetricsBreakdown } from '../components/runs/RunMetricsBreakdown';
import { CaseResultsTable } from '../components/runs/CaseResultsTable';

interface RunDetailPageProps {
  runId: string;
  onNavigate: (route: NavRoute, runId?: string) => void;
}

export const RunDetailPage: React.FC<RunDetailPageProps> = ({ runId, onNavigate }) => {
  const [data, setData] = useState<RunDetailResponse | null>(null);
  const [cases, setCases] = useState<CaseResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRunDetails = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [detailRes, casesRes] = await Promise.all([
        api.getEvaluation(runId),
        api.getCaseResults(runId, 200, 0),
      ]);
      setData(detailRes);
      setCases(casesRes);
    } catch (err: any) {
      setError(err.message || `Failed to fetch run details for '${runId}'`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRunDetails();
  }, [runId]);

  return (
    <div className="run-detail-page">
      <div className="flex-between" style={{ marginBottom: 'var(--space-xs)' }}>
        <Breadcrumbs
          items={[
            { label: 'Evaluation Runs', route: 'runs' },
            { label: runId },
          ]}
          onRouteChange={onNavigate}
        />
        <div className="flex-row gap-xs">
          <Button
            variant="outline"
            size="sm"
            iconLeft={<ArrowLeft size={13} />}
            onClick={() => onNavigate('runs')}
          >
            Back to Runs
          </Button>
          <Button
            variant="outline"
            size="sm"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchRunDetails}
          >
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" style={{ marginBottom: 'var(--space-md)' }} role="alert">
          <div className="toast-content">
            <div className="toast-title">Unable to Load Run</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      {data && (
        <>
          <RunDetailHeader data={data} />
          <RunMetricsBreakdown aggregates={data.aggregates} />
          <CaseResultsTable cases={cases} isLoading={isLoading} />
        </>
      )}
    </div>
  );
};
