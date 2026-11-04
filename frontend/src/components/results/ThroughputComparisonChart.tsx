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
import { Zap, AlertCircle } from 'lucide-react';
import { ModelSummary } from '../../types/evaluationResults';

interface ThroughputComparisonChartProps {
  modelSummaries: ModelSummary[];
}

export const ThroughputComparisonChart: React.FC<ThroughputComparisonChartProps> = ({
  modelSummaries,
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center text-center min-h-[280px]">
        <AlertCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Throughput Data Available</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Measured generation throughput will appear once token telemetry is captured.
        </p>
      </div>
    );
  }

  const chartData = modelSummaries.map((m) => {
    const rawTps = m.tokens_per_second;
    const hasValue = rawTps !== null && rawTps !== undefined && rawTps > 0;
    const tps = hasValue ? Number(rawTps.toFixed(1)) : null;

    return {
      name: m.name || m.model_id,
      model_id: m.model_id,
      tps,
      displayTps: tps ?? 0,
      hasValue,
    };
  });

  const hasAnyThroughput = chartData.some((d) => d.hasValue);

  if (!hasAnyThroughput) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Throughput Comparison</h3>
              <p className="text-[11px] text-slate-500">Generation speed (unit: tokens / second)</p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-500 rounded">
            No Telemetry
          </span>
        </div>
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-100 flex flex-col items-center justify-center">
          <AlertCircle className="w-5 h-5 text-slate-400 mb-1.5" />
          <p className="text-xs font-medium text-slate-700">
            Throughput Telemetry Unavailable
          </p>
          <p className="text-[11px] text-slate-500 max-w-md mt-1">
            Generation speed is only displayed when the provider supplies verified output token counts and duration metrics. Values are never fabricated.
          </p>
        </div>
      </div>
    );
  }

  const BAR_COLORS = ['#10B981', '#059669', '#047857', '#065F46', '#064E3B'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Measured Throughput Comparison</h3>
            <p className="text-[11px] text-slate-500">Inference speed measured in tokens per second</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
          Unit: tok/s
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
              tickFormatter={(v) => `${v} tok/s`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-lg border border-slate-800">
                      <div className="font-semibold text-slate-200 mb-1">{d.name}</div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <span>Measured Throughput:</span>
                        {d.hasValue ? (
                          <span className="font-bold text-emerald-400">{d.tps} tok/s</span>
                        ) : (
                          <span className="font-medium text-slate-400 italic">Not available</span>
                        )}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="displayTps" radius={[6, 6, 0, 0]} maxBarSize={56}>
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

