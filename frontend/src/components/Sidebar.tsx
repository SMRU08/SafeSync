/**
 * Sidebar.tsx — RAKSHYA VISION Professional SOC
 * Deep industrial navy sidebar with 9 navigation tabs, dynamic alert badge,
 * and plant safety footer card.
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
  Shield,
} from 'lucide-react';

export type ActiveTab =
  | 'overview'
  | 'live-monitor'
  | 'cameras'
  | 'workers'
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

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  activeAlertsCount = 0,
}) => {
  const getNavClass = (tab: ActiveTab) => {
    if (activeTab === tab) {
      return 'flex items-center gap-3 px-3 py-2 rounded-lg bg-sky-600 text-white font-medium text-[11px] shadow-sm shadow-sky-600/30 cursor-pointer transition';
    }
    return 'flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-800/60 hover:text-white text-slate-400 transition text-[11px] font-medium cursor-pointer';
  };

  return (
    <aside className="w-56 bg-[#0c1a2e] text-slate-300 flex flex-col justify-between flex-shrink-0 border-r border-slate-800 select-none">
      {/* Navigation Links */}
      <nav className="p-3 space-y-1">
        {/* 1. Overview */}
        <button
          onClick={() => onTabChange('overview')}
          className={`w-full text-left ${getNavClass('overview')}`}
        >
          <LayoutDashboard className="w-4 h-4 flex-shrink-0" />
          <span>Overview</span>
        </button>

        {/* 2. Live Monitoring */}
        <button
          onClick={() => onTabChange('live-monitor')}
          className={`w-full text-left ${getNavClass('live-monitor')}`}
        >
          <Tv className="w-4 h-4 flex-shrink-0" />
          <span>Live Monitor</span>
        </button>

        {/* 3. Cameras */}
        <button
          onClick={() => onTabChange('cameras')}
          className={`w-full text-left ${getNavClass('cameras')}`}
        >
          <Camera className="w-4 h-4 flex-shrink-0" />
          <span>Cameras</span>
        </button>

        {/* 4. Workers & PPE */}
        <button
          onClick={() => onTabChange('workers')}
          className={`w-full text-left ${getNavClass('workers')}`}
        >
          <Users className="w-4 h-4 flex-shrink-0" />
          <span>Workers &amp; PPE</span>
        </button>

        {/* 5. Fire & Smoke */}
        <button
          onClick={() => onTabChange('hazards')}
          className={`w-full text-left ${getNavClass('hazards')}`}
        >
          <Flame className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>Fire &amp; Smoke</span>
        </button>

        {/* 6. Alerts & Incidents */}
        <button
          onClick={() => onTabChange('alerts')}
          className={`w-full text-left justify-between ${getNavClass('alerts')}`}
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>Alerts &amp; Incidents</span>
          </div>
          {activeAlertsCount > 0 && (
            <span className="w-4 h-4 rounded-full bg-rose-500 text-[9px] font-bold text-white flex items-center justify-center">
              {activeAlertsCount > 9 ? '9+' : activeAlertsCount}
            </span>
          )}
        </button>

        {/* 7. Analytics */}
        <button
          onClick={() => onTabChange('analytics')}
          className={`w-full text-left ${getNavClass('analytics')}`}
        >
          <BarChart3 className="w-4 h-4 flex-shrink-0" />
          <span>Analytics</span>
        </button>

        {/* 8. System Health */}
        <button
          onClick={() => onTabChange('health')}
          className={`w-full text-left ${getNavClass('health')}`}
        >
          <Activity className="w-4 h-4 flex-shrink-0" />
          <span>System Health</span>
        </button>

        {/* 9. Configuration */}
        <button
          onClick={() => onTabChange('settings')}
          className={`w-full text-left ${getNavClass('settings')}`}
        >
          <Settings className="w-4 h-4 flex-shrink-0" />
          <span>Configuration</span>
        </button>
      </nav>

      {/* Sidebar Footer Safety Card */}
      <div className="p-3">
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-b from-[#162744] to-[#0f1c30] p-3 border border-slate-700/60 shadow-lg">
          <div className="relative z-10 flex flex-col gap-2">
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-400/20 flex items-center justify-center text-sky-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-200 leading-snug">
                Safer People<br />
                Safer Workplaces<br />
                A Safer Tomorrow
              </p>
            </div>
            <div className="pt-2 border-t border-slate-700/50 flex items-center gap-2">
              <div className="w-4 h-4 rounded text-sky-400 flex items-center justify-center">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                </svg>
              </div>
              <div>
                <p className="text-[9px] font-bold text-slate-300">RAKSHYA VISION</p>
                <p className="text-[8px] text-slate-500">v1.0.0 Team XERSES</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
