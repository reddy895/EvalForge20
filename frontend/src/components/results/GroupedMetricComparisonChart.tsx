import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { SlidersHorizontal, AlertCircle } from 'lucide-react';
import { ModelSummary } from '../../types/evaluationResults';

interface GroupedMetricComparisonChartProps {
  modelSummaries: ModelSummary[];
  evaluators: string[];
}

export const GroupedMetricComparisonChart: React.FC<GroupedMetricComparisonChartProps> = ({
  modelSummaries,
  evaluators,
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center text-center min-h-[280px]">
        <AlertCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Metric Data</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Detailed evaluator metrics will appear once test cases are evaluated.
        </p>
      </div>
    );
  }

  // Find all compatible metric keys (excluding latency, count, etc.)
  const candidateKeys = new Set<string>();
  evaluators.forEach((e) => candidateKeys.add(e));

  modelSummaries.forEach((m) => {
    Object.keys(m.metrics || {}).forEach((k) => {
      if (
        !k.startsWith('_') &&
        !k.includes('latency') &&
        !k.includes('tokens') &&
        !k.includes('duration') &&
        !k.includes('count')
      ) {
        candidateKeys.add(k);
      }
    });
  });

  const validMetricKeys = Array.from(candidateKeys);

  if (validMetricKeys.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <SlidersHorizontal className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Evaluator Metric Comparison</h3>
            <p className="text-[11px] text-slate-500">Grouped performance across connected evaluators</p>
          </div>
        </div>
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-100">
          <p className="text-xs font-medium text-slate-600">No compatible evaluator metrics recorded.</p>
        </div>
      </div>
    );
  }

  // Build data where each row is a metric, with keys for each model
  const chartData = validMetricKeys.map((metricKey) => {
    const row: Record<string, any> = {
      metric: metricKey.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      rawKey: metricKey,
    };

    modelSummaries.forEach((m) => {
      const val = m.metrics[metricKey];
      if (val !== undefined && val !== null) {
        // Normalize 0.0-1.0 to 0-100%
        const normalized = val <= 1.0 ? val * 100 : val;
        row[m.model_id] = Number(normalized.toFixed(1));
      } else {
        row[m.model_id] = null;
      }
    });

    return row;
  });

  const MODEL_COLORS = ['#2563EB', '#0D9488', '#F59E0B', '#8B5CF6', '#EC4899'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <SlidersHorizontal className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-Metric Grouped Comparison</h3>
            <p className="text-[11px] text-slate-500">
              Normalized score distribution (0-100%) across evaluator criteria
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
          {validMetricKeys.length} Evaluator {validMetricKeys.length === 1 ? 'Metric' : 'Metrics'}
        </span>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 15, right: 20, left: 0, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis
              dataKey="metric"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tick={{ fill: '#334155', fontWeight: 500 }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              domain={[0, 100]}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-lg border border-slate-800 space-y-1">
                      <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1">
                        {label}
                      </div>
                      {payload.map((entry, idx) => (
                        <div key={idx} className="flex items-center justify-between gap-4">
                          <span style={{ color: entry.color }} className="font-medium">
                            {entry.name}:
                          </span>
                          <span className="font-mono font-bold">
                            {entry.value !== null && entry.value !== undefined
                              ? `${entry.value}%`
                              : 'N/A'}
                          </span>
                        </div>
                      ))}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ paddingBottom: 10, fontSize: 11 }}
            />
            {modelSummaries.map((m, idx) => (
              <Bar
                key={m.model_id}
                dataKey={m.model_id}
                name={m.name || m.model_id}
                fill={MODEL_COLORS[idx % MODEL_COLORS.length]}
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
