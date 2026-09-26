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
import { useSafetyData } from './hooks/useSafetyData';
import { useWebSocket } from './hooks/useWebSocket';
import { Alert, Incident } from './types';
import { CheckCircle2, AlertTriangle, X, Flame, Wind, ShieldAlert } from 'lucide-react';
import './styles/custom-theme.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);

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

  return (
    <div className="flex flex-col w-full h-screen overflow-hidden bg-[#eef3f9] text-slate-800 antialiased font-sans">
      {/* ─── Top Header with Live Status Indicators ─────────────────────────── */}
      <TopHeader
        apiStatus={status?.backend === 'healthy' ? 'online' : status?.backend === 'checking' ? 'checking' : 'offline'}
        aiEngineStatus={status?.aiEngine || 'Ready'}
        databaseStatus={status?.database === 'connected' ? 'connected' : status?.database === 'checking' ? 'checking' : 'disconnected'}
        wsStatus={wsStatus}
        unreadAlertsCount={activeAlertsCount}
        onRefresh={refreshAll}
        isRefreshing={isLoading}
      />

      {/* ─── CRITICAL ALERT BANNER (Sticky, pulsing red) ─────────────────────── */}
      {(() => {
        const fireHazard = hazards.find((h) => h.hazard_type === 'fire');
        const smokeHazard = hazards.find((h) => h.hazard_type === 'smoke');
        const criticalAlert = alerts.find(
          (a) => a.status === 'ACTIVE' && (a.severity === 'CRITICAL' || a.severity === 'HIGH')
        );
        const bannerText = fireHazard
          ? `🔥 CRITICAL: Fire Detected — ${fireHazard.camera_id?.toUpperCase() ?? 'Unknown Camera'}! Evacuate immediately.`
          : smokeHazard
          ? `💨 WARNING: Smoke Detected — ${smokeHazard.camera_id?.toUpperCase() ?? 'Unknown Camera'}! Investigate now.`
          : criticalAlert
          ? `⚠️ ALERT: ${criticalAlert.title || criticalAlert.event_type.replace(/_/g, ' ')} — ${criticalAlert.camera_id}`
          : null;
        const isFireOrSmoke = !!(fireHazard || smokeHazard);
        if (!bannerText) return null;
        return (
          <div
            className={`sticky top-0 z-[60] flex items-center justify-between gap-3 px-5 py-2.5 text-white text-sm font-bold shadow-lg select-none ${
              isFireOrSmoke
                ? 'bg-red-600 animate-pulse'
                : 'bg-rose-500'
            }`}
            style={isFireOrSmoke ? { animationDuration: '1s' } : {}}
          >
            <div className="flex items-center gap-3">
              {fireHazard ? (
                <Flame className="w-5 h-5 text-yellow-200 animate-bounce flex-shrink-0" />
              ) : smokeHazard ? (
                <Wind className="w-5 h-5 text-slate-100 flex-shrink-0" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-white flex-shrink-0" />
              )}
              <span className="tracking-wide">{bannerText}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-[11px] font-normal text-white/80 hidden sm:block">
                {new Date().toLocaleTimeString()}
              </span>
              <button
                onClick={() => setActiveTab('hazards')}
                className="px-2.5 py-1 bg-white/20 hover:bg-white/30 text-white text-[11px] font-bold rounded border border-white/30 transition"
              >
                View Details
              </button>
            </div>
          </div>
        );
      })()}

      {/* ─── Global Action Notification Toast Banner ─────────────────────────── */}

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
        />

        {/* Main Content Router Surface */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#eef3f9]">
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
            <LiveMonitoringView cameras={cameras} onRefresh={refreshAll} />
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
            <AnalyticsView alerts={alerts} incidents={incidents} summary={summary} />
          )}

          {activeTab === 'health' && <SystemHealthView />}

          {activeTab === 'settings' && (
            <SettingsView
              complianceConfig={complianceConfig}
              hazardConfig={hazardConfig}
            />
          )}
        </main>
      </div>

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
        }}
      />
    </div>
  );
};

export default App;
