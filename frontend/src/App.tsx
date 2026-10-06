/**
 * App.tsx — SafeSync Professional SOC
 * Enterprise Industrial Safety Operations Center Root Application Shell.
 * Integrates real-time FastAPI endpoints, live WebSocket telemetry,
 * real multi-camera streams, ByteTrack PPE compliance HUD, and smart alert triage.
 */

import React, { useState, useEffect } from 'react';
import { TopHeader } from './components/TopHeader';
import { Sidebar, ActiveTab } from './components/Sidebar';
import { OverviewView } from './pages/OverviewView';
import { LiveMonitoringView } from './pages/LiveMonitoringView';
import { CamerasView } from './pages/CamerasView';
import { WorkersView } from './pages/WorkersView';
import { AttendanceView } from './pages/AttendanceView';
import { HazardsView } from './pages/HazardsView';
import { AlertsView } from './pages/AlertsView';
import { AnalyticsView } from './pages/AnalyticsView';
import { SystemHealthView } from './pages/SystemHealthView';
import { SettingsView } from './pages/SettingsView';
import { AlertDetailModal } from './components/AlertDetailModal';
import { IncidentDetailModal } from './components/IncidentDetailModal';
import { WorkerRegistrationModal } from './components/WorkerRegistrationModal';
import { GlobalSearchModal } from './components/GlobalSearchModal';
import { NotificationDrawer } from './components/NotificationDrawer';
import { SystemStatusBar } from './components/SystemStatusBar';
import { DemoTopBanner, DemoScenarioId } from './components/DemoTopBanner';
import { HackathonDemoModal } from './components/HackathonDemoModal';
import { DEMO_SCENARIOS } from './utils/demoScenarios';
import { useSafetyData } from './hooks/useSafetyData';
import { useWebSocket } from './hooks/useWebSocket';
import { Alert, Incident } from './types';
import { CheckCircle2, AlertTriangle, X, Flame, ShieldAlert } from 'lucide-react';
import './styles/custom-theme.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [cameraSubTab, setCameraSubTab] = useState<'matrix' | 'entry_gate'>('matrix');

  // Hackathon Demo Mode State (Phase 10)
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [demoScenario, setDemoScenario] = useState<DemoScenarioId>('safe_worker');
  const [isDemoGuideOpen, setIsDemoGuideOpen] = useState<boolean>(false);

  // Theme Management (Default Dark Industrial Mode, with Light mode support & persistence)
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('safesync_theme');
    return saved === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
    localStorage.setItem('safesync_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Real-time backend data & WebSocket hooks
  const {
    status,
    summary,
    alerts,
    incidents,
    hazards,
    cameras,
    complianceConfig,
    hazardConfig,
    analyticsData,
    isLoading,
    actionError,
    actionSuccess,
    clearBanner,
    refreshAll,
    handleWebSocketMessage,
    handleAcknowledge,
    handleResolve,
    handleDismiss,
    handleAcknowledgeIncident,
    handleResolveIncident,
    handleToggleSpeaker,
  } = useSafetyData();

  const { status: wsStatus } = useWebSocket(handleWebSocketMessage);

  // URL hash synchronization for deep linking and back button support
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (hash === 'cameras/entry-gate' || hash === 'entry-gate') {
        setActiveTab('cameras');
        setCameraSubTab('entry_gate');
      } else if (
        hash === 'overview' ||
        hash === 'live-monitor' ||
        hash === 'cameras' ||
        hash === 'workers' ||
        hash === 'attendance' ||
        hash === 'hazards' ||
        hash === 'alerts' ||
        hash === 'analytics' ||
        hash === 'health' ||
        hash === 'settings'
      ) {
        setActiveTab(hash as ActiveTab);
        if (hash === 'cameras') setCameraSubTab('matrix');
      }
    };

    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const handleTabChange = (tab: ActiveTab, subTab?: 'matrix' | 'entry_gate') => {
    setActiveTab(tab);
    if (tab === 'cameras' && subTab) {
      setCameraSubTab(subTab);
      window.location.hash = subTab === 'entry_gate' ? 'cameras/entry-gate' : 'cameras';
    } else {
      if (tab === 'cameras') {
        setCameraSubTab('matrix');
      }
      window.location.hash = tab;
    }
  };

  // Effective scenario data in Demo Mode (Phase 10)
  const currentScenario = isDemoMode ? DEMO_SCENARIOS[demoScenario] : null;
  const effectiveAlerts = currentScenario ? currentScenario.alerts : alerts;
  const effectiveHazards = currentScenario ? currentScenario.hazards : hazards;

  const activeAlertsCount = isDemoMode && currentScenario
    ? effectiveAlerts.filter((a) => a.status === 'ACTIVE').length
    : (summary?.active_alerts ?? alerts.filter((a) => a.status === 'ACTIVE').length);

  const handleOpenIncident = (incidentId: string) => {
    const found = incidents.find((inc) => inc.incident_id === incidentId);
    if (found) {
      setSelectedIncident(found);
    } else {
      setSelectedIncident({
        incident_id: incidentId,
        status: 'OPEN',
        event_types: [],
        camera_id: '',
        zone_id: '',
        risk_score: 0,
        risk_level: 'MEDIUM',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Incident);
    }
  };

  const activeCamerasCount = cameras.filter(
    (c) => c.state === 'CONNECTED' || c.status === 'ACTIVE'
  ).length;

  return (
    <div className="flex flex-col w-full h-screen overflow-hidden bg-[#070b14] text-slate-100 antialiased font-sans select-none">
      {/* ─── Top Header with Live Status Indicators & Theme Toggle ───────────── */}
      <TopHeader
        apiStatus={status?.backend === 'healthy' ? 'online' : status?.backend === 'checking' ? 'checking' : 'offline'}
        aiEngineStatus={status?.aiEngine || 'Ready'}
        databaseStatus={status?.database === 'connected' ? 'connected' : status?.database === 'checking' ? 'checking' : 'disconnected'}
        wsStatus={wsStatus}
        unreadAlertsCount={activeAlertsCount}
        onRefresh={refreshAll}
        isRefreshing={isLoading}
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenNotifications={() => setIsNotificationsOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
        onNavigateHealth={() => handleTabChange('health')}
        isDemoMode={isDemoMode}
        onToggleDemoMode={() => setIsDemoMode((prev) => !prev)}
        onOpenDemoGuide={() => setIsDemoGuideOpen(true)}
      />

      {/* ─── DEMO MODE TOP BANNER (Phase 10) ───────────────────────────────── */}
      {isDemoMode && (
        <DemoTopBanner
          activeScenario={demoScenario}
          onSelectScenario={(scId: DemoScenarioId) => setDemoScenario(scId)}
          onOpenDemoGuide={() => setIsDemoGuideOpen(true)}
          onExitDemo={() => setIsDemoMode(false)}
        />
      )}

      {/* ─── GLOBAL BACKEND-OFFLINE BANNER (Honest Failover) ────────────────── */}
      {status?.backend === 'offline' && !isDemoMode && (
        <div className="w-full px-4 py-2 bg-gradient-to-r from-rose-950 via-slate-900 to-rose-950 border-b border-rose-500/40 text-xs font-semibold text-rose-200 flex items-center justify-between z-30 select-none shadow-md">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 animate-pulse" />
            <span>
              <strong className="text-white">SAFESYNC BACKEND UNAVAILABLE</strong> &mdash; Live monitoring cannot currently be confirmed.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => refreshAll()}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 text-[11px] font-bold transition cursor-pointer"
            >
              RETRY
            </button>
            <button
              onClick={() => setIsDemoMode(true)}
              className="px-2.5 py-1 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 text-[11px] font-black transition cursor-pointer shadow-sm"
            >
              EXPLORE IN DEMO MODE
            </button>
          </div>
        </div>
      )}

      {/* ─── CRITICAL ALERT BANNER (Sticky, pulsing red) ─────────────────────── */}
      {(() => {
        const fireHazard = effectiveHazards.find(
          (h) => h.hazard_type === 'fire' && (h.state === 'CONFIRMED' || h.state === 'ACTIVE')
        );
        const smokeHazard = effectiveHazards.find(
          (h) => h.hazard_type === 'smoke' && (h.state === 'CONFIRMED' || h.state === 'ACTIVE')
        );
        const evaluatingHazard = effectiveHazards.find(
          (h) => h.state === 'CANDIDATE' || h.state === 'DETECTING'
        );
        const criticalAlert = effectiveAlerts.find(
          (a) => a.status === 'ACTIVE' && (a.severity === 'CRITICAL' || a.severity === 'HIGH')
        );
        const bannerText = fireHazard
          ? `🔥 CRITICAL: Fire Confirmed — ${fireHazard.camera_id?.toUpperCase() ?? 'Unknown Camera'}! Evacuate immediately.`
          : smokeHazard
          ? `💨 WARNING: Smoke Confirmed — ${smokeHazard.camera_id?.toUpperCase() ?? 'Unknown Camera'}! Investigate now.`
          : evaluatingHazard
          ? `🔍 NOTICE: Hazard candidate under temporal evaluation (${evaluatingHazard.hazard_type?.toUpperCase()} - ${evaluatingHazard.state}) — ${evaluatingHazard.camera_id}`
          : criticalAlert
          ? `⚠️ ALERT: ${criticalAlert.title || criticalAlert.event_type.replace(/_/g, ' ')} — ${criticalAlert.camera_id}`
          : null;
        const isFireOrSmoke = !!(fireHazard || smokeHazard);

        if (!bannerText) return null;

        return (
          <div
            className={`w-full px-4 py-2 flex items-center justify-between text-xs font-bold tracking-wide select-none z-30 transition-all ${
              isFireOrSmoke
                ? 'bg-rose-600 text-white animate-pulse shadow-lg shadow-rose-900/40'
                : criticalAlert
                ? 'bg-amber-500 text-slate-950 font-extrabold shadow-md'
                : 'bg-sky-950 border-b border-sky-800 text-sky-200'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              {isFireOrSmoke ? (
                <Flame className="w-4 h-4 shrink-0 animate-bounce" />
              ) : (
                <ShieldAlert className="w-4 h-4 shrink-0" />
              )}
              <span className="truncate">{bannerText}</span>
            </div>

            <div className="flex items-center gap-2 shrink-0 ml-2">
              <button
                onClick={() => {
                  if (criticalAlert) setSelectedAlert(criticalAlert);
                  else handleTabChange('hazards');
                }}
                className="px-2.5 py-0.5 rounded text-[10px] font-black uppercase bg-black/30 hover:bg-black/50 text-white transition"
              >
                Inspect
              </button>
            </div>
          </div>
        );
      })()}

      {/* Floating Action Notifications */}
      {actionSuccess && (
        <div className="fixed top-16 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg shadow-lg animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionSuccess}</span>
          <button onClick={clearBanner} className="ml-2 hover:opacity-75">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {actionError && (
        <div className="fixed top-16 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 bg-rose-600 text-white text-xs font-semibold rounded-lg shadow-lg animate-in fade-in slide-in-from-top-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{actionError}</span>
          <button onClick={clearBanner} className="ml-2 hover:opacity-75">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ─── Main Body: Left Sidebar + Active View Surface ──────────────────── */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Dark Navy Industrial Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          cameraSubTab={cameraSubTab}
          activeAlertsCount={activeAlertsCount}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          onOpenDemoGuide={() => setIsDemoGuideOpen(true)}
        />

        {/* Main Content Router Surface */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#070b14]">
          <div className="flex-1 flex flex-col overflow-hidden relative">
            {activeTab === 'overview' && (
              <OverviewView
                summary={summary}
                alerts={effectiveAlerts}
                hazards={effectiveHazards}
                cameras={cameras}
                onNavigate={handleTabChange}
                onSelectAlert={(a) => setSelectedAlert(a)}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
                onDismiss={handleDismiss}
                onRefresh={refreshAll}
                onToggleSpeaker={handleToggleSpeaker}
              />
            )}

            {activeTab === 'live-monitor' && (
              <LiveMonitoringView
                cameras={cameras}
                onRefresh={refreshAll}
                onNavigateCameras={() => handleTabChange('cameras')}
                isDemoMode={isDemoMode}
                demoScenario={demoScenario}
                onOpenDemoGuide={() => setIsDemoGuideOpen(true)}
              />
            )}

            {activeTab === 'cameras' && (
              <CamerasView
                cameras={cameras}
                hazardConfig={hazardConfig}
                onRefreshCameras={refreshAll}
                onToggleSpeaker={handleToggleSpeaker}
                initialSubTab={cameraSubTab}
                onSubTabChange={setCameraSubTab}
              />
            )}

            {activeTab === 'workers' && (
              <WorkersView
                complianceConfig={complianceConfig}
                cameras={cameras}
                alerts={alerts}
                incidents={incidents}
                onNavigate={handleTabChange}
                onOpenEnrollModal={() => setIsEnrollModalOpen(true)}
              />
            )}

            {activeTab === 'attendance' && (
              <AttendanceView cameras={cameras} />
            )}

            {activeTab === 'hazards' && (
              <HazardsView
                hazards={effectiveHazards}
                hazardConfig={hazardConfig}
                cameras={cameras}
                onNavigate={handleTabChange}
                onSelectIncident={handleOpenIncident}
                onRefresh={refreshAll}
                isBackendHealthy={status?.backend === 'healthy'}
              />
            )}

            {activeTab === 'alerts' && (
              <AlertsView
                alerts={effectiveAlerts}
                incidents={incidents}
                cameras={cameras}
                summary={summary}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
                onDismiss={handleDismiss}
                onRefresh={refreshAll}
                onSelectAlert={(a) => setSelectedAlert(a)}
                onSelectIncident={handleOpenIncident}
                onNavigate={handleTabChange}
              />
            )}

            {activeTab === 'analytics' && (
              <AnalyticsView
                alerts={alerts}
                incidents={incidents}
                summary={summary}
                analyticsData={analyticsData}
                cameras={cameras}
                onRefresh={refreshAll}
              />
            )}

            {activeTab === 'health' && <SystemHealthView wsStatus={wsStatus} />}

            {activeTab === 'settings' && (
              <SettingsView
                complianceConfig={complianceConfig}
                hazardConfig={hazardConfig}
                cameras={cameras}
                onNavigate={handleTabChange}
              />
            )}
          </div>

          {/* ─── Persistent System Status Bar (Phase 30) ──────────────────────── */}
          <SystemStatusBar
            apiStatus={status?.backend === 'healthy' ? 'online' : status?.backend === 'checking' ? 'checking' : 'offline'}
            aiEngineStatus={status?.aiEngine || 'Ready'}
            databaseStatus={status?.database === 'connected' ? 'connected' : status?.database === 'checking' ? 'checking' : 'disconnected'}
            wsStatus={wsStatus}
            camerasCount={cameras.length}
            activeCamerasCount={activeCamerasCount}
            lastChecked={status?.lastChecked}
            onNavigate={handleTabChange}
          />
        </main>
      </div>

      {/* ─── Global Command Palette Search Modal (Phase 19) ────────────────── */}
      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        cameras={cameras}
        alerts={alerts}
        incidents={incidents}
        onNavigate={handleTabChange}
        onSelectAlert={(a) => setSelectedAlert(a)}
        onSelectIncident={handleOpenIncident}
      />

      {/* ─── Global Notification Center Drawer (Phase 20) ─────────────────── */}
      <NotificationDrawer
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        alerts={alerts}
        onSelectAlert={(a) => setSelectedAlert(a)}
        onAcknowledgeAlert={handleAcknowledge}
        onResolveAlert={handleResolve}
      />

      {/* ─── Global Alert Detail & Verification Modal ───────────────────────── */}
      <AlertDetailModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={handleAcknowledge}
        onResolve={handleResolve}
        onDismiss={handleDismiss}
        onSelectIncident={handleOpenIncident}
      />

      {/* ─── Global Incident Investigation & Snapshot Evidence Modal ───────── */}
      <IncidentDetailModal
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
        onSelectAlert={(alertId) => {
          const found = alerts.find((a) => a.alert_id === alertId);
          if (found) {
            setSelectedIncident(null);
            setSelectedAlert(found);
          }
        }}
        onAcknowledgeIncident={handleAcknowledgeIncident}
        onResolveIncident={handleResolveIncident}
      />

      {/* ─── Worker Biometric Enrollment Modal ───────────────────────────── */}
      <WorkerRegistrationModal
        isOpen={isEnrollModalOpen}
        onClose={() => setIsEnrollModalOpen(false)}
        cameras={cameras}
        onSuccess={() => {
          setIsEnrollModalOpen(false);
          refreshAll();
        }}
      />

      {/* ─── Hackathon Demo & Architecture Guide Modal (Phase 10) ──────────── */}
      <HackathonDemoModal
        isOpen={isDemoGuideOpen}
        onClose={() => setIsDemoGuideOpen(false)}
        onSelectDemoScenario={(scId: DemoScenarioId) => {
          setIsDemoMode(true);
          setDemoScenario(scId);
        }}
        onNavigateTab={(tab) => handleTabChange(tab as ActiveTab)}
        activeScenario={demoScenario}
        isDemoMode={isDemoMode}
        onToggleDemoMode={(enable) => setIsDemoMode(enable)}
      />
    </div>
  );
};

export default App;
