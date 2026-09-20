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
      setHealth({
        status: data.status === 'healthy' ? 'healthy' : 'unhealthy',
        database: data.database === 'connected' ? 'connected' : 'disconnected',
        aiEngine: 'Not Connected',
        lastChecked: new Date().toLocaleTimeString(),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to backend';
      setHealth({
        status: 'disconnected',
        database: 'disconnected',
        aiEngine: 'Not Connected',
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
