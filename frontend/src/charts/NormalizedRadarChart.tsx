import React from 'react';

export interface CapabilityDimension {
  name: string;
  value: number;
}

export interface NormalizedRadarChartProps {
  modelName: string;
  dimensions: CapabilityDimension[];
}

export const NormalizedRadarChart: React.FC<NormalizedRadarChartProps> = ({
  modelName,
  dimensions,
}) => {
  if (!dimensions || dimensions.length === 0) {
    return (
      <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 text-center text-sm text-[#A7A29A]">
        No capability dimensions recorded for {modelName}.
      </div>
    );
  }

  const center = 100;
  const radius = 70;
  const angleStep = (Math.PI * 2) / dimensions.length;

  const getCoordinates = (value: number, index: number, maxVal = 100) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / maxVal) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  const polygonPoints = dimensions
    .map((d, i) => {
      const { x, y } = getCoordinates(d.value, i);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{modelName} — Capability Radar</h4>
          <p className="text-xs text-[#A7A29A]">Multi-axial competence map (normalized 0-100)</p>
        </div>
        <span className="text-xs font-mono text-[#D9823B] bg-[#161715] px-2.5 py-1 rounded-full border border-white/5">
          {dimensions.length} Axes
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        {/* SVG Radar Visual */}
        <div className="flex justify-center items-center py-2">
          <div className="w-52 h-52 relative">
            <svg className="w-full h-full" viewBox="0 0 200 200">
              {/* Concentric rings */}
              {[0.25, 0.5, 0.75, 1.0].map((level, i) => {
                const points = dimensions
                  .map((_, idx) => {
                    const { x, y } = getCoordinates(level * 100, idx);
                    return `${x},${y}`;
                  })
                  .join(' ');
                return (
                  <polygon
                    key={i}
                    points={points}
                    fill="none"
                    stroke="#41413B"
                    strokeWidth="1"
                    strokeOpacity={level === 1 ? '0.7' : '0.3'}
                  />
                );
              })}

              {/* Spoke lines */}
              {dimensions.map((_, idx) => {
                const { x, y } = getCoordinates(100, idx);
                return (
                  <line
                    key={idx}
                    x1={center}
                    y1={center}
                    x2={x}
                    y2={y}
                    stroke="#41413B"
                    strokeWidth="1"
                    strokeDasharray="2,2"
                  />
                );
              })}

              {/* Data polygon */}
              <polygon
                points={polygonPoints}
                fill="#D9823B"
                fillOpacity="0.25"
                stroke="#D9823B"
                strokeWidth="2"
              />

              {/* Dots */}
              {dimensions.map((d, idx) => {
                const { x, y } = getCoordinates(d.value, idx);
                return <circle key={idx} cx={x} cy={y} r="3" fill="#F5F0E7" stroke="#D9823B" strokeWidth="2" />;
              })}
            </svg>
          </div>
        </div>

        {/* Dimension score cards */}
        <div className="grid grid-cols-2 gap-2.5">
          {dimensions.map((d) => (
            <div key={d.name} className="p-3 bg-[#161715] rounded-2xl border border-white/5 flex flex-col justify-between">
              <p className="text-[11px] text-[#A7A29A] truncate">{d.name}</p>
              <div className="flex items-baseline justify-between mt-1.5">
                <p className="text-base font-mono font-bold text-[#F5F0E7]">{d.value}%</p>
                <div className="w-12 h-1.5 rounded-full bg-[#242522] overflow-hidden ml-2">
                  <div className="h-full bg-[#D9823B] rounded-full" style={{ width: `${d.value}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
