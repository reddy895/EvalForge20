/**
 * OllamaBanner — Prominent offline recovery UI displayed when Ollama is unreachable.
 * Provides actionable instructions and a retry connection button.
 */
import React from 'react';
import { AlertTriangle, RefreshCw, Terminal, ChevronRight } from 'lucide-react';

interface OllamaBannerProps {
  /** Human-readable error description, e.g. "Ollama is not reachable at localhost:11434" */
  error?: string;
  /** Callback invoked when user clicks Retry Connection */
  onRetry: () => void;
}

export const OllamaBanner: React.FC<OllamaBannerProps> = ({ error, onRetry }) => {
  const [showInstructions, setShowInstructions] = React.useState(false);
  const [retrying, setRetrying] = React.useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await onRetry();
    } finally {
      setTimeout(() => setRetrying(false), 800);
    }
  };

  return (
    <div
      id="ollama-offline-banner"
      role="alert"
      className="bg-[#FEF3C7] border-b border-[#F59E0B] px-4 py-2.5 flex items-start justify-between gap-4 text-[#92400E] shrink-0"
    >
      <div className="flex items-start gap-3 min-w-0">
        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-[#D97706]" />
        <div className="min-w-0">
          <p className="text-xs font-semibold text-[#78350F]">
            Ollama is offline — Evaluation cannot run until the local provider is available
          </p>
          <p className="text-[11px] mt-0.5 truncate">
            {error || 'The Ollama service could not be reached at http://localhost:11434'}
          </p>

          {showInstructions && (
            <div className="mt-2 space-y-1 font-mono text-[11px] bg-[#FEF9C3] border border-[#FDE68A] rounded p-2">
              <div className="flex items-center gap-1.5">
                <ChevronRight className="w-3 h-3 text-[#B45309]" />
                <span className="text-[#78350F] font-semibold">Start Ollama service:</span>
                <code className="bg-white px-1.5 py-0.5 rounded border border-[#FDE68A] text-[#111827]">
                  ollama serve
                </code>
              </div>
              <div className="flex items-center gap-1.5">
                <ChevronRight className="w-3 h-3 text-[#B45309]" />
                <span className="text-[#78350F] font-semibold">List installed models:</span>
                <code className="bg-white px-1.5 py-0.5 rounded border border-[#FDE68A] text-[#111827]">
                  ollama list
                </code>
              </div>
              <div className="flex items-center gap-1.5">
                <ChevronRight className="w-3 h-3 text-[#B45309]" />
                <span className="text-[#78350F] font-semibold">Pull a small model:</span>
                <code className="bg-white px-1.5 py-0.5 rounded border border-[#FDE68A] text-[#111827]">
                  ollama pull qwen2.5:1.5b
                </code>
              </div>
              <div className="flex items-center gap-1.5">
                <ChevronRight className="w-3 h-3 text-[#B45309]" />
                <span className="text-[#78350F] font-semibold">Verify API:</span>
                <code className="bg-white px-1.5 py-0.5 rounded border border-[#FDE68A] text-[#111827]">
                  curl http://localhost:11434/api/tags
                </code>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded border border-[#F59E0B] bg-white hover:bg-[#FEF3C7] text-[#92400E] transition-colors"
        >
          <Terminal className="w-3 h-3" />
          {showInstructions ? 'Hide' : 'Setup'}
        </button>
        <button
          id="ollama-retry-btn"
          onClick={handleRetry}
          disabled={retrying}
          className="flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded bg-[#D97706] hover:bg-[#B45309] text-white border border-[#B45309] transition-colors disabled:opacity-60"
        >
          <RefreshCw className={`w-3 h-3 ${retrying ? 'animate-spin' : ''}`} />
          {retrying ? 'Checking...' : 'Retry Connection'}
        </button>
      </div>
    </div>
  );
};
