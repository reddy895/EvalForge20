import React, { useState, useMemo } from 'react';
import type { RunSummary } from '../../api/types';
import './ScoreHistoryChart.css';

interface ScoreHistoryChartProps {
  runs: RunSummary[];
  isLoading?: boolean;
}

export const ScoreHistoryChart: React.FC<ScoreHistoryChartProps> = ({ runs, isLoading }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const dataPoints = useMemo(() => {
    return runs
      .filter((r) => r.pass_rate !== null && r.pass_rate !== undefined)
      .map((r) => ({
        id: r.run_id,
        name: r.name,
        date: r.completed_at || r.started_at || '',
        score: Number(r.pass_rate),
      }))
      .reverse(); // chronological: oldest to newest
  }, [runs]);

  const width = 600;
  const height = 180;
  const padding = { top: 20, right: 30, bottom: 25, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const points = useMemo(() => {
    if (dataPoints.length < 2) return [];

    return dataPoints.map((d, index) => {
      const x = padding.left + (index / (dataPoints.length - 1)) * chartW;
      const y = padding.top + (1 - Math.max(0, Math.min(1, d.score))) * chartH;
      return { ...d, x, y };
    });
  }, [dataPoints, chartW, chartH, padding]);

  const pathD = useMemo(() => {
    if (points.length < 2) return '';
    return points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`, '');
  }, [points]);

  if (isLoading) {
    return (
      <div className="chart-card">
        <div className="chart-card-header">
          <span className="chart-card-title">Performance History</span>
        </div>
        <div className="chart-empty-state">
          <span>Loading performance telemetry...</span>
        </div>
      </div>
    );
  }

  if (dataPoints.length < 2) {
    return (
      <div className="chart-card">
        <div className="chart-card-header">
          <span className="chart-card-title">Performance History</span>
          <span className="chart-card-meta">Metric: Pass Rate</span>
        </div>
        <div className="chart-empty-state">
          <span>Insufficient historical runs to compute score progression.</span>
          <span style={{ fontSize: '11px', marginTop: '4px', color: 'var(--text-muted)' }}>
            Run at least two evaluations to generate historical trend curves.
          </span>
        </div>
      </div>
    );
  }

  const hoveredPoint = hoveredIndex !== null ? points[hoveredIndex] : null;

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <span className="chart-card-title">Performance History</span>
        <span className="chart-card-meta">{points.length} runs evaluated</span>
      </div>

      <div className="chart-container">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="chart-svg"
          preserveAspectRatio="none"
        >
          {/* Gridlines */}
          {[1.0, 0.75, 0.5, 0.25, 0.0].map((ratio) => {
            const y = padding.top + (1 - ratio) * chartH;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  className="chart-grid-line"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  className="chart-axis-label"
                >
                  {Math.round(ratio * 100)}%
                </text>
              </g>
            );
          })}

          {/* Sparkline Line without gradients */}
          <path d={pathD} className="chart-line" />

          {/* Interactive Data Points */}
          {points.map((p, idx) => (
            <circle
              key={p.id}
              cx={p.x}
              cy={p.y}
              r={hoveredIndex === idx ? 4.5 : 3}
              className="chart-point"
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
            />
          ))}
        </svg>

        {hoveredPoint && (
          <div
            className="chart-tooltip font-mono"
            style={{
              left: `${(hoveredPoint.x / width) * 100}%`,
              top: `${(hoveredPoint.y / height) * 100}%`,
            }}
          >
            <div><strong>{hoveredPoint.name}</strong></div>
            <div>Score: {(hoveredPoint.score * 100).toFixed(1)}%</div>
            {hoveredPoint.date && (
              <div style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                {new Date(hoveredPoint.date).toLocaleDateString()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
