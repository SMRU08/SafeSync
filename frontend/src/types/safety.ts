/**
 * safety.ts — SafeSync Phase 8
 * Centralized TypeScript type definitions for Safety Monitoring Dashboard.
 * Accurately mirrors backend Pydantic schemas without fabricated structures.
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
export type IncidentStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
export type PPEPresence = 'PRESENT' | 'ABSENT' | 'UNKNOWN';
export type HazardState = 'NO_HAZARD' | 'CANDIDATE' | 'DETECTING' | 'CONFIRMED' | 'ACTIVE' | 'CLEARING' | 'CLEARED' | 'SUSPECTED';
export type HazardRelationship = 'NO_HAZARD' | 'ISOLATED_FIRE' | 'ISOLATED_SMOKE' | 'FIRE_WITH_SMOKE_PLUME' | 'SMOKE_PRECEDING_FIRE' | 'FIRE_ONLY' | 'SMOKE_ONLY' | 'FIRE_AND_SMOKE';

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
  priority?: 'P0' | 'P1' | 'P2' | 'P3' | string;
  is_audible?: boolean;
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
  normalized_bbox?: [number, number, number, number];
  ppe_status: {
    helmet: PPEPresence;
    safety_vest: PPEPresence;
    gloves: PPEPresence;
    safety_footwear: PPEPresence;
  };
  overall_compliant: boolean;
  active_frames: number;
  dwell_seconds?: number;
  confidence?: number;
  first_seen?: string;
  zone_id?: string;
  missing_items?: string[];
}

export interface ComplianceSummary {
  total_workers: number;
  compliant_workers: number;
  non_compliant_workers: number;
  unknown_workers: number;
  compliance_rate_percent: number;
  itemized_compliance?: any;
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
  active_frames?: number;
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
  inference_latency_ms?: number;
  active_workers?: number;
  active_violations?: number;
  active_hazards?: number;
}

export type RealCameraState =
  | 'CONFIGURED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'STREAMING'
  | 'ONLINE'
  | 'RECONNECTING'
  | 'DEGRADED'
  | 'DISCONNECTED'
  | 'OFFLINE'
  | 'DISABLED'
  | 'UNKNOWN'
  | 'ERROR';

export interface CameraConfig {
  camera_id: string;
  name: string;
  location?: string;
  zone_id: string;
  status: 'ACTIVE' | 'STANDBY' | 'OFFLINE' | 'DEGRADED' | 'online' | 'offline' | 'connecting' | 'error' | 'streaming' | 'degraded';
  connection_status?: string;
  state?: RealCameraState;
  is_streaming?: boolean;
  last_frame_age_ms?: number | null;
  frame_id?: number;
  last_frame_timestamp?: number | null;
  source?: string;
  source_type?: string;
  enabled?: boolean;
  speaker_enabled?: boolean;
  resolution: string;
  fps: number;
  stream_url?: string;
  rtsp_url?: string;
  safe_source?: string;
  last_seen?: string | null;
  last_attempt?: string | null;
  last_error?: string | null;
  retry_count?: number;
  metrics?: CameraMetrics;
  ai_analysis?: {
    active_workers?: number;
    active_violations?: number;
    active_hazards?: number;
    latency_ms?: number;
    summary?: any;
  };
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
  event?:
    | 'AlertCreated'
    | 'AlertUpdated'
    | 'AlertEscalated'
    | 'IncidentCreated'
    | 'IncidentUpdated'
    | 'IncidentResolved'
    | 'AudioAlert'
    | 'AnalyticsUpdated'
    | string;
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
