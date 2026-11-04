import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { Clock, AlertCircle } from 'lucide-react';
import { ModelSummary } from '../../types/evaluationResults';

interface LatencyComparisonChartProps {
  modelSummaries: ModelSummary[];
}

export const LatencyComparisonChart: React.FC<LatencyComparisonChartProps> = ({
  modelSummaries,
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center text-center min-h-[280px]">
        <AlertCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Latency Data</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Measured inference latencies will appear once test cases complete.
        </p>
      </div>
    );
  }

  const chartData = modelSummaries.map((m) => {
    const avg = m.avg_latency_ms !== null && m.avg_latency_ms !== undefined
      ? Number(m.avg_latency_ms.toFixed(1))
      : null;
    const median = m.median_latency_ms !== null && m.median_latency_ms !== undefined
      ? Number(m.median_latency_ms.toFixed(1))
      : null;
    const p95 = m.p95_latency_ms !== null && m.p95_latency_ms !== undefined
      ? Number(m.p95_latency_ms.toFixed(1))
      : null;

    return {
      name: m.name || m.model_id,
      model_id: m.model_id,
      avg_latency_ms: avg,
      displayLatency: avg ?? 0,
      median_latency_ms: median,
      p95_latency_ms: p95,
      hasValue: avg !== null,
    };
  });

  const BAR_COLORS = ['#6366F1', '#4F46E5', '#4338CA', '#3730A3', '#312E81'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Inference Latency Comparison</h3>
            <p className="text-[11px] text-slate-500">
              Average response generation time per test case (unit: milliseconds)
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-200">
          Unit: ms
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 15, right: 20, left: 10, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis
              dataKey="name"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tick={{ fill: '#334155', fontWeight: 500 }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tickFormatter={(v) => `${v}ms`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-lg border border-slate-800 space-y-1">
                      <div className="font-semibold text-slate-200">{d.name}</div>
                      <div className="flex items-center justify-between gap-4 text-slate-300">
                        <span>Mean Latency:</span>
                        <span className="font-bold text-indigo-400">
                          {d.avg_latency_ms !== null ? `${d.avg_latency_ms} ms` : 'N/A (Missing telemetry)'}
                        </span>
                      </div>
                      {d.median_latency_ms !== null && (
                        <div className="flex items-center justify-between gap-4 text-slate-400 text-[11px]">
                          <span>Median (P50):</span>
                          <span>{d.median_latency_ms} ms</span>
                        </div>
                      )}
                      {d.p95_latency_ms !== null && (
                        <div className="flex items-center justify-between gap-4 text-slate-400 text-[11px]">
                          <span>P95 Latency:</span>
                          <span>{d.p95_latency_ms} ms</span>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="displayLatency" radius={[6, 6, 0, 0]} maxBarSize={56}>
              {chartData.map((d, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={d.hasValue ? BAR_COLORS[index % BAR_COLORS.length] : '#CBD5E1'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

