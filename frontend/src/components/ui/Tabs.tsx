import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
  size?: 'sm' | 'md';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className = '',
  size = 'md',
}) => {
  const containerPadding = size === 'sm' ? 'p-1 gap-1' : 'p-1.5 gap-1.5';
  const tabPadding = size === 'sm' ? 'px-3 py-1 text-xs' : 'px-4 py-2 text-sm';

  return (
    <div
      role="tablist"
      className={`inline-flex items-center rounded-full bg-[#191A18] border border-[#41413B] ${containerPadding} ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 rounded-full font-medium transition-all duration-150 outline-none select-none cursor-pointer ${tabPadding} ${
              isActive
                ? 'bg-[#242522] text-[#F5F0E7] border border-[#41413B] shadow-sm'
                : 'text-[#A6A49D] hover:text-[#F5F0E7] hover:bg-white/5 border border-transparent'
            }`}
          >
            {tab.icon && <span className="inline-flex shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                  isActive
                    ? 'bg-[#D9823B]/20 text-[#D9823B]'
                    : 'bg-[#41413B]/50 text-[#A6A49D]'
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
