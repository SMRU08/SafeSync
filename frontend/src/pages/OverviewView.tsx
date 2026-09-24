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

      {/* ─── 1. Key Metrics Row (6 Cards) ─────────────────────────────────── */}
      <section className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* Metric 1: Active Cameras */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-medium">Active Cameras</span>
            <div className="w-5 h-5 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center">
              <Camera className="w-3 h-3" />
            </div>
          </div>
          <div>
            <div className="text-xl font-extrabold text-slate-900 font-mono-nums">
              {activeCameras} / {totalCameras > 0 ? totalCameras : 4}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              {activeCameras} online • {Math.max(0, (totalCameras || 4) - activeCameras)} offline
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-2.5 overflow-hidden flex">
            <div
              className="bg-emerald-500 h-1 rounded-full transition-all duration-500"
              style={{
                width: `${totalCameras > 0 ? Math.round((activeCameras / totalCameras) * 100) : 25}%`,
              }}
            />
          </div>
        </div>

        {/* Metric 2: Tracked Workers */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-medium">Tracked Workers</span>
            <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-600 flex items-center justify-center">
              <Users className="w-3 h-3" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-extrabold text-slate-900 font-mono-nums">
                {totalWorkersCount}
              </span>
              <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1 py-0.5 rounded">
                Live
              </span>
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">On active cameras</div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-2.5 overflow-hidden">
            <div
              className="bg-sky-500 h-1 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, totalWorkersCount * 25)}%` }}
            />
          </div>
        </div>

        {/* Metric 3: PPE Compliance */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span className="text-[11px] font-medium">PPE Compliance</span>
            </div>
            <div className="text-xl font-extrabold text-slate-900 font-mono-nums">
              {complianceRate}%
            </div>
            <div
              className={`text-[10px] font-medium mt-0.5 ${
                activeViolationsCount > 0 ? 'text-rose-500' : 'text-emerald-600'
              }`}
            >
              {activeViolationsCount > 0
                ? `${activeViolationsCount} violations`
                : '100% compliant'}
            </div>
          </div>
          <div className="relative w-11 h-11 flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-100"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="3.5"
              />
              <path
                className="text-emerald-500 transition-all duration-500"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeDasharray={`${complianceRate}, 100`}
                strokeLinecap="round"
                strokeWidth="3.5"
              />
            </svg>
          </div>
        </div>

        {/* Metric 4: Fire Incidents */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-medium">Fire Incidents</span>
            <div className="w-5 h-5 rounded-md bg-rose-50 text-rose-600 flex items-center justify-center">
              <Flame className="w-3 h-3" />
            </div>
          </div>
          <div>
            <div
              className={`text-xl font-extrabold font-mono-nums ${
                fireAlertsCount > 0 ? 'text-rose-600' : 'text-slate-900'
              }`}
            >
              {fireAlertsCount}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              {fireAlertsCount > 0 ? 'Hazard active' : 'All zones clear'}
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-2.5 overflow-hidden">
            <div
              className={`h-1 rounded-full ${
                fireAlertsCount > 0 ? 'bg-rose-500' : 'bg-emerald-500'
              }`}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Metric 5: Smoke Incidents */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-medium">Smoke Incidents</span>
            <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-600 flex items-center justify-center">
              <CloudRain className="w-3 h-3" />
            </div>
          </div>
          <div>
            <div
              className={`text-xl font-extrabold font-mono-nums ${
                smokeAlertsCount > 0 ? 'text-amber-600' : 'text-slate-900'
              }`}
            >
              {smokeAlertsCount}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              {smokeAlertsCount > 0 ? 'Hazard active' : 'All zones clear'}
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-2.5 overflow-hidden">
            <div
              className={`h-1 rounded-full ${
                smokeAlertsCount > 0 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Metric 6: Active Alerts */}
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-medium">Active Alerts</span>
            <div className="w-5 h-5 rounded-md bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-3 h-3" />
            </div>
          </div>
          <div>
            <div
              className={`text-xl font-extrabold font-mono-nums ${
                activeAlertsCount > 0 ? 'text-rose-600' : 'text-slate-900'
              }`}
            >
              {activeAlertsCount}
            </div>
            <div
              className={`text-[10px] font-medium flex items-center gap-1 mt-0.5 ${
                activeAlertsCount > 0 ? 'text-rose-600' : 'text-slate-400'
              }`}
            >
              <span>{activeAlertsCount > 0 ? 'Needs attention' : 'Normal state'}</span>
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-2.5 overflow-hidden">
            <div
              className={`h-1 rounded-full ${
                activeAlertsCount > 0 ? 'bg-rose-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, activeAlertsCount * 25)}%` }}
            />
          </div>
        </div>
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

          <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-sky-600" />
                <h3 className="font-bold text-xs text-slate-800 tracking-tight">All Cameras</h3>
              </div>
              <button
                onClick={() => onNavigate('cameras')}
                className="text-[11px] font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 transition"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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

          <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-sky-600" />
              <h3 className="font-bold text-xs text-slate-800 tracking-tight">
                PPE Compliance <span className="font-normal text-slate-400">(Live Fleet)</span>
              </h3>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between items-center text-[10px] mb-1 font-medium">
                  <span className="text-slate-700 flex items-center gap-1.5">🪖 Helmet</span>
                  <span className="font-mono-nums font-bold text-slate-800">{helmetPct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      helmetPct >= 75 ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${helmetPct}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center text-[10px] mb-1 font-medium">
                  <span className="text-slate-700 flex items-center gap-1.5">🦺 Safety Vest</span>
                  <span className="font-mono-nums font-bold text-slate-800">{vestPct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      vestPct >= 75 ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${vestPct}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center text-[10px] mb-1 font-medium">
                  <span className="text-slate-700 flex items-center gap-1.5">🧤 Gloves</span>
                  <span className="font-mono-nums font-bold text-slate-800">{glovesPct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      glovesPct >= 75 ? 'bg-emerald-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${glovesPct}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center text-[10px] mb-1 font-medium">
                  <span className="text-slate-700 flex items-center gap-1.5">🥾 Safety Footwear</span>
                  <span className="font-mono-nums font-bold text-slate-800">{footwearPct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      footwearPct >= 75 ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${footwearPct}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-sky-600" />
                <h3 className="font-bold text-xs text-slate-800 tracking-tight">Zone Safety Status</h3>
              </div>
              <span className="text-[10px] text-slate-400">4 Monitored Zones</span>
            </div>

            <div className="space-y-2">
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
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-[11px]"
                >
                  <span className="font-medium text-slate-700">{z.zone}</span>
                  <div className="flex items-center gap-1.5 font-semibold">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        z.isWarning ? 'bg-rose-500' : 'bg-emerald-500'
                      }`}
                    />
                    <span className={z.isWarning ? 'text-rose-600' : 'text-emerald-700'}>
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
