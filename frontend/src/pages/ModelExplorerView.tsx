import React from 'react';
import { useModelDiscovery } from '../hooks/useModelDiscovery';

export const ModelExplorerView: React.FC = () => {
  const { models, loading, error, refresh } = useModelDiscovery();

  if (loading) {
    return <div className="p-8 text-center text-[#A7A29A]">Discovering models...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-[#F5F0E7]">Discovered Models ({models.length})</h3>
        <button onClick={refresh} className="px-3 py-1 bg-[#D9823B] text-[#191A18] font-semibold text-xs rounded-xl">Refresh Discovery</button>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((m) => (
          <div key={m.id} className="p-4 bg-[#1F201D] rounded-2xl border border-white/5 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-sm font-semibold text-[#F5F0E7]">{m.name}</h4>
                <p className="text-xs text-[#A7A29A]">{m.provider}</p>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${m.is_local ? 'bg-[#68B587]/20 text-[#68B587]' : 'bg-blue-500/20 text-blue-400'}`}>
                {m.is_local ? 'Local' : 'Cloud'}
              </span>
            </div>
            <p className="text-xs text-[#A7A29A] line-clamp-2">{m.description}</p>
            <div className="flex justify-between text-[11px] font-mono text-[#A7A29A] pt-2 border-t border-white/5">
              <span>RAM: {m.hardware.min_ram_gb}GB</span>
              <span>Context: {(m.context_window / 1000).toFixed(0)}k</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
