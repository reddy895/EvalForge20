import React, { useEffect, useState } from 'react';
import { Cpu, RefreshCw, Server, Zap, CheckCircle2, AlertCircle } from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  onRefreshModels?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onRefreshModels,
  isRefreshing = false,
}) => {
  const [ollamaStatus, setOllamaStatus] = useState<{
    connected: boolean;
    modelsCount: number;
    baseUrl: string;
  }>({
    connected: false,
    modelsCount: 0,
    baseUrl: 'http://localhost:11434',
  });

  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);

  const checkStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/health');
      if (res.ok) {
        const data = await res.json();
        setBackendHealthy(data.status === 'healthy');
        setOllamaStatus({
          connected: data.ollama?.status === 'connected',
          modelsCount: 0,
          baseUrl: data.ollama?.base_url || 'http://localhost:11434',
        });
      } else {
        setBackendHealthy(false);
        setOllamaStatus(prev => ({ ...prev, connected: false }));
      }
    } catch {
      setBackendHealthy(false);
      setOllamaStatus(prev => ({ ...prev, connected: false }));
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 bg-white border-b border-[#E2E8F0] px-4 flex items-center justify-between z-20 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#2563EB] flex items-center justify-center text-white font-bold text-sm shadow-sm">
            EF
          </div>
          <span className="font-semibold text-base text-[#111827] tracking-tight">
            EvalForge20
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] font-medium border border-[#BFDBFE]">
            Local Benchmarking
          </span>
        </div>

        <div className="h-4 w-[1px] bg-[#E2E8F0] mx-2" />

        <div className="text-xs font-medium text-[#64748B]">
          {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border bg-[#F8FAFC] border-[#E2E8F0] text-[#64748B]">
          <Server className="w-3.5 h-3.5" />
          <span>Backend:</span>
          {backendHealthy ? (
            <span className="text-[#16A34A] flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Online
            </span>
          ) : (
            <span className="text-[#DC2626] flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> Offline
            </span>
          )}
        </div>

        {/* Ollama Status Pill */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
            ollamaStatus.connected
              ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#16A34A]'
              : 'bg-[#FFFBEB] border-[#FDE68A] text-[#D97706]'
          }`}
          title={`Ollama URL: ${ollamaStatus.baseUrl}`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Ollama:</span>
          <span className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${
                ollamaStatus.connected ? 'bg-[#16A34A]' : 'bg-[#D97706]'
              }`}
            />
            {ollamaStatus.connected ? 'Connected' : 'Offline'}
          </span>
        </div>

        {/* Refresh Models Button */}
        {onRefreshModels && (
          <button
            onClick={onRefreshModels}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-[#64748B] hover:text-[#111827] hover:bg-[#F1F5F9] border border-[#E2E8F0] transition-colors disabled:opacity-50"
            title="Refresh local model discovery"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        )}
      </div>
    </header>
  );
};
