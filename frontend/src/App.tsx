/**
 * App.tsx — RAKSHYA VISION Phase 8
 * Root Application Shell for AI Vision-Based Safety Monitoring SOC Dashboard.
 */

import React, { useState } from 'react';
import { NavigationTab, Alert } from './types';
import { useSafetyData } from './hooks/useSafetyData';
import { useWebSocket } from './hooks/useWebSocket';
import { Header } from './components/Header';
import { OverviewView } from './pages/OverviewView';
import { CamerasView } from './pages/CamerasView';
import { WorkersView } from './pages/WorkersView';
import { HazardsView } from './pages/HazardsView';
import { AlertsView } from './pages/AlertsView';
import { AnalyticsView } from './pages/AnalyticsView';
import { SettingsView } from './pages/SettingsView';
import { AlertDetailModal } from './components/AlertDetailModal';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('overview');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

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
  } = useSafetyData();

  const { status: wsStatus } = useWebSocket(handleWebSocketMessage);

  return (
    <div className="soc-layout">
      {/* Top Header & Navigation */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        systemStatus={status}
        wsStatus={wsStatus}
        activeAlertsCount={summary?.active_alerts ?? alerts.filter((a) => a.status === 'ACTIVE').length}
        onRefresh={refreshAll}
        isRefreshing={isLoading}
      />

      {/* Global Action Notifications Banner */}
      {actionSuccess && (
        <div className="toast-notification toast-success">
          <div className="toast-content">
            <CheckCircle2 size={16} />
            <span>{actionSuccess}</span>
          </div>
          <button className="toast-close" onClick={clearBanner}>
            <X size={14} />
          </button>
        </div>
      )}

      {actionError && (
        <div className="toast-notification toast-error">
          <div className="toast-content">
            <AlertTriangle size={16} />
            <span>{actionError}</span>
          </div>
          <button className="toast-close" onClick={clearBanner}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main View Router */}
      <main className="soc-main-content">
        {currentTab === 'overview' && (
          <OverviewView
            summary={summary}
            alerts={alerts}
            hazards={hazards}
            cameras={cameras}
            onNavigate={setCurrentTab}
            onSelectAlert={(a) => setSelectedAlert(a)}
            onAcknowledge={handleAcknowledge}
            onResolve={handleResolve}
            onDismiss={handleDismiss}
          />
        )}

        {currentTab === 'cameras' && (
          <CamerasView cameras={cameras} hazardConfig={hazardConfig} onRefreshCameras={refreshAll} />
        )}

        {currentTab === 'workers' && (
          <WorkersView complianceConfig={complianceConfig} />
        )}

        {currentTab === 'hazards' && (
          <HazardsView hazards={hazards} hazardConfig={hazardConfig} />
        )}

        {currentTab === 'alerts' && (
          <AlertsView
            alerts={alerts}
            incidents={incidents}
            summary={summary}
            onAcknowledge={handleAcknowledge}
            onResolve={handleResolve}
            onDismiss={handleDismiss}
          />
        )}

        {currentTab === 'analytics' && (
          <AnalyticsView alerts={alerts} incidents={incidents} summary={summary} />
        )}

        {currentTab === 'settings' && (
          <SettingsView complianceConfig={complianceConfig} hazardConfig={hazardConfig} />
        )}
      </main>

      {/* Global Alert Detail Modal (from Overview or any view) */}
      <AlertDetailModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={handleAcknowledge}
        onResolve={handleResolve}
        onDismiss={handleDismiss}
      />
    </div>
  );
};

export default App;
