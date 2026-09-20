import React from 'react';
import { useHealthCheck } from '../hooks/useHealthCheck';
import { StatusCard } from '../components/StatusCard';

export const Dashboard: React.FC = () => {
  const { health, refresh } = useHealthCheck();

  const getBackendStatus = () => {
    if (health.status === 'checking') return { label: 'Checking...', variant: 'pending' as const };
    if (health.status === 'healthy') return { label: 'Connected', variant: 'success' as const };
    return { label: 'Disconnected', variant: 'error' as const };
  };

  const getDatabaseStatus = () => {
    if (health.database === 'checking') return { label: 'Checking...', variant: 'pending' as const };
    if (health.database === 'connected') return { label: 'Connected', variant: 'success' as const };
    return { label: 'Disconnected', variant: 'error' as const };
  };

  const backendInfo = getBackendStatus();
  const dbInfo = getDatabaseStatus();

  return (
    <main className="dashboard-container">
      <header className="dashboard-header">
        <div className="logo-badge">PHASE 1 FOUNDATION</div>
        <h1 className="main-title">RAKSHYA VISION</h1>
        <p className="subtitle">AI Vision-Based Safety Monitoring</p>
      </header>

      <section className="status-section">
        <div className="section-title-bar">
          <h2>System Status</h2>
          <button className="refresh-btn" onClick={refresh}>
            Refresh Status
          </button>
        </div>

        <div className="status-grid">
          <StatusCard
            title="Backend"
            status={backendInfo.label}
            variant={backendInfo.variant}
            detail={health.status === 'healthy' ? 'FastAPI /health responsive' : health.errorMessage || 'Attempting connection...'}
          />
          <StatusCard
            title="AI Engine"
            status={health.aiEngine}
            variant="neutral"
            detail="Phase 1 Foundation — Model training not started"
          />
          <StatusCard
            title="Database"
            status={dbInfo.label}
            variant={dbInfo.variant}
            detail={health.database === 'connected' ? 'SQLite rakshya_vision.db ready' : 'Database unreachable'}
          />
        </div>

        {health.lastChecked && (
          <p className="last-checked">Last synced: {health.lastChecked}</p>
        )}
      </section>

      <section className="scope-section">
        <h3>Phase 1 Scope & Architecture</h3>
        <ul>
          <li><strong>Architecture:</strong> FastAPI + React (TypeScript) + SQLite + OpenCV</li>
          <li><strong>Detection Target:</strong> Person, Helmet, Safety Vest, Gloves, Safety Footwear, Fire, Smoke</li>
          <li><strong>Rule:</strong> No mock AI detections, no premature training datasets</li>
        </ul>
      </section>
    </main>
  );
};
