import React from 'react';
import {
  PlaySquare,
  FlaskConical,
  Cpu,
  BookmarkCheck,
  Database,
  Trophy,
  Settings as SettingsIcon,
  BarChart3,
} from 'lucide-react';

export type NavigationTab =
  | 'playground'
  | 'results'
  | 'experiments'
  | 'models'
  | 'benchmarks'
  | 'datasets'
  | 'leaderboard'
  | 'settings';

interface NavigationSidebarProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
}

interface NavItem {
  id: NavigationTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'playground', label: 'Playground', icon: PlaySquare },
  { id: 'results', label: 'Evaluation Results', icon: BarChart3 },
  { id: 'experiments', label: 'Experiments', icon: FlaskConical },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'benchmarks', label: 'Benchmarks', icon: BookmarkCheck },
  { id: 'datasets', label: 'Datasets', icon: Database },
  { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

export const NavigationSidebar: React.FC<NavigationSidebarProps> = ({
  activeTab,
  onTabChange,
}) => {
  return (
    <aside className="w-56 bg-white border-r border-[#E2E8F0] flex flex-col justify-between p-3 select-none shrink-0 z-10">
      <div className="space-y-1">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8] px-2 py-1.5">
          Platform
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]'
                  : 'text-[#64748B] hover:text-[#111827] hover:bg-[#F8FAFC]'
              }`}
            >
              <Icon
                className={`w-4 h-4 ${isActive ? 'text-[#2563EB]' : 'text-[#64748B]'}`}
              />
              <span>{item.label}</span>
              {item.id === 'playground' && (
                <span className="ml-auto text-[9px] font-mono px-1.5 py-0.2 rounded bg-white text-[#2563EB] border border-[#BFDBFE]">
                  Main
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="border-t border-[#E2E8F0] pt-3 px-2 text-[11px] text-[#94A3B8]">
        <div>Local-First Engine</div>
        <div className="font-mono text-[10px] text-[#64748B] mt-0.5">Ollama @ 11434</div>
      </div>
    </aside>
  );
};
