import React, { useState, useEffect } from 'react';
import { ActiveTab, Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { SocOverview } from './components/SocOverview';
import { CamerasFeed } from './components/CamerasFeed';
import { WorkersMonitoring } from './components/WorkersMonitoring';
import { FireSmokeHazard } from './components/FireSmokeHazard';
import { AlertsTriage } from './components/AlertsTriage';
import { AnalyticsTrends } from './components/AnalyticsTrends';
import { SystemHealth } from './components/SystemHealth';
import { ConfigurationSettings } from './components/ConfigurationSettings';
import { EscalationSimulation } from './components/EscalationSimulation';
import './styles/custom-theme.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [showQuickNav, setShowQuickNav] = useState<boolean>(false);

  // Synchronize with URL hash for easy bookmarking and external linking
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (
        hash === 'overview' ||
        hash === 'cameras' ||
        hash === 'workers' ||
        hash === 'hazards' ||
        hash === 'alerts' ||
        hash === 'analytics' ||
        hash === 'health' ||
        hash === 'settings' ||
        hash === 'simulation'
      ) {
        setActiveTab(hash as ActiveTab);
      }
    };

    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    window.location.hash = tab;
  };

  return (
    <div className="flex flex-col w-full h-screen overflow-hidden bg-[#eef3f9]">
      {/* Exact Custom Top Header */}
      <TopHeader unreadAlertsCount={3} />

      {/* Main Container: Sidebar + Active View */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Exact Custom Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          activeAlertsCount={3}
        />

        {/* View Surface: 100% Exact Custom Design Replication */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#eef3f9]">
          {activeTab === 'overview' && <SocOverview onNavigate={handleTabChange} />}
          {activeTab === 'cameras' && <CamerasFeed onNavigate={handleTabChange} />}
          {activeTab === 'workers' && <WorkersMonitoring onNavigate={handleTabChange} />}
          {activeTab === 'hazards' && <FireSmokeHazard onNavigate={handleTabChange} />}
          {activeTab === 'alerts' && <AlertsTriage onNavigate={handleTabChange} />}
          {activeTab === 'analytics' && <AnalyticsTrends onNavigate={handleTabChange} />}
          {activeTab === 'health' && <SystemHealth onNavigate={handleTabChange} />}
          {activeTab === 'settings' && <ConfigurationSettings onNavigate={handleTabChange} />}
          {activeTab === 'simulation' && <EscalationSimulation onNavigate={handleTabChange} />}

          {/* Discreet Quick View Switcher Pill */}
          <div className="absolute bottom-3 right-4 z-40">
            {showQuickNav && (
              <div className="mb-2 bg-slate-900/95 backdrop-blur border border-slate-700 p-2 rounded-xl shadow-2xl flex flex-col gap-1 w-52 text-xs">
                <div className="text-[10px] font-bold text-sky-400 px-2 py-1 uppercase tracking-wider border-b border-slate-800">
                  Select Custom Screen
                </div>
                {[
                  { key: 'overview', label: '1. SOC Overview' },
                  { key: 'cameras', label: '2. Cameras & Feeds' },
                  { key: 'workers', label: '3. Workers & PPE' },
                  { key: 'hazards', label: '4. Fire & Smoke' },
                  { key: 'alerts', label: '5. Alerts & Triage' },
                  { key: 'analytics', label: '6. Analytics & Trends' },
                  { key: 'health', label: '7. System Health' },
                  { key: 'settings', label: '8. Configuration' },
                  { key: 'simulation', label: '9. Live Simulation' },
                ].map((s) => (
                  <button
                    key={s.key}
                    onClick={() => {
                      handleTabChange(s.key as ActiveTab);
                      setShowQuickNav(false);
                    }}
                    className={`text-left px-2 py-1.5 rounded text-[11px] font-medium transition ${
                      activeTab === s.key
                        ? 'bg-sky-600 text-white font-semibold'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
            <button
              onClick={() => setShowQuickNav(!showQuickNav)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-full shadow-lg text-[11px] font-medium transition cursor-pointer"
              title="Quick Jump between Custom Screens"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Screen: <strong className="text-sky-400 capitalize">{activeTab}</strong></span>
              <svg className={`w-3 h-3 transition-transform ${showQuickNav ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M5 15l7-7 7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
              </svg>
            </button>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
