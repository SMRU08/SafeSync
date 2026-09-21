export * from './safety';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'checking' | 'disconnected';
  database: 'connected' | 'disconnected' | 'checking';
  aiEngine: string;
  errorMessage?: string;
  lastChecked?: string;
}

export interface BackendHealthResponse {
  status: string;
  database?: string;
  ai_engine?: string;
  app_name?: string;
  environment?: string;
  database_connected?: boolean;
  device_selected?: string;
  model_loaded?: boolean;
}
