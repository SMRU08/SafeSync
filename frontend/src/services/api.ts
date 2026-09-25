/**
 * api.ts — RAKSHYA VISION Phase 8
 * Fully typed REST API client for backend communication.
 * Connects directly to FastAPI endpoints for health, compliance, hazards, and smart alerts.
 */

import { API_BASE_URL } from '../utils/constants';
import {
  BackendHealthResponse,
  RiskSummary,
  Alert,
  Incident,
  HazardEventDetail,
  EvidenceItem,
} from '../types';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Use fallback errorDetail
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// ─── Health & Detection Status ──────────────────────────────────────────────

export async function fetchHealth(): Promise<BackendHealthResponse> {
  return request<BackendHealthResponse>('/health');
}

export async function fetchDetectionHealth(): Promise<any> {
  return request<any>('/api/detection/health');
}

// ─── Risk & Smart Alerts ────────────────────────────────────────────────────

export async function fetchRiskSummary(): Promise<RiskSummary> {
  return request<RiskSummary>('/api/risk/summary');
}

export interface AlertFilters {
  status?: string;
  risk_level?: string;
  camera_id?: string;
  zone_id?: string;
  event_type?: string;
  limit?: number;
}

export async function fetchAlerts(filters: AlertFilters = {}): Promise<Alert[]> {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.risk_level) params.append('risk_level', filters.risk_level);
  if (filters.camera_id) params.append('camera_id', filters.camera_id);
  if (filters.zone_id) params.append('zone_id', filters.zone_id);
  if (filters.event_type) params.append('event_type', filters.event_type);
  if (filters.limit) params.append('limit', filters.limit.toString());

  const qs = params.toString();
  return request<Alert[]>(`/api/alerts${qs ? `?${qs}` : ''}`);
}

export async function fetchAlertDetail(alertId: string): Promise<Alert> {
  return request<Alert>(`/api/alerts/${alertId}`);
}

export async function acknowledgeAlert(alertId: string): Promise<any> {
  return request<any>(`/api/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
}

export async function resolveAlert(alertId: string): Promise<any> {
  return request<any>(`/api/alerts/${alertId}/resolve`, {
    method: 'POST',
  });
}

export async function dismissAlert(alertId: string): Promise<any> {
  return request<any>(`/api/alerts/${alertId}/dismiss`, {
    method: 'POST',
  });
}

// ─── Incidents ──────────────────────────────────────────────────────────────

export async function fetchIncidents(status?: string, limit: number = 50): Promise<Incident[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit.toString());

  return request<Incident[]>(`/api/incidents?${params.toString()}`);
}

export async function fetchIncidentDetail(incidentId: string): Promise<Incident> {
  return request<Incident>(`/api/incidents/${incidentId}`);
}

export async function acknowledgeIncident(incidentId: string): Promise<any> {
  return request<any>(`/api/incidents/${incidentId}/acknowledge`, {
    method: 'POST',
  });
}

export async function resolveIncident(incidentId: string): Promise<any> {
  return request<any>(`/api/incidents/${incidentId}/resolve`, {
    method: 'POST',
  });
}

// ─── Compliance & Hazards Configuration ─────────────────────────────────────

export async function fetchComplianceConfig(): Promise<any> {
  return request<any>('/api/compliance/config');
}

export async function fetchHazardConfig(): Promise<any> {
  return request<any>('/api/hazards/config');
}

export async function fetchHazards(): Promise<HazardEventDetail[]> {
  return request<HazardEventDetail[]>('/api/hazards');
}

export async function fetchHazardDetail(eventId: string): Promise<any> {
  return request<any>(`/api/hazards/${eventId}`);
}

// ─── Production Multi-Camera Manager ────────────────────────────────────────

export async function fetchCameras(): Promise<any[]> {
  const res = await request<any>('/api/cameras');
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.cameras)) return res.cameras;
  return [];
}

export async function startCamera(cameraId: string): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}/start`, { method: 'POST' });
}

export async function stopCamera(cameraId: string): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}/stop`, { method: 'POST' });
}

export async function reconnectCamera(cameraId: string): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}/reconnect`, { method: 'POST' });
}

export async function createCamera(cameraData: any): Promise<any> {
  return request<any>('/api/cameras', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cameraData),
  });
}

export async function deleteCamera(cameraId: string): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}`, { method: 'DELETE' });
}

export async function testCameraSource(source: string, sourceType: string = 'usb'): Promise<any> {
  return request<any>('/api/cameras/test-source', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, source_type: sourceType }),
  });
}

export async function analyzeCameraLive(cameraId: string): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}/analyze`, { method: 'POST' });
}

export async function analyzeCameraUpload(cameraId: string, file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  const url = `${API_BASE_URL}/api/cameras/${cameraId}/analyze`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Analysis failed with status ${response.status}`);
  }
  return response.json();
}

// ─── Evidence Archival ──────────────────────────────────────────────────────

export async function fetchIncidentEvidence(incidentId: string): Promise<EvidenceItem[]> {
  return request<EvidenceItem[]>(`/api/incidents/${incidentId}/evidence`);
}

export async function fetchEvidenceDetail(evidenceId: string): Promise<EvidenceItem> {
  return request<EvidenceItem>(`/api/evidence/${evidenceId}`);
}

// ─── Camera Speaker & Audio Alerts ──────────────────────────────────────────

export async function toggleCameraSpeaker(cameraId: string, enabled: boolean): Promise<any> {
  return request<any>(`/api/cameras/${cameraId}/speaker`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
}

export async function fetchAudioAlerts(cameraId?: string, limit: number = 50): Promise<any[]> {
  const qs = cameraId ? `?camera_id=${cameraId}&limit=${limit}` : `?limit=${limit}`;
  return request<any[]>(`/api/audio/alerts${qs}`);
}

