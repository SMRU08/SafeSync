export * from './safety';

export interface ServiceComponentHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'warning' | 'offline' | 'unknown' | 'online' | 'connected' | 'ready' | string;
  details?: string;
  latency_ms?: number;
  [key: string]: any;
}

export interface SystemHealthSnapshot {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'checking' | 'offline' | 'running' | string;
  cluster_state: 'healthy' | 'degraded' | 'warning' | 'critical' | 'checking' | 'offline' | string;
  cluster_message: string;
  timestamp: string;
  lastCheckedTime?: string;
  isStale?: boolean;
  api: ServiceComponentHealth & {
    version: string;
    environment: string;
    port: number;
    uptime_seconds: number;
  };
  database: ServiceComponentHealth & {
    connected: boolean;
    query_ok: boolean;
    integrity_check: string;
    dialect: string;
    journal_mode: string;
    foreign_keys: boolean;
    tables_count: number;
  };
  ai_engine: ServiceComponentHealth & {
    loaded: boolean;
    device: string;
    model_name: string;
    model_path?: string;
    classes_count: number;
    classes: Record<number, string>;
    components: {
      ppe_model: { status: string; classes: string[] };
      fire_smoke_model: { status: string; classes: string[]; fire_class_id?: number; smoke_class_id?: number };
      tracker: { status: string; algorithm: string };
    };
    inference_probe: {
      executed: boolean;
      success: boolean;
      latency_ms: number;
      device: string;
      fire_class_detected?: boolean;
      smoke_class_detected?: boolean;
      error?: string | null;
    };
    mean_latency_ms: number;
    target_latency_ms: number;
    within_target: boolean;
  };
  websocket: ServiceComponentHealth & {
    server_active: boolean;
    active_connections: number;
    endpoint?: string;
  };
  camera_manager: ServiceComponentHealth & {
    total_cameras: number;
    enabled_cameras: number;
    streaming_cameras: number;
    cameras: Array<{
      camera_id: string;
      name: string;
      state: string;
      status: string;
      enabled: boolean;
      source_type: string;
      fps: number;
      dropped_frames: number;
      reconnect_count: number;
      last_frame_age_ms: number | null;
      is_streaming: boolean;
    }>;
  };
  incident_engine: ServiceComponentHealth & {
    rules_loaded: number;
    cooldown_seconds: number;
    deduplication_active: boolean;
  };
  system_resources?: {
    cpu_percent?: number;
    memory_percent?: number;
    memory_used_mb?: number;
    memory_total_mb?: number;
    python_version?: string;
    process_id?: number;
    [key: string]: any;
  };
  database_connected?: boolean;
  ai_status?: string;
  model_loaded?: boolean;
  [key: string]: any;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'checking' | 'disconnected' | 'offline';
  backend?: 'healthy' | 'offline' | 'checking';
  database: 'connected' | 'disconnected' | 'checking';
  aiEngine: string;
  errorMessage?: string;
  lastChecked?: string;
}

export interface BackendHealthResponse extends Partial<SystemHealthSnapshot> {
  app_name?: string;
  environment?: string;
  device_selected?: string;
}

