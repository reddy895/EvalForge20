import { Node, Edge } from '@xyflow/react';

export interface SerializedNode {
  id: string;
  type: string;
  name: string;
  category: string;
  data: Record<string, any>;
  position: { x: number; y: number };
}

export interface SerializedEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
}

export interface SerializedGraph {
  nodes: SerializedNode[];
  edges: SerializedEdge[];
}

export interface ExecutionPayload {
  name: string;
  workflow_graph: SerializedGraph;
  execution_name?: string;
  concurrency_limit?: number;
  timeout_seconds?: number;
}

export interface ExtractedExecutionConfig {
  models: Array<{ id: string; name: string; model_identifier: string; provider: string }>;
  dataset?: { id: string; name: string; dataset_id: string; category?: string };
  evaluators: Array<{ id: string; name: string; evaluator_id: string; metric_type?: string }>;
}

/**
 * Serialize React Flow canvas nodes and edges into validated backend payload structure.
 */
export function serializeEvaluationGraph(
  nodes: Node[],
  edges: Edge[],
  workflowName: string = 'Evaluation Run'
): ExecutionPayload {
  const serializedNodes: SerializedNode[] = nodes.map((node) => ({
    id: String(node.id),
    type: String(node.type || 'model'),
    name: String(node.data?.name || node.data?.label || node.id),
    category: String(node.data?.category || ''),
    data: { ...(node.data || {}) },
    position: {
      x: Number(node.position?.x ?? 0),
      y: Number(node.position?.y ?? 0),
    },
  }));

  const serializedEdges: SerializedEdge[] = edges.map((edge) => ({
    id: String(edge.id),
    source: String(edge.source),
    target: String(edge.target),
    sourceHandle: edge.sourceHandle || null,
    targetHandle: edge.targetHandle || null,
  }));

  return {
    name: workflowName,
    execution_name: workflowName,
    workflow_graph: {
      nodes: serializedNodes,
      edges: serializedEdges,
    },
  };
}

/**
 * Extract typed semantic components from canvas graph (models, dataset, evaluators)
 * to facilitate both client-side inspection and targeted API execution.
 */
export function extractExecutionConfig(nodes: Node[], _edges: Edge[] = []): ExtractedExecutionConfig {
  const models: ExtractedExecutionConfig['models'] = [];
  let dataset: ExtractedExecutionConfig['dataset'] | undefined = undefined;
  const evaluators: ExtractedExecutionConfig['evaluators'] = [];

  for (const node of nodes) {
    const nodeType = (node.type || '').toLowerCase();
    const d = (node.data || {}) as Record<string, unknown>;

    if (nodeType === 'model') {
      models.push({
        id: node.id,
        name: String(d.name || d.label || 'Model'),
        model_identifier: String(d.model_identifier || d.identifier || d.id || 'qwen2.5:1.5b'),
        provider: String(d.provider || 'ollama'),
      });
    } else if (nodeType === 'dataset' || nodeType === 'benchmark') {
      if (!dataset) {
        dataset = {
          id: node.id,
          name: String(d.name || d.label || 'Dataset'),
          dataset_id: String(d.dataset_id || d.id || 'coding_basics'),
          category: typeof d.category === 'string' ? d.category : undefined,
        };
      }
    } else if (nodeType === 'evaluator') {
      evaluators.push({
        id: node.id,
        name: String(d.name || d.label || 'Evaluator'),
        evaluator_id: String(d.evaluator_id || d.id || 'exact_match'),
        metric_type: typeof d.metric_type === 'string' ? d.metric_type : (typeof d.type === 'string' ? d.type : undefined),
      });
    }
  }

  return {
    models,
    dataset,
    evaluators,
  };
}
