import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Cpu, Database, CheckCircle2, BookmarkCheck, Clock, Zap } from 'lucide-react';

/* MODEL NODE */
export const ModelNode: React.FC<NodeProps> = ({ data, selected }) => {
  const modelId = (data.model_identifier as string) || (data.label as string) || 'Ollama Model';
  const family = (data.family as string) || 'qwen/llama';
  const paramSize = (data.parameter_size as string) || 'Local';
  const status = (data.status as string) || 'idle'; // idle | evaluating | completed | error

  return (
    <div
      className={`w-64 bg-white rounded-lg border text-left shadow-sm transition-all ${
        selected ? 'border-[#2563EB] ring-2 ring-[#BFDBFE]' : 'border-[#E2E8F0] hover:border-[#94A3B8]'
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="dataset-in"
        className="!w-3 !h-3 !bg-[#2563EB] !border-2 !border-white"
        title="Input Dataset"
      />
      <div className="p-3">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB]">
              <Cpu className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#111827] truncate max-w-[140px]">{modelId}</div>
              <div className="text-[10px] text-[#64748B] uppercase">{family} · {paramSize}</div>
            </div>
          </div>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#F0FDF4] text-[#16A34A] border border-[#BBF7D0]">
            Ollama
          </span>
        </div>

        <div className="text-[10px] text-[#64748B] bg-[#F8FAFC] rounded px-2 py-1 mt-1 border border-[#E2E8F0]">
          Temperature: 0.0 · Greedy
        </div>

        {status === 'evaluating' && (
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-[#2563EB]">
            <Clock className="w-3 h-3 animate-spin" /> Evaluating cases...
          </div>
        )}
        {status === 'completed' && (
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-[#16A34A]">
            <CheckCircle2 className="w-3 h-3" /> Inference Done
          </div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="model-out"
        className="!w-3 !h-3 !bg-[#2563EB] !border-2 !border-white"
        title="Model Output"
      />
    </div>
  );
};

/* DATASET NODE */
export const DatasetNode: React.FC<NodeProps> = ({ data, selected }) => {
  const name = (data.label as string) || (data.name as string) || 'Evaluation Dataset';
  const casesCount = Array.isArray(data.cases) ? data.cases.length : (data.cases_count as number) || 4;

  return (
    <div
      className={`w-64 bg-white rounded-lg border text-left shadow-sm transition-all ${
        selected ? 'border-[#2563EB] ring-2 ring-[#BFDBFE]' : 'border-[#E2E8F0] hover:border-[#94A3B8]'
      }`}
    >
      <div className="p-3">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#F0FDF4] border border-[#BBF7D0] flex items-center justify-center text-[#16A34A]">
              <Database className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#111827] truncate max-w-[140px]">{name}</div>
              <div className="text-[10px] text-[#64748B]">{casesCount} Test Cases</div>
            </div>
          </div>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#F8FAFC] text-[#64748B] border border-[#E2E8F0]">
            Ground Truth
          </span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="dataset-out"
        className="!w-3 !h-3 !bg-[#16A34A] !border-2 !border-white"
        title="Dataset Feed"
      />
    </div>
  );
};

/* BENCHMARK SUITE NODE */
export const BenchmarkNode: React.FC<NodeProps> = ({ data, selected }) => {
  const name = (data.label as string) || (data.name as string) || 'Standard Benchmark';
  const category = (data.category as string) || 'Reasoning';
  const license = (data.license as string) || 'MIT';

  return (
    <div
      className={`w-64 bg-white rounded-lg border text-left shadow-sm transition-all ${
        selected ? 'border-[#2563EB] ring-2 ring-[#BFDBFE]' : 'border-[#E2E8F0] hover:border-[#94A3B8]'
      }`}
    >
      <div className="p-3">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#FFFBEB] border border-[#FDE68A] flex items-center justify-center text-[#D97706]">
              <BookmarkCheck className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#111827] truncate max-w-[140px]">{name}</div>
              <div className="text-[10px] text-[#64748B]">{category} Suite</div>
            </div>
          </div>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#FFFBEB] text-[#D97706] border border-[#FDE68A]">
            {license}
          </span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="benchmark-out"
        className="!w-3 !h-3 !bg-[#D97706] !border-2 !border-white"
        title="Benchmark Feed"
      />
    </div>
  );
};

/* EVALUATOR NODE */
export const EvaluatorNode: React.FC<NodeProps> = ({ data, selected }) => {
  const name = (data.label as string) || (data.evaluator_id as string) || 'Evaluator';
  const category = (data.category as string) || 'Accuracy';
  const score = data.score !== undefined ? (data.score as number) : null;

  return (
    <div
      className={`w-64 bg-white rounded-lg border text-left shadow-sm transition-all ${
        selected ? 'border-[#2563EB] ring-2 ring-[#BFDBFE]' : 'border-[#E2E8F0] hover:border-[#94A3B8]'
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="evaluator-in"
        className="!w-3 !h-3 !bg-[#7C3AED] !border-2 !border-white"
        title="Input Output & Reference"
      />
      <div className="p-3">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#F5F3FF] border border-[#DDD6FE] flex items-center justify-center text-[#7C3AED]">
              <Zap className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#111827] truncate max-w-[140px]">{name}</div>
              <div className="text-[10px] text-[#64748B]">{category} Metric</div>
            </div>
          </div>
          {score !== null ? (
            <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-[#F0FDF4] text-[#16A34A] border border-[#BBF7D0]">
              {(score * 100).toFixed(0)}%
            </span>
          ) : (
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#F8FAFC] text-[#64748B] border border-[#E2E8F0]">
              Metric
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export const nodeTypes = {
  model: ModelNode,
  dataset: DatasetNode,
  benchmark: BenchmarkNode,
  evaluator: EvaluatorNode,
};
