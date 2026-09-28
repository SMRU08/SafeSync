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
      if (
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

  const activeAlertsCount =
    summary?.active_alerts ?? alerts.filter((a) => a.status === 'ACTIVE').length;

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
      />

      {/* ─── CRITICAL ALERT BANNER (Sticky, pulsing red) ─────────────────────── */}
      {(() => {
        const fireHazard = hazards.find(
          (h) => h.hazard_type === 'fire' && (h.state === 'CONFIRMED' || h.state === 'ACTIVE')
        );
        const smokeHazard = hazards.find(
          (h) => h.hazard_type === 'smoke' && (h.state === 'CONFIRMED' || h.state === 'ACTIVE')
        );
        const evaluatingHazard = hazards.find(
          (h) => h.state === 'CANDIDATE' || h.state === 'DETECTING'
        );
        const criticalAlert = alerts.find(
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
          activeAlertsCount={activeAlertsCount}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />

        {/* Main Content Router Surface */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#070b14]">
          <div className="flex-1 flex flex-col overflow-hidden relative">
            {activeTab === 'overview' && (
              <OverviewView
                summary={summary}
                alerts={alerts}
                hazards={hazards}
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
              />
            )}

            {activeTab === 'cameras' && (
              <CamerasView
                cameras={cameras}
                hazardConfig={hazardConfig}
                onRefreshCameras={refreshAll}
                onToggleSpeaker={handleToggleSpeaker}
              />
            )}

            {activeTab === 'workers' && (
              <WorkersView
                complianceConfig={complianceConfig}
                onOpenEnrollModal={() => setIsEnrollModalOpen(true)}
              />
            )}

            {activeTab === 'attendance' && (
              <AttendanceView cameras={cameras} />
            )}

            {activeTab === 'hazards' && (
              <HazardsView hazards={hazards} hazardConfig={hazardConfig} />
            )}

            {activeTab === 'alerts' && (
              <AlertsView
                alerts={alerts}
                incidents={incidents}
                summary={summary}
                onAcknowledge={handleAcknowledge}
                onResolve={handleResolve}
                onDismiss={handleDismiss}
                onRefresh={refreshAll}
                onSelectAlert={(a) => setSelectedAlert(a)}
                onSelectIncident={handleOpenIncident}
              />
            )}

            {activeTab === 'analytics' && (
              <AnalyticsView
                alerts={alerts}
                incidents={incidents}
                summary={summary}
                analyticsData={analyticsData}
                onRefresh={refreshAll}
              />
            )}

            {activeTab === 'health' && <SystemHealthView wsStatus={wsStatus} />}

            {activeTab === 'settings' && (
              <SettingsView
                complianceConfig={complianceConfig}
                hazardConfig={hazardConfig}
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
    </div>
  );
};

export default App;
