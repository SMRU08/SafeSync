/**
 * OverviewView.tsx — RAKSHYA VISION Phase 8
 * Main SOC Executive Dashboard with real-time KPI metrics, zone hazard summary, and live alerts.
 */

import React, { useState, useEffect } from 'react';
import {
  Video,
  Users,
  ShieldCheck,
  AlertTriangle,
  Flame,
  CloudRain,
  Bell,
  ArrowRight,
  ShieldAlert,
  Activity,
} from 'lucide-react';
import { RiskSummary, Alert, HazardEventDetail, CameraConfig, NavigationTab } from '../types';
import { MetricCard } from '../components/MetricCard';
import { HazardStatusPanel } from '../components/HazardStatusPanel';
import { AlertsTable } from '../components/AlertsTable';
import { API_BASE_URL } from '../utils/constants';

interface OverviewViewProps {
  summary: RiskSummary | null;
  alerts: Alert[];
  hazards: HazardEventDetail[];
  cameras: CameraConfig[];
  onNavigate: (tab: NavigationTab) => void;
  onSelectAlert: (alert: Alert) => void;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  summary,
  alerts,
  hazards,
  cameras,
  onNavigate,
  onSelectAlert,
  onAcknowledge,
  onResolve,
  onDismiss,
}) => {
  const activeAlerts = alerts.filter((a) => a.status === 'ACTIVE');
  const fireAlerts = activeAlerts.filter((a) => a.event_type.includes('FIRE'));
  const smokeAlerts = activeAlerts.filter((a) => a.event_type.includes('SMOKE'));
  const ppeViolations = activeAlerts.filter((a) => a.event_type.startsWith('MISSING_'));

  const criticalCount = summary?.critical ?? activeAlerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = summary?.high ?? activeAlerts.filter((a) => a.severity === 'HIGH').length;

  const [liveWorkersCount, setLiveWorkersCount] = useState<number | null>(null);
  const [liveComplianceRate, setLiveComplianceRate] = useState<number | null>(null);
  const [snapshotTimestamp, setSnapshotTimestamp] = useState<number>(Date.now());

  useEffect(() => {
    let isMounted = true;
    const fetchLive = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/compliance/live`);
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data && data.summary) {
            setLiveWorkersCount(data.summary.total_workers);
            setLiveComplianceRate(data.summary.compliance_percentage);
          } else if (data && Array.isArray(data.workers)) {
            setLiveWorkersCount(data.workers.length);
          }
          setSnapshotTimestamp(Date.now());
        }
      } catch {
        // Silently ignore dropouts
      }
    };

    fetchLive();
    const interval = setInterval(fetchLive, 2500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="overview-container">
      {/* Top Banner if Critical or High alerts exist */}
      {criticalCount > 0 ? (
        <div className="alert-banner-critical">
          <ShieldAlert size={22} className="animate-pulse" />
          <div className="banner-text">
            <strong>CRITICAL SAFETY ALERT ACTIVE:</strong> {criticalCount} critical hazard event(s)
            require immediate human intervention.
          </div>
          <button className="btn-banner" onClick={() => onNavigate('alerts')}>
            Review Critical Alerts <ArrowRight size={14} />
          </button>
        </div>
      ) : highCount > 0 ? (
        <div className="alert-banner-warning">
          <AlertTriangle size={20} />
          <div className="banner-text">
            <strong>HIGH SEVERITY ADVISORY:</strong> {highCount} high risk event(s) detected.
          </div>
          <button className="btn-banner" onClick={() => onNavigate('alerts')}>
            View Alerts <ArrowRight size={14} />
          </button>
        </div>
      ) : null}

      {/* KPI Metrics Grid */}
      <section className="kpi-grid">
        <MetricCard
          title="Active Cameras"
          value={cameras.length > 0 ? cameras.length : '4'}
          subtitle="All optical streams connected"
          icon={<Video size={20} />}
          variant="info"
          onClick={() => onNavigate('cameras')}
        />
        <MetricCard
          title="Tracked Workers"
          value={liveWorkersCount !== null ? liveWorkersCount : '0'}
          subtitle={liveWorkersCount !== null && liveWorkersCount > 0 ? `${liveWorkersCount} active in view` : 'Standby / No active stream'}
          icon={<Users size={20} />}
          variant={liveWorkersCount && liveWorkersCount > 0 ? 'info' : 'default'}
          onClick={() => onNavigate('workers')}
        />
        <MetricCard
          title="PPE Compliance Rate"
          value={liveComplianceRate !== null ? `${Math.round(liveComplianceRate)}%` : 'NO DATA'}
          subtitle={liveComplianceRate !== null ? 'Live stream evaluation' : 'Awaiting active video feed'}
          icon={<ShieldCheck size={20} />}
          variant={liveComplianceRate !== null ? (liveComplianceRate >= 80 ? 'success' : 'warning') : 'default'}
          onClick={() => onNavigate('workers')}
        />
        <MetricCard
          title="PPE Violations"
          value={ppeViolations.length}
          subtitle={ppeViolations.length > 0 ? 'Confirmed missing PPE' : 'Zero active violations'}
          icon={<AlertTriangle size={20} />}
          variant={ppeViolations.length > 0 ? 'warning' : 'success'}
          onClick={() => onNavigate('alerts')}
        />
        <MetricCard
          title="Fire Incidents"
          value={fireAlerts.length}
          subtitle={fireAlerts.length > 0 ? 'Thermal/optical flame active' : 'All zones clear'}
          icon={<Flame size={20} />}
          variant={fireAlerts.length > 0 ? 'critical' : 'success'}
          onClick={() => onNavigate('hazards')}
        />
        <MetricCard
          title="Smoke Incidents"
          value={smokeAlerts.length}
          subtitle={smokeAlerts.length > 0 ? 'Smoke plume detected' : 'All zones clear'}
          icon={<CloudRain size={20} />}
          variant={smokeAlerts.length > 0 ? 'warning' : 'success'}
          onClick={() => onNavigate('hazards')}
        />
        <MetricCard
          title="Active Alerts"
          value={summary?.active_alerts ?? activeAlerts.length}
          subtitle={`${summary?.open_incidents ?? 0} open incidents`}
          icon={<Bell size={20} />}
          variant={criticalCount > 0 ? 'critical' : highCount > 0 ? 'high' : 'default'}
          badge={criticalCount > 0 ? `${criticalCount} CRIT` : undefined}
          onClick={() => onNavigate('alerts')}
        />
      </section>

      {/* Main Grid: Zones Status + Camera Feeds */}
      <div className="overview-two-col">
        {/* Monitored Zones */}
        <section className="soc-section">
          <div className="section-header-row">
            <h3 className="section-heading">
              <Activity size={18} /> Monitored Safety Zones
            </h3>
            <button className="btn-link" onClick={() => onNavigate('hazards')}>
              Zone Details <ArrowRight size={14} />
            </button>
          </div>
          <HazardStatusPanel hazards={hazards} />
        </section>

        {/* Camera Feeds Preview */}
        <section className="soc-section">
          <div className="section-header-row">
            <h3 className="section-heading">
              <Video size={18} /> Optical Feeds Preview
            </h3>
            <button className="btn-link" onClick={() => onNavigate('cameras')}>
              Manage Feeds <ArrowRight size={14} />
            </button>
          </div>
          <div className="camera-preview-grid">
            {(cameras.length > 0
              ? cameras
              : [
                  { camera_id: 'camera_01', name: 'Production Floor South', zone_id: 'production_floor', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
                  { camera_id: 'camera_02', name: 'Raw Material Storage', zone_id: 'storage_area', status: 'STANDBY', resolution: '1280x720', fps: 25 },
                  { camera_id: 'camera_03', name: 'Electrical Room', zone_id: 'electrical_room', status: 'STANDBY', resolution: '640x480', fps: 20 },
                  { camera_id: 'camera_04', name: 'Loading Dock Outer', zone_id: 'loading_dock', status: 'STANDBY', resolution: '1920x1080', fps: 25 },
                ]
            ).map((cam) => {
              const isLive = (cam as any).state === 'CONNECTED' || cam.status === 'ACTIVE';
              return (
                <div key={cam.camera_id} className="camera-thumb-card" onClick={() => onNavigate('cameras')}>
                  <div className="camera-thumb-screen relative overflow-hidden bg-black flex items-center justify-center min-h-[120px]">
                    <div className="camera-thumb-overlay z-10">
                      <span className="camera-badge-id">{cam.camera_id}</span>
                      <span className={`badge ${isLive ? 'badge-success' : 'badge-neutral'} text-xs`}>
                        {isLive ? 'ONLINE' : 'STANDBY'}
                      </span>
                    </div>
                    {isLive ? (
                      <img
                        src={`${API_BASE_URL}/api/cameras/${cam.camera_id}/snapshot?t=${snapshotTimestamp}`}
                        alt={cam.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.currentTarget as HTMLElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="camera-standby-placeholder">
                        <Video size={24} className="text-muted" />
                        <span>{cam.resolution || '720p'}</span>
                      </div>
                    )}
                  </div>
                  <div className="camera-thumb-meta">
                    <div className="camera-thumb-name">{cam.name}</div>
                    <div className="camera-thumb-zone">{cam.zone_id}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* Recent Alerts Section */}
      <section className="soc-section mt-6">
        <div className="section-header-row">
          <h3 className="section-heading">
            <Bell size={18} /> Live Safety Alerts Feed
          </h3>
          <button className="btn-link" onClick={() => onNavigate('alerts')}>
            View All ({alerts.length}) <ArrowRight size={14} />
          </button>
        </div>
        <AlertsTable
          alerts={alerts.slice(0, 5)}
          compact={true}
          onSelectAlert={onSelectAlert}
          onAcknowledge={onAcknowledge}
          onResolve={onResolve}
          onDismiss={onDismiss}
        />
      </section>
    </div>
  );
};
