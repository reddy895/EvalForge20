import React, { useState } from 'react';
import { TrendingUp } from 'lucide-react';

export interface TrendPoint {
  date: string;
  passRate: number; // 0 to 100
  latencyMs?: number | null;
  modelName?: string;
  suiteName?: string;
  runId?: string;
}

export interface HistoricalTrendsChartProps {
  points: TrendPoint[];
  title?: string;
  description?: string;
}

/**
 * Chart 5: Run History
 * Clean, minimal 2D line chart displaying metric changes across completed runs.
 * Labels time axis and metric axis without connecting unrelated models or incompatible suites.
 */
export const HistoricalTrendsChart: React.FC<HistoricalTrendsChartProps> = ({
  points,
  title = 'Run History & Metric Trends',
  description = 'Metric trajectory across sequential evaluation runs',
}) => {
  const [metricMode, setMetricMode] = useState<'passRate' | 'latency'>('passRate');
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  // Filter valid points for selected metric
  const validPoints = (points || []).filter((pt) => {
    if (metricMode === 'passRate') {
      return typeof pt.passRate === 'number' && !isNaN(pt.passRate);
    }
    return typeof pt.latencyMs === 'number' && !isNaN(pt.latencyMs) && pt.latencyMs > 0;
  });

  if (validPoints.length === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#D9823B]/10 text-[#D9823B] flex items-center justify-center">
          <TrendingUp size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            {metricMode === 'latency'
              ? 'No valid latency measurements recorded for this run sequence. Switch to pass rate or execute a benchmark.'
              : 'No historical evaluation runs recorded. Run an evaluation suite to build a trajectory of model performance over time.'}
          </p>
        </div>
      </div>
    );
  }

  // Calculate SVG ViewBox dimensions
  const width = 500;
  const height = 180;
  const paddingLeft = 45;
  const paddingRight = 20;
  const paddingTop = 25;
  const paddingBottom = 35;
  const plotWidth = width - paddingLeft - paddingRight;
  const plotHeight = height - paddingTop - paddingBottom;

  // Determine Y range
  let minY = 0;
  let maxY = 100;
  if (metricMode === 'latency') {
    const latencies = validPoints.map((p) => p.latencyMs as number);
    minY = 0;
    maxY = Math.max(50, Math.ceil(Math.max(...latencies) * 1.2));
  }

  // Calculate coordinates for points
  const coords = validPoints.map((pt, i) => {
    const x =
      validPoints.length === 1
        ? paddingLeft + plotWidth / 2
        : paddingLeft + (i / (validPoints.length - 1)) * plotWidth;

    const val = metricMode === 'passRate' ? pt.passRate : (pt.latencyMs || 0);
    const normalizedY = (val - minY) / (maxY - minY || 1);
    const y = paddingTop + plotHeight - normalizedY * plotHeight;

    return { x, y, pt, val };
  });

  // Construct SVG Path line
  const pathD = coords
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`)
    .join(' ');

  // Y-axis grid ticks (4 ticks)
  const yTicks = [
    { val: maxY, y: paddingTop },
    { val: Math.round((maxY + minY) / 2), y: paddingTop + plotHeight / 2 },
    { val: minY, y: paddingTop + plotHeight },
  ];

  const activeColor = metricMode === 'passRate' ? '#68B587' : '#D9823B';

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-5">
      {/* Header with Metric Mode Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <TrendingUp size={16} className="text-[#68B587]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>

        {/* Metric Toggle: Pass Rate (%) vs Latency (ms) */}
        <div className="flex items-center gap-1 bg-[#161715] p-1 rounded-xl border border-white/5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setMetricMode('passRate')}
            className={`px-3 py-1 rounded-lg transition-colors ${
              metricMode === 'passRate'
                ? 'bg-[#242522] text-[#68B587] font-semibold'
                : 'text-[#A7A29A] hover:text-[#F5F0E7]'
            }`}
          >
            Pass Rate (%)
          </button>
          <button
            type="button"
            onClick={() => setMetricMode('latency')}
            className={`px-3 py-1 rounded-lg transition-colors ${
              metricMode === 'latency'
                ? 'bg-[#242522] text-[#D9823B] font-semibold'
                : 'text-[#A7A29A] hover:text-[#F5F0E7]'
            }`}
          >
            Latency (ms)
          </button>
        </div>
      </div>

      {/* 2D Line Chart SVG Canvas */}
      <div className="relative w-full overflow-hidden bg-[#161715] rounded-2xl border border-white/5 p-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
        >
          {/* Subtle Gridlines */}
          {yTicks.map((t, idx) => (
            <g key={idx}>
              <line
                x1={paddingLeft}
                y1={t.y}
                x2={width - paddingRight}
                y2={t.y}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeDasharray="3 3"
              />
              <text
                x={paddingLeft - 8}
                y={t.y + 3}
                fill="#A7A29A"
                fontSize="10"
                fontFamily="monospace"
                textAnchor="end"
              >
                {t.val}
                {metricMode === 'passRate' ? '%' : 'ms'}
              </text>
            </g>
          ))}

          {/* Metric Trend Line */}
          {coords.length > 1 && (
            <path
              d={pathD}
              fill="none"
              stroke={activeColor}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data Points */}
          {coords.map((c, idx) => (
            <g
              key={idx}
              className="cursor-pointer"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <circle
                cx={c.x}
                cy={c.y}
                r={hoveredIdx === idx ? 6 : 4}
                fill={activeColor}
                stroke="#161715"
                strokeWidth="2"
                className="transition-all duration-200"
              />
              {/* Point Label / Date on X Axis */}
              <text
                x={c.x}
                y={height - 12}
                fill="#A7A29A"
                fontSize="9"
                fontFamily="monospace"
                textAnchor="middle"
              >
                {c.pt.date.length > 8 ? c.pt.date.slice(0, 8) : c.pt.date}
              </text>
            </g>
          ))}
        </svg>

        {/* Active Point Tooltip */}
        {hoveredIdx !== null && coords[hoveredIdx] && (
          <div
            className="absolute z-20 px-3 py-1.5 rounded-xl bg-[#292A26] border border-white/10 text-[11px] font-mono text-[#F5F0E7] shadow-xl pointer-events-none"
            style={{
              left: `${Math.min(75, Math.max(10, (coords[hoveredIdx].x / width) * 100))}%`,
              top: '15%',
            }}
          >
            <div>Run Date: <strong>{coords[hoveredIdx].pt.date}</strong></div>
            <div>
              {metricMode === 'passRate'
                ? `Pass Rate: ${coords[hoveredIdx].val.toFixed(1)}%`
                : `Mean Latency: ${coords[hoveredIdx].val.toFixed(1)} ms`}
            </div>
            {coords[hoveredIdx].pt.modelName && (
              <div className="text-[#A7A29A]">Model: {coords[hoveredIdx].pt.modelName}</div>
            )}
          </div>
        )}
      </div>

      {/* Axis Description */}
      <div className="flex justify-between items-center text-[10px] font-mono text-[#78766F] pt-1">
        <span>Vertical: {metricMode === 'passRate' ? 'Accuracy Pass Rate (0–100%)' : 'Response Latency (ms)'}</span>
        <span>Horizontal: Sequential Run Progression</span>
      </div>
    </div>
  );
};
