/**
 * useSafetyData.ts — RAKSHYA VISION Phase 8
 * Custom hook orchestrating live safety metrics, alerts, camera metadata, and incident lifecycles.
 * Reacts automatically to WebSocket pushes and exposes explicit action dispatchers.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  RiskSummary,
  Alert,
  Incident,
  HazardEventDetail,
  CameraConfig,
  WebSocketMessage,
} from '../types';
import {
  fetchHealth,
  fetchRiskSummary,
  fetchAlerts,
  fetchIncidents,
  fetchHazards,
  fetchHazardConfig,
  fetchComplianceConfig,
  acknowledgeAlert,
  resolveAlert,
  dismissAlert,
} from '../services/api';

export interface SystemStatusState {
  backend: 'healthy' | 'offline' | 'checking';
  database: 'connected' | 'disconnected' | 'checking';
  aiEngine: string;
  lastChecked: string;
}

export function useSafetyData() {
  const [status, setStatus] = useState<SystemStatusState>({
    backend: 'checking',
    database: 'checking',
    aiEngine: 'Initializing',
    lastChecked: '',
  });

  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [hazards, setHazards] = useState<HazardEventDetail[]>([]);
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [complianceConfig, setComplianceConfig] = useState<any>(null);
  const [hazardConfig, setHazardConfig] = useState<any>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    const nowStr = new Date().toLocaleTimeString();

    // 1. Health check
    try {
      const healthData = await fetchHealth();
      setStatus({
        backend: healthData.status === 'healthy' ? 'healthy' : 'offline',
        database: healthData.database === 'connected' || healthData.database_connected ? 'connected' : 'disconnected',
        aiEngine: healthData.ai_engine || (healthData.model_loaded ? 'Connected' : 'Ready'),
        lastChecked: nowStr,
      });
    } catch {
      setStatus({
        backend: 'offline',
        database: 'disconnected',
        aiEngine: 'Unavailable',
        lastChecked: nowStr,
      });
    }

    // 2. Risk summary
    try {
      const sum = await fetchRiskSummary();
      setSummary(sum);
    } catch {
      setSummary(null);
    }

    // 3. Alerts
    try {
      const alertList = await fetchAlerts({ limit: 100 });
      setAlerts(alertList);
    } catch {
      setAlerts([]);
    }

    // 4. Incidents
    try {
      const incList = await fetchIncidents(undefined, 50);
      setIncidents(incList);
    } catch {
      setIncidents([]);
    }

    // 5. Hazards
    try {
      const hazardList = await fetchHazards();
      setHazards(hazardList);
    } catch {
      setHazards([]);
    }

    // 6. Hazard & Camera Config
    try {
      const hConfig = await fetchHazardConfig();
      setHazardConfig(hConfig);
      if (hConfig && hConfig.cameras) {
        const mappedCameras: CameraConfig[] = hConfig.cameras.map((c: any) => ({
          camera_id: c.camera_id,
          name: c.name || `Camera ${c.camera_id}`,
          zone_id: c.zone_id,
          status: 'ACTIVE',
          resolution: '1280x720',
          fps: 30,
          rtsp_url: c.rtsp_url,
        }));
        setCameras(mappedCameras);
      }
    } catch {
      setHazardConfig(null);
    }

    // 7. Compliance Config
    try {
      const cConfig = await fetchComplianceConfig();
      setComplianceConfig(cConfig);
    } catch {
      setComplianceConfig(null);
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    refreshAll();
    const intervalId = window.setInterval(refreshAll, 10000);
    return () => clearInterval(intervalId);
  }, [refreshAll]);

  // Handle incoming live WebSocket event message
  const handleWebSocketMessage = useCallback(
    (msg: WebSocketMessage) => {
      if (msg.type === 'event' && msg.event) {
        // Refresh alerts and summary immediately
        fetchRiskSummary().then(setSummary).catch(() => {});
        fetchAlerts({ limit: 100 }).then(setAlerts).catch(() => {});
        fetchIncidents(undefined, 50).then(setIncidents).catch(() => {});
        fetchHazards().then(setHazards).catch(() => {});
      }
    },
    []
  );

  // Actions
  const handleAcknowledge = async (alertId: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await acknowledgeAlert(alertId);
      setActionSuccess(`Alert ${alertId} acknowledged successfully.`);
      // Optimistic update
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
      );
      // Refresh summary
      fetchRiskSummary().then(setSummary).catch(() => {});
    } catch (err: any) {
      setActionError(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  const handleResolve = async (alertId: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await resolveAlert(alertId);
      setActionSuccess(`Alert ${alertId} resolved.`);
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: 'RESOLVED' } : a))
      );
      fetchRiskSummary().then(setSummary).catch(() => {});
      fetchIncidents(undefined, 50).then(setIncidents).catch(() => {});
    } catch (err: any) {
      setActionError(`Failed to resolve alert: ${err.message}`);
    }
  };

  const handleDismiss = async (alertId: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await dismissAlert(alertId);
      setActionSuccess(`Alert ${alertId} dismissed.`);
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: 'DISMISSED' } : a))
      );
      fetchRiskSummary().then(setSummary).catch(() => {});
    } catch (err: any) {
      setActionError(`Failed to dismiss alert: ${err.message}`);
    }
  };

  return {
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
    clearBanner: () => {
      setActionError(null);
      setActionSuccess(null);
    },
    refreshAll,
    handleWebSocketMessage,
    handleAcknowledge,
    handleResolve,
    handleDismiss,
  };
}
