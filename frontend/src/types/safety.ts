/**
 * safety.ts — RAKSHYA VISION Phase 8
 * Centralized TypeScript type definitions for Safety Monitoring Dashboard.
 * Accurately mirrors backend Pydantic schemas without fabricated structures.
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
export type IncidentStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
export type PPEPresence = 'PRESENT' | 'ABSENT' | 'UNKNOWN';
export type HazardState = 'NO_HAZARD' | 'SUSPECTED' | 'CONFIRMED' | 'CLEARED';
export type HazardRelationship = 'NO_HAZARD' | 'ISOLATED_FIRE' | 'ISOLATED_SMOKE' | 'FIRE_WITH_SMOKE_PLUME' | 'SMOKE_PRECEDING_FIRE';

export interface RiskSummary {
  active_alerts: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  open_incidents: number;
  timestamp_utc: string;
}

export interface AlertHistoryItem {
  action: string;
  previous_level: string | null;
  new_level: string | null;
  reason: string | null;
  timestamp: string;
}

export interface Alert {
  alert_id: string;
  incident_id: string;
  severity: RiskLevel;
  title: string;
  message: string;
  camera_id: string;
  zone_id: string;
  event_type: string;
  status: AlertStatus;
  timestamp: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  history?: AlertHistoryItem[];
}

export interface Incident {
  incident_id: string;
  status: IncidentStatus;
  event_types: string[];
  camera_id: string;
  zone_id: string;
  affected_tracks?: number[];
  risk_score: number;
  risk_level: RiskLevel;
  factors?: Record<string, any>;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  alerts?: {
    alert_id: string;
    severity: RiskLevel;
    title: string;
    status: AlertStatus;
    created_at: string;
  }[];
}

export interface EvidenceItem {
  evidence_id: string;
  incident_id: string;
  camera_id: string;
  evidence_type: string;
  file_size_bytes: number;
  sha256_checksum: string;
  created_at: string;
  download_url: string;
  computed_sha256?: string;
  verified?: boolean;
  tampered?: boolean;
}

export interface WorkerTrack {
  track_id: number;
  bbox: [number, number, number, number];
  ppe_status: {
    helmet: PPEPresence;
    safety_vest: PPEPresence;
    gloves: PPEPresence;
    safety_footwear: PPEPresence;
  };
  overall_compliant: boolean;
  active_frames: number;
  zone_id?: string;
  missing_items?: string[];
}

export interface ComplianceSummary {
  total_workers: number;
  compliant_workers: number;
  non_compliant_workers: number;
  unknown_workers: number;
  compliance_rate_percent: number;
}

export interface HazardEventDetail {
  hazard_id: string;
  hazard_type: 'fire' | 'smoke';
  state: HazardState;
  confidence: number;
  zone_id: string;
  camera_id: string;
  first_seen_frame?: number;
  last_seen_frame?: number;
  persistence_frames?: number;
  bbox?: [number, number, number, number];
}

export interface CameraMetrics {
  fps: number;
  frame_count: number;
  dropped_frames: number;
  reconnect_count: number;
  last_successful_frame_timestamp?: number | null;
  last_error?: string | null;
  uptime_seconds: number;
}

export type RealCameraState =
  | 'DISABLED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'RECONNECTING'
  | 'DEGRADED'
  | 'DISCONNECTED'
  | 'ERROR';

export interface CameraConfig {
  camera_id: string;
  name: string;
  zone_id: string;
  status: 'ACTIVE' | 'STANDBY' | 'OFFLINE';
  state?: RealCameraState;
  source_type?: string;
  enabled?: boolean;
  resolution: string;
  fps: number;
  rtsp_url?: string;
  safe_source?: string;
  metrics?: CameraMetrics;
}

export interface ZoneConfig {
  zone_id: string;
  name: string;
  risk_multiplier: number;
  description?: string;
}

export interface WebSocketMessage {
  type: 'connected' | 'event' | 'pong';
  message?: string;
  event?: 'AlertCreated' | 'AlertUpdated' | 'AlertEscalated' | 'IncidentCreated' | 'IncidentResolved';
  payload?: any;
  active_connections?: number;
  timestamp: string;
}

export type NavigationTab =
  | 'overview'
  | 'cameras'
  | 'workers'
  | 'hazards'
  | 'alerts'
  | 'analytics'
  | 'settings';
