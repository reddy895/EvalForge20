import React, { useEffect, useState } from 'react';
import { Database, RefreshCw, Eye } from 'lucide-react';
import { Badge, EmptyState } from '../components/ui/Primitives';

export const DatasetsView: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDataset, setSelectedDataset] = useState<any | null>(null);

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/datasets');
      if (res.ok) {
        const data = await res.json();
        setDatasets(data.datasets || []);
        if (data.datasets && data.datasets.length > 0 && !selectedDataset) {
          setSelectedDataset(data.datasets[0]);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Evaluation Datasets</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Curated benchmark test suites and custom prompt datasets with ground truth
          </p>
        </div>
        <button
          onClick={fetchDatasets}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E2E8F0] bg-white text-xs font-medium text-[#64748B] hover:text-[#111827] shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* DATASETS LIST */}
        <div className="space-y-3">
          <div className="text-xs font-semibold text-[#111827] uppercase tracking-wider">
            Available Datasets ({datasets.length})
          </div>

          <div className="space-y-2">
            {datasets.map((d) => {
              const isSelected = selectedDataset?.id === d.id;
              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDataset(d)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#EFF6FF] border-[#2563EB] shadow-sm'
                      : 'bg-white border-[#E2E8F0] hover:border-[#CBD5E1]'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="text-xs font-bold text-[#111827]">{d.name}</div>
                    <Badge variant="neutral">{d.category || 'General'}</Badge>
                  </div>
                  <div className="text-[11px] text-[#64748B] mt-1 line-clamp-2">
                    {d.description || 'Standard evaluation dataset'}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-[#64748B] mt-2 font-mono">
                    <span>{d.sample_count || (d.samples && d.samples.length) || 0} samples</span>
                    <span>•</span>
                    <span>{d.license || 'Open Source'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* DATASET DETAILS & TEST CASES PREVIEW */}
        <div className="md:col-span-2 space-y-4">
          {selectedDataset ? (
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-4">
              <div className="border-b border-[#E2E8F0] pb-3 flex items-start justify-between">
                <div>
                  <h2 className="text-base font-bold text-[#111827]">{selectedDataset.name}</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">{selectedDataset.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono text-[#64748B]">License</div>
                  <div className="text-xs font-semibold text-[#111827]">
                    {selectedDataset.license || 'MIT / Apache-2.0'}
                  </div>
                </div>
              </div>

              {/* SAMPLES TABLE */}
              <div>
                <div className="text-xs font-bold text-[#111827] mb-2 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-[#2563EB]" />
                  <span>Sample Test Cases Preview</span>
                </div>

                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {(selectedDataset.samples || []).map((sample: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded text-xs space-y-2"
                    >
                      <div className="font-semibold text-[#111827] flex items-center justify-between">
                        <span>Case #{idx + 1}</span>
                        {sample.id && <span className="text-[10px] font-mono text-[#64748B]">{sample.id}</span>}
                      </div>
                      <div>
                        <div className="text-[10px] uppercase font-mono text-[#64748B]">Input / Prompt:</div>
                        <div className="text-xs text-[#111827] bg-white p-2 rounded border border-[#E2E8F0] mt-0.5 font-mono">
                          {sample.input || sample.prompt}
                        </div>
                      </div>
                      {sample.expected_output && (
                        <div>
                          <div className="text-[10px] uppercase font-mono text-[#64748B]">Expected Output:</div>
                          <div className="text-xs text-[#16A34A] bg-[#F0FDF4] p-2 rounded border border-[#BBF7D0] mt-0.5 font-mono">
                            {sample.expected_output}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Database}
              title="No Dataset Selected"
              description="Select a dataset on the left to preview its schema, license, and ground truth samples."
            />
          )}
        </div>
      </div>
    </div>
  );
};
