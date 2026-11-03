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
import { CheckSquare, AlertCircle } from 'lucide-react';
import { ModelSummary } from '../../types/evaluationResults';

interface ExactMatchComparisonChartProps {
  modelSummaries: ModelSummary[];
}

export const ExactMatchComparisonChart: React.FC<ExactMatchComparisonChartProps> = ({
  modelSummaries,
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center text-center min-h-[280px]">
        <AlertCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Exact Match Data</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Exact match scores will display once evaluated.
        </p>
      </div>
    );
  }

  // Filter models that have exact_match metric
  const chartData = modelSummaries.map((m) => {
    const rawVal = m.metrics.exact_match;
    const hasValue = rawVal !== undefined && rawVal !== null;
    const normalizedScore = hasValue
      ? Number((rawVal <= 1.0 ? rawVal * 100 : rawVal).toFixed(1))
      : null;

    return {
      name: m.name || m.model_id,
      model_id: m.model_id,
      score: normalizedScore,
      hasValue,
      rawScore: rawVal,
    };
  });

  const allMissing = chartData.every((d) => !d.hasValue);
  if (allMissing) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Exact Match Comparison</h3>
            <p className="text-[11px] text-slate-500">Strict string and pattern equality verification</p>
          </div>
        </div>
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-100">
          <p className="text-xs font-medium text-slate-600">
            No exact_match evaluator was connected in this run.
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Connect an Exact Match Evaluator node to view strict string comparisons.
          </p>
        </div>
      </div>
    );
  }

  const BAR_COLORS = ['#0D9488', '#0284C7', '#2563EB', '#14B8A6', '#065F46'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Exact Match Comparison</h3>
            <p className="text-[11px] text-slate-500">Normalized percentage of strict reference matches</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-teal-50 text-teal-700 rounded border border-teal-200">
          Exact Match
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData.map((d) => ({
              ...d,
              displayScore: d.hasValue ? d.score : 0,
            }))}
            margin={{ top: 15, right: 20, left: 0, bottom: 25 }}
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
              domain={[0, 100]}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-lg border border-slate-800">
                      <div className="font-semibold text-slate-200 mb-1">{d.name}</div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <span>Exact Match:</span>
                        {d.hasValue ? (
                          <span className="font-bold text-teal-400">{d.score}%</span>
                        ) : (
                          <span className="font-medium text-slate-400 italic">Not evaluated</span>
                        )}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="displayScore" radius={[6, 6, 0, 0]} maxBarSize={56}>
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
