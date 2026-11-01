import React, { useState } from 'react';
import {
  Search,
  Cpu,
  Database,
  Zap,
  BookmarkCheck,
  ChevronDown,
  ChevronRight,
  Shield,
  Activity,
  Code,
  Calculator,
} from 'lucide-react';

interface NodeLibrarySidebarProps {
  installedModels: Array<{ id: string; name: string; family?: string; size_bytes?: number }>;
  benchmarkSuites: Array<{ id: string; name: string; category: string; license: string }>;
  evaluators: Array<{ evaluator_id: string; name: string; category: string; description: string }>;
}

export const NodeLibrarySidebar: React.FC<NodeLibrarySidebarProps> = ({
  installedModels,
  benchmarkSuites,
  evaluators,
}) => {
  const [search, setSearch] = useState('');
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    models: true,
    benchmarks: true,
    evaluators: true,
  });

  const toggleSection = (sec: string) => {
    setOpenSections((prev) => ({ ...prev, [sec]: !prev[sec] }));
  };

  const onDragStart = (event: React.DragEvent, type: string, data: any) => {
    event.dataTransfer.setData(
      'application/evalforge-node',
      JSON.stringify({ type, data })
    );
    event.dataTransfer.effectAllowed = 'move';
  };

  const filteredModels = installedModels.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  );
  const filteredBenchmarks = benchmarkSuites.filter((b) =>
    b.name.toLowerCase().includes(search.toLowerCase()) || b.category.toLowerCase().includes(search.toLowerCase())
  );
  const filteredEvaluators = evaluators.filter((e) =>
    e.name.toLowerCase().includes(search.toLowerCase()) || e.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <aside className="w-64 bg-white border-r border-[#E2E8F0] flex flex-col h-full select-none shrink-0 z-10">
      <div className="p-3 border-b border-[#E2E8F0]">
        <div className="text-xs font-semibold text-[#111827] mb-2">Node Library</div>
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#94A3B8]" />
          <input
            type="text"
            placeholder="Search nodes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-8 pr-2.5 py-1.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#2563EB] text-[#111827] placeholder-[#94A3B8]"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {/* MODEL NODES */}
        <div>
          <button
            onClick={() => toggleSection('models')}
            className="w-full flex items-center justify-between text-[11px] font-semibold text-[#64748B] uppercase tracking-wider py-1 px-1 hover:text-[#111827]"
          >
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#2563EB]" />
              Local Models ({filteredModels.length})
            </span>
            {openSections.models ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>

          {openSections.models && (
            <div className="mt-1 space-y-1">
              {filteredModels.length === 0 ? (
                <div className="text-[11px] text-[#94A3B8] p-2 bg-[#F8FAFC] rounded border border-dashed border-[#E2E8F0]">
                  No models discovered via Ollama. Run <span className="font-mono">ollama pull &lt;model&gt;</span>.
                </div>
              ) : (
                filteredModels.map((m) => (
                  <div
                    key={m.id}
                    draggable
                    onDragStart={(e) =>
                      onDragStart(e, 'model', {
                        label: m.name,
                        model_identifier: m.name,
                        family: m.family || 'ollama',
                      })
                    }
                    className="p-2 rounded-md bg-[#F8FAFC] hover:bg-[#EFF6FF] border border-[#E2E8F0] hover:border-[#BFDBFE] cursor-grab active:cursor-grabbing transition-colors"
                  >
                    <div className="text-xs font-medium text-[#111827] truncate">{m.name}</div>
                    <div className="text-[10px] text-[#64748B] flex items-center justify-between mt-0.5">
                      <span>{m.family || 'qwen'}</span>
                      <span className="text-[#16A34A] font-mono text-[9px]">Installed</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* BENCHMARKS & DATASETS */}
        <div>
          <button
            onClick={() => toggleSection('benchmarks')}
            className="w-full flex items-center justify-between text-[11px] font-semibold text-[#64748B] uppercase tracking-wider py-1 px-1 hover:text-[#111827]"
          >
            <span className="flex items-center gap-1.5">
              <BookmarkCheck className="w-3.5 h-3.5 text-[#D97706]" />
              Benchmark Suites ({filteredBenchmarks.length})
            </span>
            {openSections.benchmarks ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>

          {openSections.benchmarks && (
            <div className="mt-1 space-y-1">
              {filteredBenchmarks.map((b) => (
                <div
                  key={b.id}
                  draggable
                  onDragStart={(e) =>
                    onDragStart(e, 'benchmark', {
                      label: b.name,
                      suite_id: b.id,
                      category: b.category,
                      license: b.license,
                    })
                  }
                  className="p-2 rounded-md bg-[#F8FAFC] hover:bg-[#FFFBEB] border border-[#E2E8F0] hover:border-[#FDE68A] cursor-grab active:cursor-grabbing transition-colors"
                >
                  <div className="text-xs font-medium text-[#111827] truncate">{b.name}</div>
                  <div className="text-[10px] text-[#64748B] flex items-center justify-between mt-0.5">
                    <span>{b.category}</span>
                    <span className="font-mono text-[9px] text-[#D97706]">{b.license}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* EVALUATOR METRICS */}
        <div>
          <button
            onClick={() => toggleSection('evaluators')}
            className="w-full flex items-center justify-between text-[11px] font-semibold text-[#64748B] uppercase tracking-wider py-1 px-1 hover:text-[#111827]"
          >
            <span className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-[#7C3AED]" />
              Evaluators ({filteredEvaluators.length})
            </span>
            {openSections.evaluators ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>

          {openSections.evaluators && (
            <div className="mt-1 space-y-1">
              {filteredEvaluators.map((ev) => (
                <div
                  key={ev.evaluator_id}
                  draggable
                  onDragStart={(e) =>
                    onDragStart(e, 'evaluator', {
                      label: ev.name,
                      evaluator_id: ev.evaluator_id,
                      category: ev.category,
                    })
                  }
                  className="p-2 rounded-md bg-[#F8FAFC] hover:bg-[#F5F3FF] border border-[#E2E8F0] hover:border-[#DDD6FE] cursor-grab active:cursor-grabbing transition-colors"
                >
                  <div className="text-xs font-medium text-[#111827]">{ev.name}</div>
                  <div className="text-[10px] text-[#64748B] mt-0.5">{ev.category}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
