/**
 * Sidebar.tsx — SafeSync Modern Industrial SOC
 * Interactive Navigation Sidebar with upward sliding hover animation,
 * glowing active indicators, live alert count badges, and telemetry footer.
 */

import React from 'react';
import {
  LayoutDashboard,
  Tv,
  Camera,
  Users,
  Flame,
  AlertTriangle,
  BarChart3,
  Activity,
  Settings,
  UserCheck,
  Shield,
} from 'lucide-react';

export type ActiveTab =
  | 'overview'
  | 'live-monitor'
  | 'cameras'
  | 'workers'
  | 'attendance'
  | 'hazards'
  | 'alerts'
  | 'analytics'
  | 'health'
  | 'settings';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  activeAlertsCount?: number;
}

interface NavItem {
  id: ActiveTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColor?: string;
  badge?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  activeAlertsCount = 0,
}) => {
  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'live-monitor', label: 'Live Monitor', icon: Tv },
    { id: 'cameras', label: 'Cameras', icon: Camera },
    { id: 'workers', label: 'Workers & PPE', icon: Users },
    { id: 'attendance', label: 'Attendance', icon: UserCheck, iconColor: 'text-emerald-400' },
    { id: 'hazards', label: 'Fire & Smoke', icon: Flame, iconColor: 'text-amber-400' },
    {
      id: 'alerts',
      label: 'Alerts & Incidents',
      icon: AlertTriangle,
      iconColor: 'text-rose-400',
      badge: activeAlertsCount,
    },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'health', label: 'System Health', icon: Activity },
    { id: 'settings', label: 'Configuration', icon: Settings },
  ];

  return (
    <aside className="w-60 bg-[#090e1a] text-slate-300 flex flex-col justify-between flex-shrink-0 border-r border-slate-800/80 shadow-2xl select-none z-20">
      {/* Navigation Links */}
      <nav className="p-3.5 space-y-1.5 overflow-y-auto">
        <div className="px-2 pb-2 mb-1 border-b border-slate-800/60 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Control Console
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            Live
          </span>
        </div>

        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`group w-full flex items-center justify-between px-3 py-2.5 rounded-xl font-medium text-xs cursor-pointer
                transition-all duration-200 ease-out transform hover:-translate-y-1
                ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-600 via-sky-600 to-sky-700 text-white shadow-lg shadow-sky-600/30 border border-sky-400/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/70 border border-transparent hover:border-slate-700/60 shadow-sm'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-110 ${
                    isActive ? 'text-white' : item.iconColor || 'text-slate-400 group-hover:text-sky-400'
                  }`}
                />
                <span className="tracking-tight">{item.label}</span>
              </div>

              {typeof item.badge === 'number' && item.badge > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-rose-500/90 text-white text-[10px] font-bold font-mono shadow-sm animate-pulse">
                  {item.badge > 99 ? '99+' : item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Control Room Footer Banner */}
      <div className="p-3 border-t border-slate-800/70">
        <div className="glass-card rounded-xl p-3 border border-slate-700/60 relative overflow-hidden group">
          <div className="absolute -right-4 -bottom-4 w-16 h-16 bg-sky-500/10 rounded-full blur-xl group-hover:bg-sky-500/20 transition-all duration-500 pointer-events-none" />
          <div className="relative z-10 flex items-start gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-sky-950/80 border border-sky-700/60 flex items-center justify-center text-sky-400 flex-shrink-0 mt-0.5">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[11px] font-bold text-slate-200 leading-tight">SafeSync Core</p>
              <p className="text-[9px] text-slate-400 mt-0.5">Active Visual Safety AI</p>
              <p className="text-[8px] font-mono text-emerald-400 mt-1 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Zero Incident Target
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
