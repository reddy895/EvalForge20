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
import { Target, AlertCircle } from 'lucide-react';
import { ModelSummary } from '../../types/evaluationResults';

interface AccuracyComparisonChartProps {
  modelSummaries: ModelSummary[];
}

export const AccuracyComparisonChart: React.FC<AccuracyComparisonChartProps> = ({
  modelSummaries,
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center text-center min-h-[280px]">
        <AlertCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="text-sm font-semibold text-slate-700">No Accuracy Data Available</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Accuracy calculations will appear here once model evaluation completes.
        </p>
      </div>
    );
  }

  const chartData = modelSummaries.map((m) => {
    const accuracyVal =
      m.metrics.accuracy !== undefined && m.metrics.accuracy !== null
        ? Number((m.metrics.accuracy * (m.metrics.accuracy <= 1.0 ? 100 : 1)).toFixed(1))
        : Number(m.pass_rate.toFixed(1));

    return {
      name: m.name || m.model_id,
      model_id: m.model_id,
      accuracy: accuracyVal,
      passed: m.passed_cases,
      total: m.total_cases,
    };
  });

  const BAR_COLORS = ['#2563EB', '#0D9488', '#6366F1', '#0284C7', '#4F46E5'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Overall Accuracy Comparison</h3>
            <p className="text-[11px] text-slate-500">Evaluated test case success rate across models</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
          {modelSummaries.length} {modelSummaries.length === 1 ? 'Model' : 'Models'}
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 15, right: 20, left: 0, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis
              dataKey="name"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              interval={0}
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
                        <span>Accuracy:</span>
                        <span className="font-bold text-emerald-400">{d.accuracy}%</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {d.passed} / {d.total} cases passed
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="accuracy" radius={[6, 6, 0, 0]} maxBarSize={56}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
