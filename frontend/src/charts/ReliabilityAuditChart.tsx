import React from 'react';
import { AlertTriangle, CheckCircle2, XCircle, Clock } from 'lucide-react';

export interface ReliabilityGroup {
  name: string;
  passed: number;
  failed: number;
  errored: number;
}

export interface ReliabilityAuditChartProps {
  // Aggregate run counts (from AnalyticsView)
  completedRuns?: number;
  failedRuns?: number;
  timeoutRuns?: number;
  reliabilityRate?: number;
  // Or multi-model/suite grouped case data
  data?: ReliabilityGroup[];
  title?: string;
  description?: string;
}

/**
 * Chart 3: Reliability Breakdown
 * Clean minimal grouped 2D bar chart showing actual counts of passed, failed, and errored cases.
 * Uses dedicated integer count axis (no mixing percentages and counts on an unlabeled axis).
 */
export const ReliabilityAuditChart: React.FC<ReliabilityAuditChartProps> = ({
  completedRuns = 0,
  failedRuns = 0,
  timeoutRuns = 0,
  reliabilityRate,
  data,
  title = 'Reliability Breakdown',
  description = 'Empirical execution outcomes showing verified passed, failed, and errored cases',
}) => {
  // Normalize into groups: if explicit data array provided, use it. Otherwise, create a group from run/case props.
  const groups: ReliabilityGroup[] =
    data && data.length > 0
      ? data
      : [
          {
            name: 'Execution Runs',
            passed: completedRuns,
            failed: failedRuns,
            errored: timeoutRuns,
          },
        ];

  const totalCasesAll = groups.reduce(
    (sum, g) => sum + g.passed + g.failed + g.errored,
    0
  );

  if (totalCasesAll === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#D9823B]/10 text-[#D9823B] flex items-center justify-center">
          <AlertTriangle size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            No execution cases recorded. Execute an evaluation run to view test reliability and error distribution.
          </p>
        </div>
      </div>
    );
  }

  // Find max count across all groups and series to scale the Y/X axis
  const maxCount = Math.max(
    ...groups.map((g) => Math.max(g.passed, g.failed, g.errored)),
    1
  );
  // Round up to nice integer ceiling
  const ceiling = Math.max(4, Math.ceil(maxCount * 1.2));
  const ticks = [0, Math.round(ceiling * 0.25), Math.round(ceiling * 0.5), Math.round(ceiling * 0.75), ceiling];

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      {/* Header with Series Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <CheckCircle2 size={16} className="text-[#68B587]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#68B587]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#68B587]" /> Passed
          </span>
          <span className="flex items-center gap-1.5 text-[#E06C75]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#E06C75]" /> Failed
          </span>
          <span className="flex items-center gap-1.5 text-[#D9823B]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#D9823B]" /> Errored
          </span>
        </div>
      </div>

      {/* Grouped 2D Bar Chart Layout */}
      <div className="space-y-4">
        {groups.map((group) => {
          const groupTotal = group.passed + group.failed + group.errored;
          const passedWidth = Math.max(0, (group.passed / ceiling) * 100);
          const failedWidth = Math.max(0, (group.failed / ceiling) * 100);
          const erroredWidth = Math.max(0, (group.errored / ceiling) * 100);

          return (
            <div
              key={group.name}
              className="p-4 bg-[#161715] rounded-2xl border border-white/5 space-y-3"
            >
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-[#F5F0E7]">{group.name}</span>
                <span className="font-mono text-[11px] text-[#A7A29A]">
                  Total: <strong className="text-[#F5F0E7]">{groupTotal}</strong> cases
                  {typeof reliabilityRate === 'number' && (
                    <span className="ml-2 text-[#68B587]">
                      ({reliabilityRate.toFixed(1)}% success)
                    </span>
                  )}
                </span>
              </div>

              {/* Grouped Bars Container */}
              <div className="space-y-2 pt-1">
                {/* 1. Passed Series Bar */}
                <div className="flex items-center gap-3 text-xs">
                  <span className="w-16 shrink-0 font-mono text-[11px] text-[#68B587] flex items-center gap-1">
                    <CheckCircle2 size={12} /> Passed
                  </span>
                  <div className="flex-1 relative flex items-center h-6 bg-[#1F201D] rounded-lg px-2 border border-white/5 overflow-hidden">
                    <div
                      className="h-3 bg-[#68B587] rounded transition-all duration-500"
                      style={{ width: `${Math.max(group.passed > 0 ? 2 : 0, passedWidth)}%` }}
                    />
                    <span className="ml-2 font-mono text-xs font-bold text-[#F5F0E7]">
                      {group.passed}
                    </span>
                  </div>
                </div>

                {/* 2. Failed Series Bar */}
                <div className="flex items-center gap-3 text-xs">
                  <span className="w-16 shrink-0 font-mono text-[11px] text-[#E06C75] flex items-center gap-1">
                    <XCircle size={12} /> Failed
                  </span>
                  <div className="flex-1 relative flex items-center h-6 bg-[#1F201D] rounded-lg px-2 border border-white/5 overflow-hidden">
                    <div
                      className="h-3 bg-[#E06C75] rounded transition-all duration-500"
                      style={{ width: `${Math.max(group.failed > 0 ? 2 : 0, failedWidth)}%` }}
                    />
                    <span className="ml-2 font-mono text-xs font-bold text-[#F5F0E7]">
                      {group.failed}
                    </span>
                  </div>
                </div>

                {/* 3. Errored / Timeout Series Bar */}
                <div className="flex items-center gap-3 text-xs">
                  <span className="w-16 shrink-0 font-mono text-[11px] text-[#D9823B] flex items-center gap-1">
                    <Clock size={12} /> Errored
                  </span>
                  <div className="flex-1 relative flex items-center h-6 bg-[#1F201D] rounded-lg px-2 border border-white/5 overflow-hidden">
                    <div
                      className="h-3 bg-[#D9823B] rounded transition-all duration-500"
                      style={{ width: `${Math.max(group.errored > 0 ? 2 : 0, erroredWidth)}%` }}
                    />
                    <span className="ml-2 font-mono text-xs font-bold text-[#F5F0E7]">
                      {group.errored}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Axis Scale and Unit */}
      <div className="pt-2 border-t border-white/5 flex flex-col gap-1">
        <div className="flex justify-between text-[10px] font-mono text-[#A7A29A] pl-20 pr-2">
          {ticks.map((t, idx) => (
            <span key={idx}>{t} cases</span>
          ))}
        </div>
        <div className="text-[11px] text-[#78766F] text-center font-mono">
          Horizontal Axis: Discrete Case Counts (Integer Scale)
        </div>
      </div>
    </div>
  );
};
