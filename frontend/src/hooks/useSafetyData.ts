/**
 * useSafetyData.ts — SafeSync Phase 8
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
  SystemHealthSnapshot,
} from '../types';
import {
  fetchSystemHealth,
  fetchRiskSummary,
  fetchAlerts,
  fetchIncidents,
  fetchHazards,
  fetchHazardConfig,
  fetchComplianceConfig,
  fetchCameras,
  acknowledgeAlert,
  resolveAlert,
  dismissAlert,
  acknowledgeIncident,
  resolveIncident,
  toggleCameraSpeaker,
  fetchAnalyticsMetrics,
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
  const [systemHealth, setSystemHealth] = useState<SystemHealthSnapshot | null>(null);

  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [hazards, setHazards] = useState<HazardEventDetail[]>([]);
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [complianceConfig, setComplianceConfig] = useState<any>(null);
  const [hazardConfig, setHazardConfig] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    const nowStr = new Date().toLocaleTimeString();

    // 1. Health check
    try {
      const healthData = await fetchSystemHealth();
      setSystemHealth(healthData);

      // Determine Database status
      const isDbConnected =
        healthData.database?.status === 'connected' ||
        healthData.database?.reachable === true ||
        (healthData as any).database_connected === true;

      // Determine AI Engine status
      const aiStatusRaw = healthData.ai_engine?.status || (healthData as any).ai_status;
      const isAiAvailable =
        ['available', 'connected', 'ready', 'loaded', 'online'].includes(
          String(aiStatusRaw || '').toLowerCase()
        ) ||
        (healthData.ai_engine?.models_loaded ?? 0) > 0 ||
        (healthData as any).model_loaded === true;
      const aiLabel = isAiAvailable ? 'Ready' : 'Unavailable';

      // Determine API status
      const apiStatusRaw = healthData.api?.status || healthData.status;
      const isApiHealthy =
        apiStatusRaw === 'online' ||
        healthData.status === 'healthy' ||
        healthData.status === 'degraded' ||
        healthData.status === 'running';

      setStatus({
        backend: isApiHealthy ? 'healthy' : 'offline',
        database: isDbConnected ? 'connected' : 'disconnected',
        aiEngine: aiLabel,
        lastChecked: nowStr,
      });
    } catch {
      setSystemHealth(null);
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

    // 6. Hazard & Camera Manager
    try {
      const hConfig = await fetchHazardConfig();
      setHazardConfig(hConfig);

      // Fetch real multi-camera statuses from /api/cameras
      try {
        const realCameras = await fetchCameras();
        if (Array.isArray(realCameras) && realCameras.length > 0) {
          const mappedCameras: CameraConfig[] = realCameras.map((c: any) => ({
            camera_id: c.camera_id,
            name: c.name || `Camera ${c.camera_id}`,
            zone_id: c.zone_id,
            status:
              c.state === 'STREAMING' || c.state === 'CONNECTED' || c.is_streaming
                ? 'ACTIVE'
                : c.state === 'DISABLED'
                ? 'STANDBY'
                : c.state === 'DEGRADED'
                ? 'DEGRADED'
                : 'OFFLINE',
            state: c.state,
            is_streaming: c.is_streaming ?? (c.state === 'STREAMING'),
            last_frame_age_ms: c.last_frame_age_ms,
            frame_id: c.frame_id,
            last_frame_timestamp: c.last_frame_timestamp,
            source_type: c.source_type,
            enabled: c.enabled,
            resolution: '1280x720',
            fps: c.metrics?.fps || 0,
            safe_source: c.safe_source,
            metrics: c.metrics,
          }));
          setCameras(mappedCameras);
        } else if (hConfig && hConfig.cameras) {
          const fallbackCameras: CameraConfig[] = hConfig.cameras.map((c: any) => ({
            camera_id: c.camera_id,
            name: c.name || `Camera ${c.camera_id}`,
            zone_id: c.zone_id,
            status: 'ACTIVE',
            resolution: '1280x720',
            fps: 30,
            rtsp_url: c.rtsp_url,
          }));
          setCameras(fallbackCameras);
        }
      } catch {
        if (hConfig && hConfig.cameras) {
          const fallbackCameras: CameraConfig[] = hConfig.cameras.map((c: any) => ({
            camera_id: c.camera_id,
            name: c.name || `Camera ${c.camera_id}`,
            zone_id: c.zone_id,
            status: 'ACTIVE',
            resolution: '1280x720',
            fps: 30,
            rtsp_url: c.rtsp_url,
          }));
          setCameras(fallbackCameras);
        }
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

    // 8. Analytics Aggregations
    try {
      const aData = await fetchAnalyticsMetrics();
      setAnalyticsData(aData);
    } catch {
      // Keep previous state
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
        // Handle real-time analytics updates
        if (msg.event === 'AnalyticsUpdated' && msg.payload) {
          setAnalyticsData(msg.payload);
        }

        // Handle dynamic AudioAlert voice synthesis (Strictly Hindi Voice)
        if (msg.event === 'AudioAlert' && msg.payload) {
          const payload = msg.payload;
          const shouldSpeak =
            Boolean(payload.speaker_enabled) ||
            Boolean(payload.bypass_speaker) ||
            payload.action === 'CRITICAL_HAZARD_TRIGGERED';

          if (
            shouldSpeak &&
            payload.message &&
            typeof window !== 'undefined' &&
            'speechSynthesis' in window
          ) {
            try {
              window.speechSynthesis.cancel(); // Cancel any ongoing stutter
              const utterance = new SpeechSynthesisUtterance(payload.message);
              utterance.lang = 'hi-IN'; // Strictly Hindi voice format
              utterance.rate = 0.95;
              utterance.pitch = 1.0;

              // If browser provides native Hindi voice, attach it
              const voices = window.speechSynthesis.getVoices();
              const hindiVoice = voices.find(
                (v) => v.lang.startsWith('hi') || v.name.toLowerCase().includes('hindi')
              );
              if (hindiVoice) {
                utterance.voice = hindiVoice;
              }

              window.speechSynthesis.speak(utterance);
            } catch {
              // Ignore browser audio restrictions
            }
          }
        }

        // Refresh alerts and summary immediately
        fetchRiskSummary().then(setSummary).catch(() => {});
        fetchAlerts({ limit: 100 }).then(setAlerts).catch(() => {});
        fetchIncidents(undefined, 50).then(setIncidents).catch(() => {});
        fetchHazards().then(setHazards).catch(() => {});
        fetchAnalyticsMetrics().then(setAnalyticsData).catch(() => {});
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

  const handleAcknowledgeIncident = async (incidentId: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await acknowledgeIncident(incidentId);
      setActionSuccess(`Incident ${incidentId} acknowledged.`);
      setIncidents((prev) =>
        prev.map((inc) => (inc.incident_id === incidentId ? { ...inc, status: 'ACKNOWLEDGED' } : inc))
      );
      fetchAlerts({ limit: 100 }).then(setAlerts).catch(() => {});
      fetchRiskSummary().then(setSummary).catch(() => {});
    } catch (err: any) {
      setActionError(`Failed to acknowledge incident: ${err.message}`);
    }
  };

  const handleResolveIncident = async (incidentId: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await resolveIncident(incidentId);
      setActionSuccess(`Incident ${incidentId} resolved.`);
      setIncidents((prev) =>
        prev.map((inc) => (inc.incident_id === incidentId ? { ...inc, status: 'RESOLVED' } : inc))
      );
      fetchAlerts({ limit: 100 }).then(setAlerts).catch(() => {});
      fetchRiskSummary().then(setSummary).catch(() => {});
    } catch (err: any) {
      setActionError(`Failed to resolve incident: ${err.message}`);
    }
  };

  const handleToggleSpeaker = async (cameraId: string, enabled: boolean) => {
    try {
      await toggleCameraSpeaker(cameraId, enabled);
      setCameras((prev) =>
        prev.map((c) => (c.camera_id === cameraId ? { ...c, speaker_enabled: enabled } : c))
      );
      setActionSuccess(`Camera ${cameraId} speaker set to ${enabled ? 'ON' : 'OFF'}.`);
    } catch (err: any) {
      setActionError(`Failed to toggle camera speaker: ${err.message}`);
    }
  };

  return {
    status,
    systemHealth,
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
    clearBanner: () => {
      setActionError(null);
      setActionSuccess(null);
    },
    refreshAll,
    handleWebSocketMessage,
    handleAcknowledge,
    handleResolve,
    handleDismiss,
    handleAcknowledgeIncident,
    handleResolveIncident,
    handleToggleSpeaker,
  };
}
