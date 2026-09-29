/**
 * OverviewView.tsx — SafeSync Professional SOC
 * Executive Command Center Dashboard (Phase 6).
 * Features 7 real-time KPI metrics, live stream with ByteTrack PPE HUD,
 * active critical incidents timeline, itemized PPE compliance density, and zone health matrix.
 */

import React, { useState, useEffect } from 'react';
import {
  Camera,
  Users,
  ShieldCheck,
  Flame,
  CloudRain,
  AlertTriangle,
  ArrowRight,
  MapPin,
  Activity,
  Radio,
} from 'lucide-react';
import {
  RiskSummary,
  Alert,
  HazardEventDetail,
  CameraConfig,
  WorkerTrack,
  ComplianceSummary,
} from '../types';
import { CameraFeedPlayer } from '../components/CameraFeedPlayer';
import { CameraCard } from '../components/CameraCard';
import { AlertsTimeline } from '../components/AlertsTimeline';
import { API_BASE_URL } from '../utils/constants';

interface OverviewViewProps {
  summary: RiskSummary | null;
  alerts: Alert[];
  hazards: HazardEventDetail[];
  cameras: CameraConfig[];
  onNavigate: (tab: any) => void;
  onSelectAlert: (alert: Alert) => void;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onRefresh?: () => void | Promise<void>;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
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
  onRefresh,
  onToggleSpeaker,
}) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    cameras[0]?.camera_id || 'camera_01'
  );
  const [liveWorkers, setLiveWorkers] = useState<WorkerTrack[]>([]);
  const [liveHazards, setLiveHazards] = useState<HazardEventDetail[]>([]);
  const [complianceSummary, setComplianceSummary] = useState<ComplianceSummary | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchLiveCompliance = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/compliance/live`);
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data) {
            if (Array.isArray(data.workers)) {
              setLiveWorkers(data.workers);
            }
            if (Array.isArray(data.hazards)) {
              setLiveHazards(data.hazards);
            }
            if (data.summary) {
              setComplianceSummary(data.summary);
            }
          }
        }
      } catch {
        // Tolerate network dropouts
      }
    };

    fetchLiveCompliance();
    const interval = setInterval(fetchLiveCompliance, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const totalCameras = cameras.length;
  const activeCameras = cameras.filter(
    (c) => c.enabled && (c.state === 'CONNECTED' || c.state === 'DEGRADED' || c.status === 'ACTIVE')
  ).length;

  const totalWorkersCount =
    complianceSummary?.total_workers ??
    liveWorkers.length ??
    cameras.reduce((sum, c) => sum + (c.metrics?.active_workers ?? 0), 0);

  const hasLiveWorkers = totalWorkersCount > 0;
  const complianceRate = complianceSummary
    ? Math.round(complianceSummary.compliance_rate_percent)
    : (hasLiveWorkers ? 100 : null);

  const activeViolationsCount = complianceSummary
    ? complianceSummary.non_compliant_workers
    : liveWorkers.filter((w) => !w.overall_compliant).length;

  const activeAlerts = alerts.filter((a) => a.status === 'ACTIVE');
  const fireAlertsCount =
    alerts.filter((a) => a.status === 'ACTIVE' && a.event_type.includes('FIRE')).length +
    hazards.filter((h) => h.hazard_type === 'fire' && (h.state === 'ACTIVE' || h.state === 'CONFIRMED')).length;

  const smokeAlertsCount =
    alerts.filter((a) => a.status === 'ACTIVE' && a.event_type.includes('SMOKE')).length +
    hazards.filter((h) => h.hazard_type === 'smoke' && (h.state === 'ACTIVE' || h.state === 'CONFIRMED')).length;

  const activeAlertsCount = summary?.active_alerts ?? activeAlerts.length;
  const openIncidentsCount = summary?.open_incidents ?? activeAlerts.length;

  const itemized = complianceSummary?.itemized_compliance;
  const calcPpeRate = (stat?: { present: number; absent: number; unknown: number }): number | null => {
    if (!hasLiveWorkers || !stat) return null;
    const evalTotal = stat.present + stat.absent;
    if (evalTotal === 0) return null;
    return Math.round((stat.present / evalTotal) * 100);
  };

  const helmetPct = calcPpeRate(itemized?.helmet);
  const vestPct = calcPpeRate(itemized?.vest);
  const glovesPct = calcPpeRate(itemized?.gloves);
  const footwearPct = calcPpeRate(itemized?.footwear);

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#070b14] text-slate-100 select-none">
      {/* Top Header & Operational Tagline */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white tracking-tight">Overview</h2>
            <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono font-medium">
              <Radio className="w-2.5 h-2.5 animate-pulse text-emerald-400" />
              Live Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Real-time command center for workplace safety, PPE tracking, and thermal hazards</p>
        </div>
        <div className="flex items-center gap-2.5 px-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-lg text-slate-300">
          <ShieldCheck className="w-4 h-4 text-sky-400 flex-shrink-0" />
          <span className="text-[11px] font-medium italic text-slate-300">
            "Zero Compromise on Worker Life Safety"
          </span>
        </div>
      </div>

      {/* ─── 1. Key Metrics Row (7 Cards as Required by Phase 6) ──────────── */}
      <section className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-7 gap-3">
        {/* Card 1: Active Cameras */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Active Cameras</span>
            <div className="p-1 rounded bg-sky-500/10 text-sky-400">
              <Camera className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-black text-white font-mono-nums leading-none">
              {activeCameras}
              <span className="text-xs text-slate-400 font-normal ml-1">/{totalCameras || 1}</span>
            </div>
            <div className="text-[10px] text-emerald-400 font-semibold mt-1.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {activeCameras} Online Matrix
            </div>
          </div>
        </div>

        {/* Card 2: Tracked Workers */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Tracked Workers</span>
            <div className="p-1 rounded bg-sky-500/10 text-sky-400">
              <Users className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-black text-sky-400 font-mono-nums leading-none">
              {totalWorkersCount}
            </div>
            <div className="text-[10px] text-slate-400 font-medium mt-1.5">
              Active in camera feeds
            </div>
          </div>
        </div>

        {/* Card 3: PPE Compliance */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">PPE Compliance</span>
            <div className="p-1 rounded bg-emerald-500/10 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-black font-mono-nums leading-none ${complianceRate !== null && complianceRate >= 80 ? 'text-emerald-400' : complianceRate !== null ? 'text-amber-400' : 'text-slate-400'}`}>
              {complianceRate !== null ? `${complianceRate}%` : 'N/A'}
            </div>
            <div className="text-[10px] text-slate-400 font-medium mt-1.5">
              {hasLiveWorkers
                ? (activeViolationsCount > 0 ? `${activeViolationsCount} Non-compliant` : '100% compliant')
                : 'No workers detected'}
            </div>
          </div>
        </div>

        {/* Card 4: Active Incidents */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Active Incidents</span>
            <div className="p-1 rounded bg-rose-500/10 text-rose-400">
              <Activity className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-black font-mono-nums leading-none ${openIncidentsCount > 0 ? 'text-rose-400' : 'text-white'}`}>
              {openIncidentsCount}
            </div>
            <div className="text-[10px] text-slate-400 font-medium mt-1.5">
              {openIncidentsCount > 0 ? 'Operator triage pending' : 'Zero open incidents'}
            </div>
          </div>
        </div>

        {/* Card 5: Fire Events */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Fire Events</span>
            <div className="p-1 rounded bg-rose-500/10 text-rose-400">
              <Flame className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-black font-mono-nums leading-none ${fireAlertsCount > 0 ? 'text-rose-400 animate-pulse' : 'text-white'}`}>
              {activeCameras === 0 && fireAlertsCount === 0 ? '--' : fireAlertsCount}
            </div>
            <div className="text-[10px] font-semibold mt-1.5">
              {activeCameras === 0 && fireAlertsCount === 0 ? (
                <span className="text-slate-500">No live camera data</span>
              ) : fireAlertsCount > 0 ? (
                <span className="text-rose-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
                  Combustion active
                </span>
              ) : (
                <span className="text-emerald-400">✓ All zones clear</span>
              )}
            </div>
          </div>
        </div>

        {/* Card 6: Smoke Events */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Smoke Events</span>
            <div className="p-1 rounded bg-amber-500/10 text-amber-400">
              <CloudRain className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-black font-mono-nums leading-none ${smokeAlertsCount > 0 ? 'text-amber-400 animate-pulse' : 'text-white'}`}>
              {activeCameras === 0 && smokeAlertsCount === 0 ? '--' : smokeAlertsCount}
            </div>
            <div className="text-[10px] font-semibold mt-1.5">
              {activeCameras === 0 && smokeAlertsCount === 0 ? (
                <span className="text-slate-500">No live camera data</span>
              ) : smokeAlertsCount > 0 ? (
                <span className="text-amber-400">Plume confirmed</span>
              ) : (
                <span className="text-emerald-400">✓ Air quality clear</span>
              )}
            </div>
          </div>
        </div>

        {/* Card 7: Active Alerts */}
        <div className="glass-card p-3 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-semibold text-[10px] uppercase tracking-wider">Active Alerts</span>
            <div className="p-1 rounded bg-sky-500/10 text-sky-400">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-black font-mono-nums leading-none ${activeAlertsCount > 0 ? 'text-amber-400' : 'text-white'}`}>
              {activeAlertsCount}
            </div>
            <div className="text-[10px] text-slate-400 font-medium mt-1.5">
              {activeAlertsCount > 0 ? `${activeAlertsCount} Unresolved` : 'Normal state'}
            </div>
          </div>
        </div>
      </section>

      {/* ─── 2. Core Dashboard Split Grid ─────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
        {/* Left / Center Column: Live Camera & Camera Grid (8 Cols) */}
        <div className="xl:col-span-8 space-y-4">
          <CameraFeedPlayer
            cameras={cameras}
            selectedCameraId={selectedCameraId}
            onSelectCamera={setSelectedCameraId}
            workers={liveWorkers}
            hazards={
              liveHazards.length > 0
                ? liveHazards.filter((h) => !h.camera_id || h.camera_id === selectedCameraId)
                : hazards.filter((h) => !h.camera_id || h.camera_id === selectedCameraId)
            }
            onRefresh={onRefresh ? () => onRefresh() : undefined}
          />

          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-3.5 h-3.5 text-sky-400" />
                <h3 className="font-bold text-xs text-white tracking-wide uppercase">All Camera Feeds</h3>
              </div>
              <button
                onClick={() => onNavigate('cameras')}
                className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 transition"
              >
                View Camera Matrix <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="p-3 grid grid-cols-2 md:grid-cols-4 gap-3">
              {cameras.map((camera) => (
                <CameraCard
                  key={camera.camera_id}
                  camera={camera}
                  isSelected={camera.camera_id === selectedCameraId}
                  onSelect={setSelectedCameraId}
                  onToggleSpeaker={onToggleSpeaker}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Incident Feed, PPE Analytics, Zones (4 Cols) */}
        <div className="xl:col-span-4 space-y-4">
          <AlertsTimeline
            alerts={alerts}
            onAcknowledge={onAcknowledge}
            onResolve={onResolve}
            onViewAll={() => onNavigate('alerts')}
            onSelectAlert={onSelectAlert}
          />

          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <h3 className="font-bold text-xs text-white tracking-wide uppercase">
                  PPE Compliance Matrix
                </h3>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Live Telemetry</span>
            </div>

            <div className="p-4 space-y-3">
              {[
                { label: '🪖 Safety Helmet', pct: helmetPct },
                { label: '🦺 High-Vis Vest', pct: vestPct },
                { label: '🧤 Protective Gloves', pct: glovesPct },
                { label: '🥾 Safety Footwear', pct: footwearPct },
              ].map(({ label, pct }) => {
                const isAvailable = pct !== null;
                const barColor = !isAvailable ? 'bg-slate-700' : pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-rose-500';
                const textColor = !isAvailable ? 'text-slate-400' : pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-rose-400';
                return (
                  <div key={label}>
                    <div className="flex justify-between items-center text-[11px] mb-1 font-medium">
                      <span className="text-slate-300 flex items-center gap-1.5">{label}</span>
                      <span className={`font-mono-nums font-bold ${textColor}`}>
                        {isAvailable ? `${pct}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
                        style={{ width: isAvailable ? `${pct}%` : '0%' }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-sky-400" />
                <h3 className="font-bold text-xs text-white tracking-wide uppercase">Safety Zones</h3>
              </div>
              <span className="text-[10px] text-slate-400 font-medium">Facility Zones</span>
            </div>

            <div className="p-3 space-y-2">
              {[
                {
                  zone: 'Production Floor South',
                  status: activeViolationsCount > 0 ? `${activeViolationsCount} Infractions` : 'Normal',
                  isWarning: activeViolationsCount > 0,
                },
                { zone: 'Raw Material Storage', status: 'Normal', isWarning: false },
                { zone: 'High Voltage Room', status: 'Normal', isWarning: false },
                { zone: 'Loading Dock Outer', status: 'Normal', isWarning: false },
              ].map((z, idx) => (
                <div
                  key={idx}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs border ${
                    z.isWarning
                      ? 'bg-rose-500/10 border-rose-500/30'
                      : 'bg-slate-900/40 border-slate-800/60'
                  }`}
                >
                  <span className="font-medium text-slate-300">{z.zone}</span>
                  <div className="flex items-center gap-1.5 font-bold">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        z.isWarning ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'
                      }`}
                    />
                    <span className={z.isWarning ? 'text-rose-400' : 'text-emerald-400'}>
                      {z.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewView;
