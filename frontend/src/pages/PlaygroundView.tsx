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

const INITIAL_NODES: Node[] = [
  {
    id: 'benchmark-1',
    type: 'benchmark',
    position: { x: 50, y: 150 },
    data: {
      id: 'math_gsm8k_mini',
      name: 'GSM8K Reasoning Mini',
      category: 'Mathematics',
      sample_count: 5,
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

export const PlaygroundView: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<Edge[]>(INITIAL_EDGES);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [workflowName, setWorkflowName] = useState<string>('Local Model Reasoning Benchmark');

  // Metadata lists
  const [installedModels, setInstalledModels] = useState<any[]>([]);
  const [benchmarkSuites, setBenchmarkSuites] = useState<any[]>([]);
  const [evaluatorsList, setEvaluatorsList] = useState<any[]>([]);

  // Execution states
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationStatus, setValidationStatus] = useState<{ isValid: boolean; message?: string } | null>(null);
  const [progressPercentage, setProgressPercentage] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<number>(0);
  const [totalSteps, setTotalSteps] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [cases, setCases] = useState<any[]>([]);

  // Fetch models, benchmarks, evaluators from backend API
  useEffect(() => {
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
  }, []);

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
    try {
      const res = await fetch('http://localhost:8000/api/workflows/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: nodes.map((n) => ({
            id: n.id,
            type: n.type,
            name: n.data.name || n.id,
            config: n.data,
          })),
          edges: edges.map((e) => ({
            id: e.id,
            source_id: e.source,
            target_id: e.target,
          })),
        }),
      });
      const data = await res.json();
      setValidationStatus({
        isValid: data.is_valid,
        message: data.is_valid
          ? `Valid workflow: ${data.execution_plan?.models?.length || 1} model(s), ${data.execution_plan?.evaluators?.length || 1} metric(s)`
          : (data.errors && data.errors[0]) || 'Validation failed',
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
      await fetch('http://localhost:8000/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName,
          nodes: nodes.map((n) => ({
            id: n.id,
            type: n.type,
            name: n.data.name || n.id,
            config: n.data,
            position: n.position,
          })),
          edges: edges.map((e) => ({
            id: e.id,
            source_id: e.source,
            target_id: e.target,
          })),
        }),
      });
      alert('Workflow saved successfully!');
    } catch {
      alert('Failed to save workflow.');
    }
  };

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    setProgressPercentage(0);
    setLogs(['Initiating local evaluation run through Ollama engine...']);
    setCases([]);

    try {
      const execRes = await fetch('http://localhost:8000/api/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${workflowName} Run`,
          workflow_graph: {
            nodes: nodes.map((n) => ({
              id: n.id,
              type: n.type,
              name: n.data.name || n.id,
              config: n.data,
            })),
            edges: edges.map((e) => ({
              id: e.id,
              source_id: e.source,
              target_id: e.target,
            })),
          },
        }),
      });

      if (!execRes.ok) {
        const err = await execRes.json();
        throw new Error(err.detail || 'Failed to start execution');
      }

      const execData = await execRes.json();
      const executionId = execData.execution_id;
      setLogs((prev) => [...prev, `Execution dispatched: ${executionId}`]);

      // Connect to SSE stream
      const eventSource = new EventSource(
        `http://localhost:8000/api/executions/${executionId}/events`
      );

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'log') {
            setLogs((prev) => [...prev, payload.message]);
          } else if (payload.type === 'progress') {
            setProgressPercentage(payload.progress_percentage || 0);
            setCompletedSteps(payload.completed_steps || 0);
            setTotalSteps(payload.total_steps || 0);
          } else if (payload.type === 'case_result') {
            setCases((prev) => [...prev, payload.case]);
          } else if (payload.type === 'finished' || payload.type === 'failed') {
            setIsEvaluating(false);
            eventSource.close();
            setLogs((prev) => [
              ...prev,
              payload.type === 'finished'
                ? 'Evaluation finished successfully. Results persisted to database.'
                : `Evaluation error: ${payload.error || 'Failed'}`,
            ]);
          }
        } catch (e) {
          console.error('SSE parse error', e);
        }
      };

      eventSource.onerror = () => {
        setIsEvaluating(false);
        eventSource.close();
      };
    } catch (err: any) {
      setIsEvaluating(false);
      setLogs((prev) => [...prev, `Execution error: ${err.message}`]);
    }
  };

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(cases, null, 2));
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
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
    const dl = document.createElement('a');
    dl.setAttribute('href', encodeURI(csvContent));
    dl.setAttribute('download', `evalforge-cases-${Date.now()}.csv`);
    dl.click();
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F8FAFC]">
      {/* TOP TOOLBAR */}
      <TopToolbar
        workflowName={workflowName}
        onNameChange={setWorkflowName}
        onSave={handleSave}
        onValidate={handleValidate}
        onEvaluate={handleEvaluate}
        isEvaluating={isEvaluating}
        isValidating={isValidating}
        validationStatus={validationStatus}
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
