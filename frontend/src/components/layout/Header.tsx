import React, { useState } from 'react';
import { NavRoute } from '../../types';
import { Button } from '../ui/Button';
import { Menu, X, Cpu, GitCompare, Play, History, Grid, Flame } from 'lucide-react';

interface HeaderProps {
  currentRoute: NavRoute;
  onRouteChange: (route: NavRoute) => void;
  onOpenModelDetail?: (modelId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentRoute, onRouteChange }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: { label: string; route: NavRoute; icon: React.ReactNode }[] = [
    { label: 'Overview', route: 'landing', icon: <Flame size={15} /> },
    { label: 'Catalog', route: 'models', icon: <Grid size={15} /> },
    { label: 'Compare', route: 'compare', icon: <GitCompare size={15} /> },
    { label: 'Evaluate', route: 'evaluate', icon: <Play size={15} /> },
    { label: 'History', route: 'history', icon: <History size={15} /> },
  ];

  const handleNavClick = (route: NavRoute) => {
    onRouteChange(route);
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <header className="sticky top-4 z-40 w-full px-4 sm:px-8 lg:px-12 2xl:px-16">
      <div className="flex items-center justify-between h-16 px-6 sm:px-8 rounded-full bg-[#191A18]/90 backdrop-blur-md border border-[#41413B] shadow-[0_8px_32px_rgba(0,0,0,0.36)] transition-all">
        {/* Brand */}
        <button
          onClick={() => handleNavClick('landing')}
          className="flex items-center gap-2.5 outline-none group cursor-pointer text-left"
        >
          <div className="w-8 h-8 rounded-full bg-[#242522] border border-[#41413B] flex items-center justify-center text-[#D9823B] group-hover:border-[#D9823B] transition-colors">
            <Cpu size={18} className="transform group-hover:scale-105 transition-transform" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-[#F5F0E7]">
              Eval<span className="text-[#D9823B]">Forge</span>20
            </span>
            <span className="text-[10px] text-[#A6A49D] font-mono leading-none">v2.0 • Local-First</span>
          </div>
        </button>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-1 bg-[#242522] p-1 rounded-full border border-[#41413B]/60">
          {navItems.map((item) => {
            const isActive = currentRoute === item.route;
            return (
              <button
                key={item.route}
                onClick={() => handleNavClick(item.route)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#191A18] text-[#F5F0E7] border border-[#41413B] shadow-sm'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7] hover:bg-white/5 border border-transparent'
                }`}
              >
                <span className={isActive ? 'text-[#D9823B]' : 'text-current opacity-70'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Action */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="primary"
            onClick={() => handleNavClick('evaluate')}
            className="hidden sm:inline-flex"
            iconRight={<Play size={12} className="fill-current" />}
          >
            Launch Studio
          </Button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-full text-[#A6A49D] hover:text-[#F5F0E7] hover:bg-[#242522] transition-colors cursor-pointer"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-2 p-3 rounded-2xl bg-[#191A18] border border-[#41413B] shadow-2xl flex flex-col gap-1.5 animate-in fade-in slide-in-from-top-2">
          {navItems.map((item) => {
            const isActive = currentRoute === item.route;
            return (
              <button
                key={item.route}
                onClick={() => handleNavClick(item.route)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors text-left ${
                  isActive
                    ? 'bg-[#242522] text-[#F5F0E7] border border-[#41413B]'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7] hover:bg-[#242522]'
                }`}
              >
                <span className={isActive ? 'text-[#D9823B]' : 'text-current'}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
          <div className="pt-2 border-t border-[#41413B] mt-1">
            <Button
              size="sm"
              variant="primary"
              className="w-full justify-center"
              onClick={() => handleNavClick('evaluate')}
              iconRight={<Play size={12} className="fill-current" />}
            >
              Launch Studio
            </Button>
          </div>
        </div>
      )}
    </header>
  );
};
