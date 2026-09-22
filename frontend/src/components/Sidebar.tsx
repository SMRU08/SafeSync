import React from 'react';

export type ActiveTab =
  | 'overview'
  | 'cameras'
  | 'workers'
  | 'hazards'
  | 'alerts'
  | 'analytics'
  | 'health'
  | 'settings'
  | 'simulation';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  activeAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  activeAlertsCount = 3,
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
        {/* Overview */}
        <button
          onClick={() => onTabChange('overview')}
          className={`w-full text-left ${getNavClass('overview')}`}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
          </svg>
          <span>Overview</span>
        </button>

        {/* Live Monitoring / Cameras */}
        <button
          onClick={() => onTabChange('cameras')}
          className={`w-full text-left ${getNavClass('cameras')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Cameras &amp; Feeds</span>
        </button>

        {/* Workers & PPE */}
        <button
          onClick={() => onTabChange('workers')}
          className={`w-full text-left ${getNavClass('workers')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Workers &amp; PPE</span>
        </button>

        {/* Fire & Smoke */}
        <button
          onClick={() => onTabChange('hazards')}
          className={`w-full text-left ${getNavClass('hazards')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Fire &amp; Smoke</span>
        </button>

        {/* Alerts & Incidents */}
        <button
          onClick={() => onTabChange('alerts')}
          className={`w-full text-left justify-between ${getNavClass('alerts')}`}
        >
          <div className="flex items-center gap-3">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
              />
            </svg>
            <span>Alerts &amp; Incidents</span>
          </div>
          {activeAlertsCount > 0 && (
            <span className="w-4 h-4 rounded-full bg-rose-500 text-[9px] font-bold text-white flex items-center justify-center">
              {activeAlertsCount}
            </span>
          )}
        </button>

        {/* Analytics */}
        <button
          onClick={() => onTabChange('analytics')}
          className={`w-full text-left ${getNavClass('analytics')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Analytics</span>
        </button>

        {/* System Health */}
        <button
          onClick={() => onTabChange('health')}
          className={`w-full text-left ${getNavClass('health')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M13 10V3L4 14h7v7l9-11h-7z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>System Health</span>
        </button>

        {/* Configuration */}
        <button
          onClick={() => onTabChange('settings')}
          className={`w-full text-left ${getNavClass('settings')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
            <path
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Configuration</span>
        </button>

        {/* Live Simulation */}
        <button
          onClick={() => onTabChange('simulation')}
          className={`w-full text-left ${getNavClass('simulation')}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
            <path
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
          </svg>
          <span>Live Simulation</span>
        </button>
      </nav>

      {/* Sidebar Footer Safety Card */}
      <div className="p-3">
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-b from-[#162744] to-[#0f1c30] p-3 border border-slate-700/60 shadow-lg">
          <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:8px_8px]" />
          <div className="relative z-10 flex flex-col gap-2">
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-400/20 flex items-center justify-center text-sky-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.8"
                />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-200 leading-snug">
                Safer People
                <br />
                Safer Workplaces
                <br />
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
