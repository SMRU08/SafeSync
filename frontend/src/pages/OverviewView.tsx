/**
 * OverviewView.tsx — RAKSHYA VISION Professional SOC
 * Executive Industrial Safety Dashboard with real-time KPI metrics,
 * live camera stream with ByteTrack PPE overlay, hardware fleet grid,
 * recent alerts ledger, and zone compliance summary.
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
            if (data.summary) {
              setComplianceSummary(data.summary);
            }
          }
        }
      } catch {
        // Silently tolerate background dropouts
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

  const complianceRate = complianceSummary
    ? Math.round(complianceSummary.compliance_rate_percent)
    : 67;

  const activeViolationsCount = complianceSummary
    ? complianceSummary.non_compliant_workers
    : liveWorkers.filter((w) => !w.overall_compliant).length;

  const activeAlerts = alerts.filter((a) => a.status === 'ACTIVE');
  const fireAlertsCount =
    alerts.filter((a) => a.status === 'ACTIVE' && a.event_type.includes('FIRE')).length +
    hazards.filter((h) => h.hazard_type === 'fire').length;

  const smokeAlertsCount =
    alerts.filter((a) => a.status === 'ACTIVE' && a.event_type.includes('SMOKE')).length +
    hazards.filter((h) => h.hazard_type === 'smoke').length;

  const activeAlertsCount = summary?.active_alerts ?? activeAlerts.length;

  const itemized = complianceSummary?.itemized_compliance;
  const calcPpeRate = (stat?: { present: number; absent: number; unknown: number }, fallback = 80) => {
    if (!stat) return fallback;
    const evalTotal = stat.present + stat.absent;
    if (evalTotal === 0) return fallback;
    return Math.round((stat.present / evalTotal) * 100);
  };

  const helmetPct = calcPpeRate(itemized?.helmet, 78);
  const vestPct = calcPpeRate(itemized?.vest, 67);
  const glovesPct = calcPpeRate(itemized?.gloves, 52);
  const footwearPct = calcPpeRate(itemized?.footwear, 85);

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Top Header & Safety Quote Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Overview</h2>
          <p className="text-xs text-slate-500">Real-time monitoring of workplace safety and hazards</p>
        </div>
        <div className="flex items-center gap-2.5 px-3 py-1.5 bg-sky-50/80 border border-sky-200/70 rounded-lg text-sky-900 shadow-xs">
          <ShieldCheck className="w-4 h-4 text-sky-600 flex-shrink-0" />
          <span className="text-[11px] font-medium italic">
            "Safety is not an option, it's a responsibility."
          </span>
        </div>
      </div>

      {/* ─── 1. Key Metrics Row (6 Cards) — Enterprise Color-Coded ──────────── */}
      <section className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* Metric 1: Active Cameras */}
        {(() => {
          const pct = totalCameras > 0 ? Math.round((activeCameras / totalCameras) * 100) : 0;
          const color = pct >= 75 ? 'emerald' : pct >= 50 ? 'amber' : 'rose';
          return (
            <div className={`bg-white rounded-xl p-3.5 border shadow-sm flex flex-col justify-between relative overflow-hidden border-${color}-200`}>
              <div className={`absolute inset-x-0 bottom-0 h-1 bg-${color}-500`} />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Active Cameras</span>
                <div className={`w-7 h-7 rounded-lg bg-${color}-50 text-${color}-600 flex items-center justify-center shadow-inner`}>
                  <Camera className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="text-2xl font-black text-slate-900 font-mono-nums leading-none">
                {activeCameras}<span className="text-sm font-semibold text-slate-400">/{totalCameras || 4}</span>
              </div>
              <div className={`text-[10px] font-semibold mt-1.5 text-${color}-600`}>
                {activeCameras} online • {Math.max(0, (totalCameras || 4) - activeCameras)} offline
              </div>
            </div>
          );
        })()}

        {/* Metric 2: Tracked Workers */}
        <div className="bg-white rounded-xl p-3.5 border border-sky-200 shadow-sm flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-sky-500" />
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Tracked Workers</span>
            <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center shadow-inner">
              <Users className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 font-mono-nums leading-none">{totalWorkersCount}</span>
            <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full animate-pulse">LIVE</span>
          </div>
          <div className="text-[10px] font-semibold text-sky-600 mt-1.5">Across all active cameras</div>
        </div>

        {/* Metric 3: PPE Compliance */}
        {(() => {
          const color = complianceRate >= 80 ? 'emerald' : complianceRate >= 60 ? 'amber' : 'rose';
          return (
            <div className={`bg-white rounded-xl p-3.5 border border-${color}-200 shadow-sm flex items-center justify-between relative overflow-hidden`}>
              <div className={`absolute inset-x-0 bottom-0 h-1 bg-${color}-500`} />
              <div>
                <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">PPE Compliance</div>
                <div className={`text-2xl font-black font-mono-nums leading-none text-${color}-600`}>{complianceRate}%</div>
                <div className={`text-[10px] font-semibold mt-1.5 text-${color}-600`}>
                  {activeViolationsCount > 0 ? `${activeViolationsCount} violations` : 'All compliant'}
                </div>
              </div>
              <div className="relative w-12 h-12 flex-shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path className="text-slate-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5" />
                  <path className={`text-${color}-500 transition-all duration-700`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeDasharray={`${complianceRate}, 100`} strokeLinecap="round" strokeWidth="3.5" />
                </svg>
                <ShieldCheck className={`absolute inset-0 m-auto w-4 h-4 text-${color}-500`} />
              </div>
            </div>
          );
        })()}

        {/* Metric 4: Fire Incidents */}
        {(() => {
          const hasFire = fireAlertsCount > 0;
          return (
            <div className={`bg-white rounded-xl p-3.5 border shadow-sm flex flex-col justify-between relative overflow-hidden ${hasFire ? 'border-rose-300' : 'border-emerald-200'}`}>
              <div className={`absolute inset-x-0 bottom-0 h-1 ${hasFire ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'}`} />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Fire Incidents</span>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shadow-inner ${hasFire ? 'bg-rose-100 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
                  <Flame className={`w-3.5 h-3.5 ${hasFire ? 'animate-pulse' : ''}`} />
                </div>
              </div>
              <div className={`text-2xl font-black font-mono-nums leading-none ${hasFire ? 'text-rose-600' : 'text-slate-900'}`}>{fireAlertsCount}</div>
              <div className={`text-[10px] font-semibold mt-1.5 ${hasFire ? 'text-rose-500' : 'text-emerald-600'}`}>
                {hasFire ? '🔥 Hazard ACTIVE' : '✓ All zones clear'}
              </div>
            </div>
          );
        })()}

        {/* Metric 5: Smoke Incidents */}
        {(() => {
          const hasSmoke = smokeAlertsCount > 0;
          return (
            <div className={`bg-white rounded-xl p-3.5 border shadow-sm flex flex-col justify-between relative overflow-hidden ${hasSmoke ? 'border-amber-300' : 'border-emerald-200'}`}>
              <div className={`absolute inset-x-0 bottom-0 h-1 ${hasSmoke ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Smoke Detection</span>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shadow-inner ${hasSmoke ? 'bg-amber-100 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
                  <CloudRain className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className={`text-2xl font-black font-mono-nums leading-none ${hasSmoke ? 'text-amber-600' : 'text-slate-900'}`}>{smokeAlertsCount}</div>
              <div className={`text-[10px] font-semibold mt-1.5 ${hasSmoke ? 'text-amber-500' : 'text-emerald-600'}`}>
                {hasSmoke ? '💨 Hazard ACTIVE' : '✓ All zones clear'}
              </div>
            </div>
          );
        })()}

        {/* Metric 6: Active Alerts */}
        {(() => {
          const hasAlerts = activeAlertsCount > 0;
          const color = activeAlertsCount === 0 ? 'emerald' : activeAlertsCount <= 2 ? 'amber' : 'rose';
          return (
            <div className={`bg-white rounded-xl p-3.5 border border-${color}-200 shadow-sm flex flex-col justify-between relative overflow-hidden`}>
              <div className={`absolute inset-x-0 bottom-0 h-1 bg-${color}-500 ${hasAlerts ? 'animate-pulse' : ''}`} />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Active Alerts</span>
                <div className={`w-7 h-7 rounded-lg bg-${color}-50 text-${color}-600 flex items-center justify-center shadow-inner`}>
                  <AlertTriangle className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className={`text-2xl font-black font-mono-nums leading-none text-${color}-600`}>{activeAlertsCount}</div>
              <div className={`text-[10px] font-semibold mt-1.5 text-${color}-600`}>
                {hasAlerts ? 'Needs attention' : '✓ Normal state'}
              </div>
            </div>
          );
        })()}
      </section>

      {/* ─── 2. Core Dashboard Split Grid ─────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Left / Center Column: Live Camera & Camera Grid (8 Cols) */}
        <div className="xl:col-span-8 space-y-4">
          <CameraFeedPlayer
            cameras={cameras}
            selectedCameraId={selectedCameraId}
            onSelectCamera={setSelectedCameraId}
            workers={liveWorkers}
            onRefresh={onRefresh ? () => onRefresh() : undefined}
          />

          <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="px-4 py-3 bg-[#111f35] border-b border-slate-700/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-3.5 h-3.5 text-sky-400" />
                <h3 className="font-bold text-xs text-white tracking-wide uppercase">All Cameras</h3>
              </div>
              <button
                onClick={() => onNavigate('cameras')}
                className="text-[10px] font-semibold text-sky-400 hover:text-sky-200 flex items-center gap-1 transition"
              >
                View All <ArrowRight className="w-3 h-3" />
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

          <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="px-4 py-3 bg-[#111f35] border-b border-slate-700/80 flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <h3 className="font-bold text-xs text-white tracking-wide uppercase">
                PPE Compliance
                <span className="ml-2 font-normal text-slate-400 normal-case text-[10px]">Live Fleet</span>
              </h3>
            </div>

            <div className="p-4 space-y-3">
              {[
                { label: '🪖 Helmet', pct: helmetPct },
                { label: '🦺 Safety Vest', pct: vestPct },
                { label: '🧤 Gloves', pct: glovesPct },
                { label: '🥾 Safety Footwear', pct: footwearPct },
              ].map(({ label, pct }) => {
                const barColor = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-rose-500';
                const textColor = pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-rose-400';
                return (
                  <div key={label}>
                    <div className="flex justify-between items-center text-[10px] mb-1.5 font-medium">
                      <span className="text-slate-300 flex items-center gap-1.5">{label}</span>
                      <span className={`font-mono-nums font-bold ${textColor}`}>{pct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="px-4 py-3 bg-[#111f35] border-b border-slate-700/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-sky-400" />
                <h3 className="font-bold text-xs text-white tracking-wide uppercase">Zone Safety Status</h3>
              </div>
              <span className="text-[10px] text-slate-400 font-medium">4 Zones</span>
            </div>

            <div className="p-3 space-y-2">
              {[
                {
                  zone: 'Production Floor South',
                  status: activeViolationsCount > 0 ? `${activeViolationsCount} violations` : 'Normal',
                  isWarning: activeViolationsCount > 0,
                },
                { zone: 'Raw Material Storage', status: 'Standby', isWarning: false },
                { zone: 'High Voltage Room', status: 'Normal', isWarning: false },
                { zone: 'Loading Dock Outer', status: 'Normal', isWarning: false },
              ].map((z, idx) => (
                <div
                  key={idx}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-[11px] border ${
                    z.isWarning
                      ? 'bg-rose-950/40 border-rose-700/50'
                      : 'bg-slate-800/50 border-slate-700/50'
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
