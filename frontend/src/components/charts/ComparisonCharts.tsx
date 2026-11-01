import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ComparisonChartsProps {
  data: Array<{
    model: string;
    accuracy: number;
    latency_ms: number;
    tokens_per_sec?: number;
    pass_rate: number;
  }>;
}

export const ComparisonCharts: React.FC<ComparisonChartsProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-[#94A3B8] border border-[#E2E8F0] rounded-lg bg-white">
        Run an evaluation with 2 or more models to render comparison charts.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    name: d.model,
    'Pass Rate (%)': Math.round(d.pass_rate * 100),
    'Accuracy (%)': Math.round(d.accuracy * 100),
    'Avg Latency (ms)': Math.round(d.latency_ms),
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Accuracy & Pass Rate Bar Chart */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
        <h4 className="text-xs font-semibold text-[#111827] mb-1">
          Quality & Accuracy Comparison
        </h4>
        <p className="text-[11px] text-[#64748B] mb-3">
          Controlled benchmark pass rate on identical test cases
        </p>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748B' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E2E8F0',
                  fontSize: '11px',
                  borderRadius: '6px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Bar dataKey="Pass Rate (%)" fill="#2563EB" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Accuracy (%)" fill="#16A34A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency Comparison Chart */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
        <h4 className="text-xs font-semibold text-[#111827] mb-1">
          Inference Latency (ms)
        </h4>
        <p className="text-[11px] text-[#64748B] mb-3">
          Average measured roundtrip request duration (lower is faster)
        </p>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E2E8F0',
                  fontSize: '11px',
                  borderRadius: '6px',
                }}
              />
              <Bar dataKey="Avg Latency (ms)" fill="#D97706" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
