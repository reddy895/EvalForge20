import React, { useEffect, useState } from 'react';
import {
  FlaskConical,
  Download,
  Trash2,
  BarChart3,
  CheckCircle2,
  Calendar,
  Layers,
  Cpu,
} from 'lucide-react';
import { Button, Card, Badge, EmptyState } from '../components/ui/Primitives';
import { ComparisonCharts } from '../components/charts/ComparisonCharts';

export const ExperimentsView: React.FC = () => {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparisonData, setComparisonData] = useState<any[]>([]);

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/experiments');
      if (res.ok) {
        const data = await res.json();
        setExperiments(data.experiments || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, []);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleCompare = () => {
    const selectedExps = experiments.filter((e) => selectedIds.includes(e.id));
    const comp = selectedExps.map((e) => ({
      model: e.model_identifier,
      pass_rate: e.metrics?.pass_rate ?? 0,
      accuracy: e.metrics?.normalized_accuracy ?? e.metrics?.pass_rate ?? 0,
      latency_ms: e.metrics?.avg_latency_ms ?? 0,
    }));
    setComparisonData(comp);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this experiment record?')) return;
    try {
      const res = await fetch(`http://localhost:8000/api/experiments/${id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setExperiments((prev) => prev.filter((e) => e.id !== id));
        setSelectedIds((prev) => prev.filter((x) => x !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleExport = (id: string, format: 'json' | 'csv') => {
    window.open(`http://localhost:8000/api/experiments/${id}/export?format=${format}`, '_blank');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Experiment History</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Audit, inspect, and compare past model evaluation runs persisted locally in SQLite.
          </p>
        </div>
        {selectedIds.length >= 2 && (
          <Button
            variant="primary"
            size="sm"
            onClick={handleCompare}
            icon={<BarChart3 className="w-3.5 h-3.5" />}
          >
            Compare ({selectedIds.length}) Models
          </Button>
        )}
      </div>

      {/* Comparison Chart Display */}
      {comparisonData.length > 0 && (
        <Card title="Multi-Model Experiment Delta Analysis">
          <ComparisonCharts data={comparisonData} />
        </Card>
      )}

      {/* Experiments List */}
      {loading ? (
        <div className="text-xs text-[#64748B] py-8 text-center">Loading experiment records...</div>
      ) : experiments.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="No experiments recorded yet"
          description="Evaluate models in the visual Playground. Every benchmark run is automatically recorded here."
        />
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {experiments.map((exp) => {
            const isSelected = selectedIds.includes(exp.id);
            const passRate = exp.metrics?.pass_rate !== undefined ? exp.metrics.pass_rate * 100 : 0;
            const avgLat = exp.metrics?.avg_latency_ms;

            return (
              <div
                key={exp.id}
                className={`p-4 bg-white border rounded-lg transition-all shadow-sm flex items-center justify-between ${
                  isSelected ? 'border-[#2563EB] ring-1 ring-[#BFDBFE]' : 'border-[#E2E8F0] hover:border-[#CBD5E1]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(exp.id)}
                    className="rounded border-[#CBD5E1] text-[#2563EB] focus:ring-[#2563EB]"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-[#111827]">{exp.name}</span>
                      <Badge variant="accent">{exp.model_identifier}</Badge>
                      <span className="text-[10px] text-[#64748B] flex items-center gap-1 font-mono">
                        <Calendar className="w-3 h-3" /> {exp.created_at.slice(0, 16)}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-[#64748B] mt-2 font-mono">
                      <span>Pass Rate: <strong className="text-[#16A34A]">{passRate.toFixed(1)}%</strong></span>
                      {avgLat !== undefined && (
                        <span>Avg Latency: <strong className="text-[#111827]">{avgLat.toFixed(0)}ms</strong></span>
                      )}
                      <span>Cases: {exp.metrics?.total_cases ?? 0}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleExport(exp.id, 'csv')}
                    icon={<Download className="w-3.5 h-3.5" />}
                  >
                    CSV
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleExport(exp.id, 'json')}
                    icon={<Download className="w-3.5 h-3.5" />}
                  >
                    JSON
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(exp.id)}
                    className="text-[#DC2626] hover:bg-[#FEF2F2]"
                    icon={<Trash2 className="w-3.5 h-3.5" />}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
