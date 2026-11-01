import React from 'react';
import { Node } from '@xyflow/react';
import { X, Trash2, Sliders, CheckSquare, Settings } from 'lucide-react';
import { Button } from '../ui/Primitives';

interface NodeConfigPanelProps {
  selectedNode: Node | null;
  onClose: () => void;
  onUpdateNodeData: (nodeId: string, newData: any) => void;
  onDeleteNode: (nodeId: string) => void;
}

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  selectedNode,
  onClose,
  onUpdateNodeData,
  onDeleteNode,
}) => {
  if (!selectedNode) {
    return (
      <aside className="w-72 bg-white border-l border-[#E2E8F0] p-4 flex flex-col items-center justify-center text-center text-[#94A3B8] shrink-0">
        <Sliders className="w-8 h-8 mb-2 stroke-1" />
        <div className="text-xs font-medium text-[#64748B]">No Node Selected</div>
        <div className="text-[11px] mt-1">Click any node on the canvas to configure parameters.</div>
      </aside>
    );
  }

  const { id, type, data } = selectedNode;
  const label = (data.label as string) || (data.name as string) || id;

  return (
    <aside className="w-72 bg-white border-l border-[#E2E8F0] flex flex-col h-full shrink-0 z-10">
      <div className="p-3 border-b border-[#E2E8F0] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-[#2563EB]" />
          <div>
            <div className="text-xs font-semibold text-[#111827] truncate max-w-[170px]">{label}</div>
            <div className="text-[10px] text-[#64748B] uppercase font-mono">{type} node</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-[#94A3B8] hover:text-[#111827] p-1 rounded-md hover:bg-[#F1F5F9]"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
        {/* MODEL NODE CONFIG */}
        {type === 'model' && (
          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">
                Model Identifier
              </label>
              <input
                type="text"
                disabled
                value={(data.model_identifier as string) || label}
                className="w-full text-xs px-2.5 py-1.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded text-[#64748B] font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">
                Temperature ({((data.temperature as number) ?? 0.0).toFixed(1)})
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.1"
                value={(data.temperature as number) ?? 0.0}
                onChange={(e) =>
                  onUpdateNodeData(id, { ...data, temperature: parseFloat(e.target.value) })
                }
                className="w-full"
              />
              <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5">
                <span>0.0 (Deterministic)</span>
                <span>1.0 (Creative)</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="300"
                value={(data.timeout_seconds as number) ?? 60}
                onChange={(e) =>
                  onUpdateNodeData(id, { ...data, timeout_seconds: parseInt(e.target.value) })
                }
                className="w-full text-xs px-2.5 py-1.5 bg-white border border-[#E2E8F0] rounded text-[#111827]"
              />
            </div>
          </div>
        )}

        {/* EVALUATOR NODE CONFIG */}
        {type === 'evaluator' && (
          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">Metric Type</label>
              <div className="p-2 bg-[#F8FAFC] rounded border border-[#E2E8F0] font-mono text-[11px] text-[#111827]">
                {(data.evaluator_id as string) || label}
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">
                Pass Threshold
              </label>
              <input
                type="number"
                min="0.0"
                max="1.0"
                step="0.05"
                value={(data.threshold as number) ?? 0.6}
                onChange={(e) =>
                  onUpdateNodeData(id, { ...data, threshold: parseFloat(e.target.value) })
                }
                className="w-full text-xs px-2.5 py-1.5 bg-white border border-[#E2E8F0] rounded text-[#111827]"
              />
            </div>
          </div>
        )}

        {/* BENCHMARK / DATASET NODE CONFIG */}
        {(type === 'dataset' || type === 'benchmark') && (
          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-[#64748B] mb-1">Dataset Name</label>
              <div className="p-2 bg-[#F8FAFC] rounded border border-[#E2E8F0] text-xs font-medium text-[#111827]">
                {label}
              </div>
            </div>

            <div className="text-[11px] text-[#64748B]">
              <span className="font-semibold text-[#111827]">Ground Truth:</span> Reference answers are
              automatically fed into connected evaluators.
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-[#E2E8F0]">
        <Button
          variant="danger"
          size="sm"
          className="w-full"
          icon={<Trash2 className="w-3.5 h-3.5" />}
          onClick={() => onDeleteNode(id)}
        >
          Delete Node
        </Button>
      </div>
    </aside>
  );
};
