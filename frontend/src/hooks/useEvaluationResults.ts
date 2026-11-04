import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import {
  EvaluationResultsData,
  LiveExecutionProgress,
  TestCaseResult,
} from '../types/evaluationResults';

interface UseEvaluationResultsReturn {
  data: EvaluationResultsData | null;
  loading: boolean;
  error: string | null;
  isLive: boolean;
  progress: LiveExecutionProgress;
  refresh: () => Promise<void>;
  cancel: () => Promise<void>;
}

export function useEvaluationResults(runId?: string | null): UseEvaluationResultsReturn {
  const [data, setData] = useState<EvaluationResultsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);

  const [progress, setProgress] = useState<LiveExecutionProgress>({
    stage: 'Initializing evaluation...',
    completed_steps: 0,
    total_steps: 0,
    progress_percentage: 0,
    elapsed_time_seconds: 0,
    logs: [],
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  const fetchResults = useCallback(async (id: string) => {
    try {
      const res = await api.getExecutionResults(id);
      setData(res);
      setError(null);
      return res;
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve evaluation results.');
      throw err;
    }
  }, []);

  const handleCancel = useCallback(async () => {
    if (!runId) return;
    try {
      await api.cancelExecution(runId);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      setIsLive(false);
      setProgress((prev) => ({
        ...prev,
        stage: 'Evaluation cancelled by user.',
        logs: [...prev.logs, 'Cancellation requested.'],
      }));
      await fetchResults(runId);
    } catch (err: any) {
      console.warn('Failed to cancel evaluation:', err);
    }
  }, [runId, fetchResults]);

  useEffect(() => {
    if (!runId) {
      setData(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    startTimeRef.current = Date.now();

    // Elapsed timer
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setProgress((prev) => ({
        ...prev,
        elapsed_time_seconds: Math.floor((Date.now() - startTimeRef.current) / 1000),
      }));
    }, 1000);

    let isMounted = true;

    // Initial load
    fetchResults(runId)
      .then((initialData) => {
        if (!isMounted) return;
        setLoading(false);

        const statusUpper = (initialData.status || '').toUpperCase();
        const isTerminal = ['COMPLETED', 'FAILED', 'CANCELLED'].includes(statusUpper);

        if (isTerminal) {
          setIsLive(false);
          if (timerRef.current) clearInterval(timerRef.current);
          return;
        }

        // Connect SSE if running
        setIsLive(true);
        connectSSE(runId);
      })
      .catch(() => {
        if (!isMounted) return;
        setLoading(false);
        // Even if initial fetch failed (e.g. still initializing in DB), try SSE
        setIsLive(true);
        connectSSE(runId);
      });

    function connectSSE(id: string) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      try {
        const es = api.createExecutionEventSource(id);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const payload = JSON.parse(event.data);
            const evType: string = payload.event_type || payload.type || '';

            if (evType === 'started') {
              setProgress((prev) => ({
                ...prev,
                stage: payload.message || 'Workflow execution started.',
                total_steps: payload.total_steps || prev.total_steps,
                logs: [...prev.logs, payload.message || 'Started execution.'],
              }));
            } else if (evType === 'step_progress') {
              const completed = payload.completed_steps ?? 0;
              const total = payload.total_steps ?? 1;
              const pct = payload.progress_percentage ?? Math.round((completed / total) * 100);
              const modelId = payload.data?.model;
              const newCase = payload.data?.case;

              setProgress((prev) => ({
                ...prev,
                stage: payload.message || `Processing test case ${completed}/${total}...`,
                current_model: modelId || prev.current_model,
                completed_steps: completed,
                total_steps: total,
                progress_percentage: pct,
                logs: payload.message ? [...prev.logs, payload.message] : prev.logs,
              }));

              if (newCase) {
                setData((prevData) => {
                  if (!prevData) return prevData;
                  const existing = prevData.case_results || [];
                  const exists = existing.some(
                    (c) => c.case_id === newCase.case_id && c.model_id === modelId
                  );
                  if (exists) return prevData;

                  const formattedCase: TestCaseResult = {
                    case_id: String(newCase.case_id || newCase.case_index || existing.length + 1),
                    case_index: newCase.case_index,
                    model_id: modelId || prevData.models[0] || 'model',
                    prompt: newCase.prompt,
                    expected_output: newCase.expected_output,
                    actual_output: newCase.actual_output,
                    passed: Boolean(newCase.passed),
                    latency_ms: newCase.latency_ms,
                    tokens_per_second: newCase.tokens_per_second,
                    evaluators: newCase.evaluators,
                    metrics: newCase.metrics,
                    error_message: newCase.error_message,
                  };

                  return {
                    ...prevData,
                    completed_cases: completed,
                    total_cases: total,
                    case_results: [...existing, formattedCase],
                  };
                });
              }
            } else if (evType === 'completed') {
              es.close();
              setIsLive(false);
              if (timerRef.current) clearInterval(timerRef.current);
              setProgress((prev) => ({
                ...prev,
                stage: 'Evaluation completed successfully.',
                progress_percentage: 100,
                logs: [...prev.logs, 'Completed.'],
              }));
              fetchResults(id).catch(() => {});
            } else if (evType === 'failed') {
              es.close();
              setIsLive(false);
              if (timerRef.current) clearInterval(timerRef.current);
              setProgress((prev) => ({
                ...prev,
                stage: `Evaluation failed: ${payload.message || 'Unknown error'}`,
                error: payload.message,
                logs: [...prev.logs, `Failed: ${payload.message}`],
              }));
              fetchResults(id).catch(() => {});
            } else if (evType === 'cancelled') {
              es.close();
              setIsLive(false);
              if (timerRef.current) clearInterval(timerRef.current);
              setProgress((prev) => ({
                ...prev,
                stage: 'Evaluation was cancelled.',
                logs: [...prev.logs, 'Cancelled.'],
              }));
              fetchResults(id).catch(() => {});
            }
          } catch (e) {
            console.error('SSE JSON error', e);
          }
        };

        es.onerror = () => {
          // If SSE connection disconnects or ends, fetch latest DB state
          if (es.readyState === EventSource.CLOSED) {
            setIsLive(false);
            if (timerRef.current) clearInterval(timerRef.current);
            fetchResults(id).catch(() => {});
          }
        };
      } catch {
        // Fallback to polling
        pollFallback(id);
      }
    }

    async function pollFallback(id: string) {
      const pollTimer = setInterval(async () => {
        if (!isMounted) return;
        try {
          const res = await api.getExecutionResults(id);
          setData(res);
          const st = (res.status || '').toUpperCase();
          if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(st)) {
            clearInterval(pollTimer);
            setIsLive(false);
            if (timerRef.current) clearInterval(timerRef.current);
          }
        } catch {
          // retry
        }
      }, 1500);
    }

    return () => {
      isMounted = false;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [runId, fetchResults]);

  const refresh = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    try {
      await fetchResults(runId);
    } finally {
      setLoading(false);
    }
  }, [runId, fetchResults]);

  return {
    data,
    loading,
    error,
    isLive,
    progress,
    refresh,
    cancel: handleCancel,
  };
}

