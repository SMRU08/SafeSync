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
}
