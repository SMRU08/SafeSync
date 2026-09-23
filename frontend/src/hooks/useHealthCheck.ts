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
      const dbStatusRaw = typeof data.database === 'object' && data.database !== null
        ? (data.database as any).status
        : data.database;
      const isDbConnected = dbStatusRaw === 'connected' || data.database_connected === true;

      const aiStatusRaw = typeof data.ai_engine === 'object' && data.ai_engine !== null
        ? (data.ai_engine as any).status
        : (data.ai_engine || data.ai_status);
      const isAiAvailable = ['available', 'connected', 'ready', 'loaded'].includes(String(aiStatusRaw || '').toLowerCase()) || data.model_loaded === true;
      const aiLabel = isAiAvailable ? (String(aiStatusRaw || '').toLowerCase() === 'available' ? 'Available' : 'Connected') : 'Unavailable';

      setHealth({
        status: data.status === 'healthy' ? 'healthy' : 'unhealthy',
        database: isDbConnected ? 'connected' : 'disconnected',
        aiEngine: aiLabel,
        lastChecked: new Date().toLocaleTimeString(),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to backend';
      setHealth({
        status: 'disconnected',
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
