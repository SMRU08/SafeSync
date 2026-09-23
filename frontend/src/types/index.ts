export * from './safety';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'checking' | 'disconnected' | 'offline';
  backend?: 'healthy' | 'offline' | 'checking';
  database: 'connected' | 'disconnected' | 'checking';
  aiEngine: string;
  errorMessage?: string;
  lastChecked?: string;
}

export interface BackendHealthResponse {
  status: string;
  api?: {
    status: string;
    app_name?: string;
    environment?: string;
    version?: string;
  };
  database?: string | {
    status: string;
    dialect?: string;
    reachable?: boolean;
  };
  database_connected?: boolean;
  ai_engine?: string | {
    status: string;
    loaded?: boolean;
    device?: string;
    model?: string;
    classes?: number;
  };
  ai_status?: string;
  model_loaded?: boolean;
  websocket?: {
    status: string;
    active_connections?: number;
    error?: string;
  };
  app_name?: string;
  environment?: string;
  device_selected?: string;
}
