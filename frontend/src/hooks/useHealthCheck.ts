import { useState, useEffect, useCallback } from 'react';
import { fetchHealth } from '../services/api';
import { HealthStatus } from '../types';
import { HEALTH_CHECK_INTERVAL_MS } from '../utils/constants';

export function useHealthCheck() {
  const [health, setHealth] = useState<HealthStatus>({
    status: 'checking',
    database: 'checking',
    aiEngine: 'Not Connected',
  });

  const check = useCallback(async () => {
    try {
      const data = await fetchHealth();
      const isDbConnected =
        typeof data.database === 'object' && data.database !== null
          ? (data.database.connected === true || data.database.status === 'healthy')
          : data.database === 'connected' || data.database_connected === true;

      const aiStatus =
        typeof data.ai_engine === 'object' && data.ai_engine !== null
          ? data.ai_engine.status
          : data.ai_status || data.ai_engine;
      const isAiAvailable =
        ['healthy', 'available', 'connected', 'ready', 'loaded'].includes(String(aiStatus || '').toLowerCase()) ||
        data.model_loaded === true;
      const aiLabel = isAiAvailable ? 'Ready' : 'Unavailable';

      const isApiHealthy =
        typeof data.api === 'object' && data.api !== null
          ? (data.api.status === 'healthy' || data.api.status === 'online')
          : data.status === 'healthy' || data.status === 'degraded';

      setHealth({
        status: isApiHealthy && isDbConnected ? 'healthy' : 'unhealthy',
        backend: isApiHealthy ? 'healthy' : 'offline',
        database: isDbConnected ? 'connected' : 'disconnected',
        aiEngine: aiLabel,
        lastChecked: new Date().toLocaleTimeString(),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to backend';
      setHealth({
        status: 'disconnected',
        backend: 'offline',
        database: 'disconnected',
        aiEngine: 'Unavailable',
        errorMessage: msg,
        lastChecked: new Date().toLocaleTimeString(),
      });
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, HEALTH_CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [check]);

  return { health, refresh: check };
}
