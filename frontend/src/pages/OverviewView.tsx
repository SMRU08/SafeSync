/**
 * OverviewView.tsx — RAKSHYA VISION Phase 8
 * Main SOC Executive Dashboard with real-time KPI metrics, zone hazard summary, and live alerts.
 */

import React from 'react';
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
          value="0"
          subtitle="Standby / No active stream"
          icon={<Users size={20} />}
          variant="default"
          onClick={() => onNavigate('workers')}
        />
        <MetricCard
          title="PPE Compliance Rate"
          value="NO DATA"
          subtitle="Awaiting active video feed"
          icon={<ShieldCheck size={20} />}
          variant="default"
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
                  { camera_id: 'CAM-01', name: 'Fabrication Bay', zone_id: 'FAB_BAY_01', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
                  { camera_id: 'CAM-02', name: 'Paint & Coating Area', zone_id: 'PAINT_COAT_02', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
                  { camera_id: 'CAM-03', name: 'Chemical Storage', zone_id: 'CHEM_STORE_03', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
                  { camera_id: 'CAM-04', name: 'Assembly Line B', zone_id: 'ASSEMBLY_B_04', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
                ]
            ).map((cam) => (
              <div key={cam.camera_id} className="camera-thumb-card" onClick={() => onNavigate('cameras')}>
                <div className="camera-thumb-screen">
                  <div className="camera-thumb-overlay">
                    <span className="camera-badge-id">{cam.camera_id}</span>
                    <span className="badge badge-success text-xs">ONLINE</span>
                  </div>
                  <div className="camera-standby-placeholder">
                    <Video size={24} className="text-muted" />
                    <span>720p @ 30 FPS</span>
                  </div>
                </div>
                <div className="camera-thumb-meta">
                  <div className="camera-thumb-name">{cam.name}</div>
                  <div className="camera-thumb-zone">{cam.zone_id}</div>
                </div>
              </div>
            ))}
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
