import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { PieChart as PieChartIcon, CheckCircle2, XCircle, MinusCircle } from 'lucide-react';
import { EvaluationDistribution } from '../../types/evaluationResults';

interface EvaluationDistributionChartProps {
  distribution: EvaluationDistribution;
  totalCases: number;
}

export const EvaluationDistributionChart: React.FC<EvaluationDistributionChartProps> = ({
  distribution,
  totalCases,
}) => {
  const total = totalCases > 0 ? totalCases : distribution.passed + distribution.failed + distribution.skipped;

  const data = [
    { name: 'Passed', value: distribution.passed, color: '#10B981', icon: CheckCircle2 },
    { name: 'Failed', value: distribution.failed, color: '#F43F5E', icon: XCircle },
    { name: 'Skipped', value: distribution.skipped, color: '#94A3B8', icon: MinusCircle },
  ].filter((d) => d.value > 0);

  const passedPct = total > 0 ? ((distribution.passed / total) * 100).toFixed(1) : '0';
  const failedPct = total > 0 ? ((distribution.failed / total) * 100).toFixed(1) : '0';
  const skippedPct = total > 0 ? ((distribution.skipped / total) * 100).toFixed(1) : '0';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <PieChartIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Outcome Distribution</h3>
            <p className="text-[11px] text-slate-500">Breakdown of passed, failed, and skipped test cases</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-700 rounded">
          {total} Total Cases
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        {/* Donut Pie Chart */}
        <div className="h-44 relative flex items-center justify-center">
          {total > 0 && data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0];
                      const pct = total > 0 ? (((d.value as number) / total) * 100).toFixed(1) : '0';
                      return (
                        <div className="bg-slate-900 text-white text-xs rounded-lg p-2 shadow-lg border border-slate-800">
                          <span className="font-semibold text-slate-200">{d.name}: </span>
                          <span className="font-bold text-white">{d.value}</span> ({pct}%)
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-xs text-slate-400 italic">No evaluated cases</div>
          )}

          {/* Center Statistic */}
          {total > 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-xl font-bold text-slate-900">{passedPct}%</span>
              <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Pass Rate</span>
            </div>
          )}
        </div>

        {/* Detailed Count Legend */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50/60 border border-emerald-100">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold text-emerald-950">Passed</span>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-emerald-700">{distribution.passed}</span>
              <span className="text-[11px] text-emerald-600/80 ml-1.5">({passedPct}%)</span>
            </div>
          </div>

          <div className="flex items-center justify-between p-2 rounded-lg bg-rose-50/60 border border-rose-100">
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-rose-600" />
              <span className="text-xs font-semibold text-rose-950">Failed</span>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-rose-700">{distribution.failed}</span>
              <span className="text-[11px] text-rose-600/80 ml-1.5">({failedPct}%)</span>
            </div>
          </div>

          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="flex items-center gap-2">
              <MinusCircle className="w-4 h-4 text-slate-500" />
              <span className="text-xs font-semibold text-slate-800">Skipped / Pending</span>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-slate-700">{distribution.skipped}</span>
              <span className="text-[11px] text-slate-500 ml-1.5">({skippedPct}%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
