import React, { useEffect, useState } from 'react';
import { Cpu, RefreshCw, CheckCircle2, AlertCircle, Zap } from 'lucide-react';
import { Badge, Button, EmptyState } from '../components/ui/Primitives';

export const ModelsView: React.FC = () => {
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; latency_ms: number; message: string }>>({});

  const fetchModels = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/models');
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/models/refresh', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (modelId: string) => {
    setTestingModel(modelId);
    try {
      const res = await fetch('http://localhost:8000/api/models/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_identifier: modelId }),
      });
      const data = await res.json();
      setTestResults((prev) => ({
        ...prev,
        [modelId]: {
          success: data.success,
          latency_ms: data.latency_ms || 0,
          message: data.message || (data.success ? 'Inference successful' : 'Failed to reach model'),
        },
      }));
    } catch {
      setTestResults((prev) => ({
        ...prev,
        [modelId]: {
          success: false,
          latency_ms: 0,
          message: 'Connection timed out or failed',
        },
      }));
    } finally {
      setTestingModel(null);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Local Model Inventory</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Locally installed Ollama models discovered dynamically from http://localhost:11434
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E2E8F0] bg-white text-xs font-medium text-[#64748B] hover:text-[#111827] shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Inventory</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-[#64748B] text-xs">
          <RefreshCw className="w-5 h-5 animate-spin mr-2 text-[#2563EB]" />
          Scanning local Ollama instance...
        </div>
      ) : models.length === 0 ? (
        <EmptyState
          icon={Cpu}
          title="No Local Models Detected"
          description="Make sure Ollama is running at localhost:11434 and at least one model is pulled (e.g. ollama pull qwen2.5:1.5b)."
          action={
            <Button variant="primary" size="sm" onClick={handleRefresh}>
              Retry Discovery
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => {
            const testResult = testResults[model.name];
            const sizeGb = model.size_bytes ? (model.size_bytes / (1024 * 1024 * 1024)).toFixed(2) : 'Unknown';

            return (
              <div
                key={model.name}
                className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm space-y-3 hover:border-[#CBD5E1] transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-md bg-[#EFF6FF] text-[#2563EB]">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111827]">{model.name}</div>
                      <div className="text-[10px] text-[#64748B] font-mono">
                        {model.family || 'ollama'} • {sizeGb} GB
                      </div>
                    </div>
                  </div>
                  <Badge variant="success">Installed</Badge>
                </div>

                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2 text-[11px] space-y-1">
                  <div className="flex justify-between text-[#64748B]">
                    <span>Format:</span>
                    <span className="font-mono text-[#111827]">{model.format || 'gguf'}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>Parameter Size:</span>
                    <span className="font-mono text-[#111827]">{model.parameter_size || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>Quantization:</span>
                    <span className="font-mono text-[#111827]">{model.quantization_level || 'N/A'}</span>
                  </div>
                </div>

                {testResult && (
                  <div
                    className={`p-2 rounded border text-[11px] ${
                      testResult.success
                        ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#16A34A]'
                        : 'bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]'
                    }`}
                  >
                    <div className="font-semibold flex items-center gap-1">
                      {testResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                      {testResult.message}
                    </div>
                    {testResult.success && (
                      <div className="text-[10px] font-mono mt-0.5">
                        Latency: {testResult.latency_ms.toFixed(0)} ms
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={() => handleTestConnection(model.name)}
                  disabled={testingModel === model.name}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded border border-[#E2E8F0] bg-white hover:bg-[#F8FAFC] text-xs font-medium text-[#111827] transition-colors"
                >
                  <Zap className={`w-3.5 h-3.5 text-[#2563EB] ${testingModel === model.name ? 'animate-spin' : ''}`} />
                  <span>{testingModel === model.name ? 'Testing...' : 'Test Connection'}</span>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
