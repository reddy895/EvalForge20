import React, { useState } from 'react';
import { useEvaluationRunner } from '../hooks/useEvaluationRunner';

export const EvaluationWorkspaceView: React.FC = () => {
  const { running, progress, launchEvaluation } = useEvaluationRunner();
  const [selectedModel, setSelectedModel] = useState('qwen-2.5-7b-instruct');
  const [result, setResult] = useState<any>(null);

  const handleStart = async () => {
    try {
      const res = await launchEvaluation({ model_id: selectedModel, benchmark_id: 'coding' });
      setResult(res);
    } catch {
      // handled in hook
    }
  };

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <h3 className="text-base font-bold text-[#F5F0E7]">Evaluation Workspace</h3>
      <div className="flex gap-4 items-center">
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="px-3 py-1.5 bg-[#161715] text-[#F5F0E7] text-xs rounded-xl border border-white/10"
        >
          <option value="qwen-2.5-7b-instruct">Qwen 2.5 7B Instruct (Local)</option>
          <option value="llama-3.1-8b-instruct">Llama 3.1 8B Instruct (Local)</option>
          <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Cloud)</option>
        </select>
        <button
          onClick={handleStart}
          disabled={running}
          className="px-4 py-1.5 bg-[#D9823B] text-[#191A18] font-bold text-xs rounded-xl disabled:opacity-50"
        >
          {running ? `Running (${progress}%)...` : 'Launch Run'}
        </button>
      </div>
      {result && (
        <div className="p-4 bg-[#161715] rounded-2xl text-xs font-mono text-[#68B587]">
          Evaluation Job Dispatched: {result.id || 'Success'}
        </div>
      )}
    </div>
  );
};
