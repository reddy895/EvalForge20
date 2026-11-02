import React, { useState, useEffect, useCallback } from 'react';
import {
  Node,
  Edge,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Connection,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
} from '@xyflow/react';
import { NodeLibrarySidebar } from '../components/canvas/NodeLibrarySidebar';
import { CanvasWorkspace } from '../components/canvas/CanvasWorkspace';
import { NodeConfigPanel } from '../components/canvas/NodeConfigPanel';
import { TopToolbar } from '../components/canvas/TopToolbar';
import { ResultsPanel } from '../components/results/ResultsPanel';
import { OllamaBanner } from '../components/canvas/OllamaBanner';
import { serializeEvaluationGraph } from '../utils/graphSerialization';

const INITIAL_NODES: Node[] = [
  {
    id: 'benchmark-1',
    type: 'benchmark',
    position: { x: 50, y: 150 },
    data: {
      id: 'general-knowledge-mini',
      name: 'General Knowledge Mini',
      category: 'General Knowledge',
      sample_count: 4,
    },
  },
  {
    id: 'model-1',
    type: 'model',
    position: { x: 380, y: 150 },
    data: {
      id: 'qwen2.5:1.5b',
      name: 'Qwen 2.5 1.5B',
      model_identifier: 'qwen2.5:1.5b',
      temperature: 0.1,
      max_tokens: 256,
      timeout_seconds: 30,
    },
  },
  {
    id: 'evaluator-1',
    type: 'evaluator',
    position: { x: 720, y: 150 },
    data: {
      evaluator_id: 'exact_match',
      name: 'Exact Match Accuracy',
      category: 'Accuracy',
      required_inputs: ['output', 'expected_output'],
    },
  },
];

const INITIAL_EDGES: Edge[] = [
  {
    id: 'e1-2',
    source: 'benchmark-1',
    target: 'model-1',
    animated: true,
    style: { stroke: '#2563EB', strokeWidth: 2 },
  },
  {
    id: 'e2-3',
    source: 'model-1',
    target: 'evaluator-1',
    animated: true,
    style: { stroke: '#2563EB', strokeWidth: 2 },
  },
];

/** Validate the canvas graph client-side before submitting. Returns null if valid or an error message. */
function validateGraph(nodes: Node[], edges: Edge[]): string | null {
  const models = nodes.filter((n) => n.type === 'model');
  const datasets = nodes.filter((n) => n.type === 'dataset' || n.type === 'benchmark');
  const evaluators = nodes.filter((n) => n.type === 'evaluator');

  if (models.length === 0) return 'Add at least one Model node to the canvas.';
  if (datasets.length === 0) return 'Add at least one Dataset or Benchmark node.';
  if (evaluators.length === 0) return 'Add at least one Evaluator node.';

  // Check that each model has a dataset incoming and an evaluator outgoing
  for (const m of models) {
    const hasDataset = edges.some(
      (e) => e.target === m.id && datasets.some((d) => d.id === e.source)
    );
    const hasEvaluator = edges.some(
      (e) => e.source === m.id && evaluators.some((ev) => ev.id === e.target)
    );
    if (!hasDataset) {
      const name = (m.data.name as string) || m.id;
      return `Model "${name}" is not connected to a Dataset or Benchmark.`;
    }
    if (!hasEvaluator) {
      const name = (m.data.name as string) || m.id;
      return `Model "${name}" is not connected to an Evaluator.`;
    }
  }

  return null;
}

export const PlaygroundView: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<Edge[]>(INITIAL_EDGES);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [workflowName, setWorkflowName] = useState<string>('Local Model Reasoning Benchmark');

  // Metadata lists
  const [installedModels, setInstalledModels] = useState<any[]>([]);
  const [benchmarkSuites, setBenchmarkSuites] = useState<any[]>([]);
  const [evaluatorsList, setEvaluatorsList] = useState<any[]>([]);

  // Ollama provider status
  const [ollamaStatus, setOllamaStatus] = useState<{
    reachable: boolean;
    checked: boolean;
    models: string[];
    error?: string;
  }>({ reachable: false, checked: false, models: [] });

  // Execution states
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationStatus, setValidationStatus] = useState<{
    isValid: boolean;
    message?: string;
  } | null>(null);
  const [progressPercentage, setProgressPercentage] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<number>(0);
  const [totalSteps, setTotalSteps] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [cases, setCases] = useState<any[]>([]);

  /** Check Ollama health and retrieve installed models. */
  const checkOllamaStatus = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/ollama/status');
      if (!res.ok) {
        setOllamaStatus({ reachable: false, checked: true, models: [], error: `HTTP ${res.status}` });
        return;
      }
      const data = await res.json();
      setOllamaStatus({
        reachable: data.is_healthy === true,
        checked: true,
        models: (data.models || []).map((m: any) => m.name || m.model_identifier || m.id || ''),
        error: data.is_healthy ? undefined : 'Ollama is not reachable at localhost:11434',
      });
      if (data.models && data.models.length > 0) {
        setInstalledModels(data.models);
      }
    } catch {
      setOllamaStatus({
        reachable: false,
        checked: true,
        models: [],
        error: 'Could not reach the backend health endpoint.',
      });
    }
  }, []);

  // Fetch models, benchmarks, evaluators from backend API
  useEffect(() => {
    checkOllamaStatus();

    fetch('http://localhost:8000/api/models')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.models) setInstalledModels(data.models);
      })
      .catch(() => {});

    fetch('http://localhost:8000/api/benchmarks')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.benchmarks) setBenchmarkSuites(data.benchmarks);
      })
      .catch(() => {});

    fetch('http://localhost:8000/api/evaluators')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.evaluators) setEvaluatorsList(data.evaluators);
      })
      .catch(() => {});
  }, [checkOllamaStatus]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect: OnConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated: true,
            style: { stroke: '#2563EB', strokeWidth: 2 },
          },
          eds
        )
      ),
    []
  );

  const onNodeClick = useCallback((node: Node) => {
    setSelectedNode(node);
  }, []);

  const onDropItem = useCallback(
    (type: string, data: any, position: { x: number; y: number }) => {
      const newNodeId = `${type}-${Date.now().toString().slice(-4)}`;
      const newNode: Node = {
        id: newNodeId,
        type,
        position,
        data: { ...data },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    []
  );

  const handleUpdateNodeData = (nodeId: string, newData: any) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...newData } } : n))
    );
    if (selectedNode && selectedNode.id === nodeId) {
      setSelectedNode((prev) => (prev ? { ...prev, data: { ...prev.data, ...newData } } : null));
    }
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    if (selectedNode && selectedNode.id === nodeId) {
      setSelectedNode(null);
    }
  };

  const handleValidate = async () => {
    setIsValidating(true);
    setValidationStatus(null);

    // Client-side validation first
    const clientError = validateGraph(nodes, edges);
    if (clientError) {
      setValidationStatus({ isValid: false, message: clientError });
      setIsValidating(false);
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/api/workflows/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: nodes.map((n) => ({
            id: n.id,
            type: n.type,
            name: (n.data.name as string) || n.id,
            category: (n.data.category as string) || '',
            config: n.data,
          })),
          edges: edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
          })),
        }),
      });
      const data = await res.json();
      setValidationStatus({
        isValid: data.is_valid,
        message: data.is_valid
          ? `Valid workflow: ${data.executable_models?.length || 1} model(s), ${data.executable_evaluators?.length || 1} metric(s)`
          : (data.errors && data.errors[0]?.message) || 'Validation failed',
      });
    } catch {
      setValidationStatus({
        isValid: false,
        message: 'Could not connect to backend validator',
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    try {
      const serialized = serializeEvaluationGraph(nodes, edges, workflowName);
      await fetch('http://localhost:8000/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName,
          graph: serialized.workflow_graph,
        }),
      });
      alert('Workflow saved successfully!');
    } catch {
      alert('Failed to save workflow.');
    }
  };

  const handleCancelEvaluation = async () => {
    if (!activeExecutionId) return;
    try {
      await fetch(`http://localhost:8000/api/executions/${activeExecutionId}/cancel`, {
        method: 'POST',
      });
      setLogs((prev) => [...prev, 'Cancellation requested.']);
    } catch {
      setLogs((prev) => [...prev, 'Could not send cancellation request.']);
    }
  };

  const handleEvaluate = async () => {
    // Prevent duplicate submission
    if (isEvaluating) return;

    // Step 1: Client-side graph validation
    const graphError = validateGraph(nodes, edges);
    if (graphError) {
      setValidationStatus({ isValid: false, message: graphError });
      return;
    }

    // Check if models in canvas require local Ollama provider
    const modelNodes = nodes.filter((n) => n.type === 'model');
    const requiresOllama = modelNodes.some((n) => {
      const modelId = String(n.data?.model_identifier || n.data?.id || '');
      return !modelId.startsWith('mock-');
    });

    if (requiresOllama) {
      // Step 2: Check Ollama provider status
      await checkOllamaStatus();
      let ollamaOk = false;
      try {
        const healthRes = await fetch('/api/providers/ollama/health').catch(() =>
          fetch('http://localhost:8000/api/ollama/status')
        );
        if (healthRes.ok) {
          const healthData = await healthRes.json();
          ollamaOk = healthData.reachable === true || healthData.is_healthy === true;
        }
      } catch {
        ollamaOk = false;
      }

      if (!ollamaOk) {
        setOllamaStatus((prev) => ({
          ...prev,
          reachable: false,
          error: 'The local Ollama service could not be reached at http://localhost:11434. Start Ollama to evaluate.',
        }));
        setValidationStatus({
          isValid: false,
          message: 'Ollama is offline. Start the service with "ollama serve" to run evaluation.',
        });
        setLogs([
          '❌ Provider check failed: Ollama is not reachable at http://localhost:11434',
          '1. Start the service: ollama serve',
          '2. Verify installed models: ollama list',
          '3. Pull a model if needed: ollama pull qwen2.5:1.5b',
          '4. Verify API response: curl http://localhost:11434/api/tags',
          'Click "Retry Connection" in the banner once Ollama is running.',
        ]);
        return;
      }
    }

    // Step 3: Submit evaluation
    setIsEvaluating(true);
    setActiveExecutionId(null);
    setProgressPercentage(0);
    setCompletedSteps(0);
    setTotalSteps(0);
    setLogs(['Initiating evaluation run through Ollama engine...']);
    setCases([]);
    setValidationStatus(null);

    const serialized = serializeEvaluationGraph(nodes, edges, `${workflowName} Run`);

    try {
      const execRes = await fetch('http://localhost:8000/api/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(serialized),
      });

      if (!execRes.ok) {
        const err = await execRes.json();
        throw new Error(err.detail || `Server returned ${execRes.status}`);
      }

      const execData = await execRes.json();
      const executionId: string = execData.execution_id;
      setActiveExecutionId(executionId);
      setLogs((prev) => [...prev, `Execution started: ${executionId}`]);

      // Step 4: Connect to SSE stream
      // Backend broadcasts: started, step_progress, completed, failed, cancelled
      const eventSource = new EventSource(
        `http://localhost:8000/api/executions/${executionId}/events`
      );

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const evType: string = payload.event_type || payload.type || '';

          if (evType === 'started') {
            setTotalSteps(payload.total_steps || 0);
            setLogs((prev) => [...prev, payload.message || 'Evaluation started.']);
          } else if (evType === 'step_progress') {
            // Backend step_progress carries data.case with individual test case result
            setProgressPercentage(payload.progress_percentage || 0);
            setCompletedSteps(payload.completed_steps || 0);
            setTotalSteps(payload.total_steps || 0);
            if (payload.data && payload.data.case) {
              setCases((prev) => [...prev, payload.data.case]);
            }
            if (payload.message) {
              setLogs((prev) => [...prev, payload.message]);
            }
          } else if (evType === 'log') {
            setLogs((prev) => [...prev, payload.message]);
          } else if (evType === 'completed') {
            setIsEvaluating(false);
            setProgressPercentage(100);
            eventSource.close();
            setLogs((prev) => [
              ...prev,
              'Evaluation completed successfully. Results persisted to database.',
            ]);
          } else if (evType === 'failed') {
            setIsEvaluating(false);
            eventSource.close();
            setLogs((prev) => [
              ...prev,
              `Evaluation failed: ${payload.message || payload.error || 'Unknown error'}`,
            ]);
          } else if (evType === 'cancelled') {
            setIsEvaluating(false);
            eventSource.close();
            setLogs((prev) => [...prev, 'Evaluation was cancelled.']);
          }
        } catch (e) {
          console.error('SSE parse error', e);
        }
      };

      eventSource.onerror = () => {
        // SSE closed after terminal event — this is expected behaviour
        if (isEvaluating) {
          setIsEvaluating(false);
          setLogs((prev) => [...prev, 'Connection to execution stream closed.']);
        }
        eventSource.close();
      };
    } catch (err: any) {
      setIsEvaluating(false);
      setLogs((prev) => [...prev, `Execution error: ${err.message}`]);
    }
  };

  const handleExportJson = () => {
    const dataStr =
      'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(cases, null, 2));
    const dl = document.createElement('a');
    dl.setAttribute('href', dataStr);
    dl.setAttribute('download', `evalforge-cases-${Date.now()}.json`);
    dl.click();
  };

  const handleExportCsv = () => {
    if (cases.length === 0) return;
    const headers = ['case_index', 'prompt', 'expected_output', 'actual_output', 'passed', 'latency_ms'];
    const rows = cases.map((c) =>
      [
        c.case_index,
        `"${(c.prompt || '').replace(/"/g, '""')}"`,
        `"${(c.expected_output || '').replace(/"/g, '""')}"`,
        `"${(c.actual_output || '').replace(/"/g, '""')}"`,
        c.passed,
        c.latency_ms,
      ].join(',')
    );
    const csvContent =
      'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
    const dl = document.createElement('a');
    dl.setAttribute('href', encodeURI(csvContent));
    dl.setAttribute('download', `evalforge-cases-${Date.now()}.csv`);
    dl.click();
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F8FAFC]">
      {/* OLLAMA OFFLINE BANNER */}
      {ollamaStatus.checked && !ollamaStatus.reachable && (
        <OllamaBanner
          error={ollamaStatus.error}
          onRetry={checkOllamaStatus}
        />
      )}

      {/* TOP TOOLBAR */}
      <TopToolbar
        workflowName={workflowName}
        onNameChange={setWorkflowName}
        onSave={handleSave}
        onValidate={handleValidate}
        onEvaluate={handleEvaluate}
        onCancel={handleCancelEvaluation}
        isEvaluating={isEvaluating}
        isValidating={isValidating}
        validationStatus={validationStatus}
        ollamaReachable={ollamaStatus.reachable}
      />

      {/* MAIN CANVAS BODY: SIDEBAR + WORKSPACE + CONFIG */}
      <div className="flex-1 flex overflow-hidden relative">
        <NodeLibrarySidebar
          installedModels={installedModels}
          benchmarkSuites={benchmarkSuites}
          evaluators={evaluatorsList}
        />

        <div className="flex-1 h-full relative">
          <CanvasWorkspace
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onDropItem={onDropItem}
          />
        </div>

        <NodeConfigPanel
          selectedNode={selectedNode}
          onClose={() => setSelectedNode(null)}
          onUpdateNodeData={handleUpdateNodeData}
          onDeleteNode={handleDeleteNode}
        />
      </div>

      {/* BOTTOM RESULTS & SSE PANEL */}
      <ResultsPanel
        isEvaluating={isEvaluating}
        progressPercentage={progressPercentage}
        completedSteps={completedSteps}
        totalSteps={totalSteps}
        logs={logs}
        cases={cases}
        onExportJson={handleExportJson}
        onExportCsv={handleExportCsv}
      />
    </div>
  );
};
