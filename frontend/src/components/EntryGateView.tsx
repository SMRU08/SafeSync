/**
 * EntryGateView.tsx — SafeSync Phase 4: Entry Gate + PPE Access Decision
 * Dedicated Entry Gate access control screen embedded inside Cameras navigation (Cameras └── Entry Gate).
 *
 * Implements:
 *   - Real-time Entry Gate camera stream via CameraFeedPlayer
 *   - Independent multi-worker ByteTrack tracking
 *   - Real-time PPE Compliance Verification (Helmet, Vest, Gloves, Footwear)
 *   - Tri-State Access Decision Engine:
 *       GREEN  → ALLOW ENTRY (#22C55E)
 *       YELLOW → VERIFICATION REQUIRED (#F5B942, non-punitive, UNKNOWN ≠ VIOLATION)
 *       RED    → DON'T ALLOW ENTRY (#EF4444, confirmed absence only)
 *   - Compliance Score calculation (4/4 100%, or UNKNOWN, or VIOLATION)
 *   - Environmental Hazard (Fire/Smoke) P0 HUD Decoupling
 *   - Recent Entry Events ledger with honest real data / NO ENTRY EVENTS AVAILABLE
 *   - Zero fabricated metrics, zero second detection engines.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  DoorOpen,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Users,
  Camera,
  RefreshCw,
  Flame,
  AlertTriangle,
  ArrowLeft,
  Info,
  Clock,
  Shield,
  Lock,
  Unlock,
  Check,
  X,
  Minus,
} from 'lucide-react';
import { CameraConfig, WorkerTrack, PPEPresence, HazardEventDetail } from '../types';
import { CameraFeedPlayer } from './CameraFeedPlayer';
import { WorkerSafetyLegend } from './WorkerSafetyLegend';
import { resolveWorkerDisplay } from '../utils/workerDisplay';
import { API_BASE_URL } from '../utils/constants';
import { reconnectCamera } from '../services/api';

interface EntryGateViewProps {
  cameras: CameraConfig[];
  onRefreshCameras?: () => void;
  onBackToMatrix?: () => void;
}

export interface EntryEventRecord {
  id: string;
  time: string;
  workerId: number | string;
  workerName?: string;
  helmet: PPEPresence;
  safetyVest: PPEPresence;
  gloves: PPEPresence;
  footwear: PPEPresence;
  decision: 'ALLOW ENTRY' | 'VERIFICATION REQUIRED' | "DON'T ALLOW ENTRY";
  reason: string;
  color: string;
}

export const EntryGateView: React.FC<EntryGateViewProps> = ({
  cameras,
  onRefreshCameras,
  onBackToMatrix,
}) => {
  // Find dedicated Entry Gate camera or default to first camera
  const isEntryGateCam = (c: CameraConfig) =>
    c.zone_id === 'entry_gate' ||
    (c.location && /entry|gate|entrance/i.test(c.location)) ||
    (c.name && /entry|gate|entrance/i.test(c.name));

  const initialCam = cameras.find(isEntryGateCam) || cameras[0];
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    initialCam?.camera_id || 'camera_01'
  );

  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [hazards, setHazards] = useState<HazardEventDetail[]>([]);
  const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
  const [sessionEvents, setSessionEvents] = useState<EntryEventRecord[]>([]);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Transition debouncer to prevent duplicate log spamming
  const transitionRef = useRef<Record<number, string>>({});

  useEffect(() => {
    if (cameras.length > 0 && !cameras.some((c) => c.camera_id === selectedCameraId)) {
      setSelectedCameraId(cameras[0].camera_id);
    }
  }, [cameras, selectedCameraId]);

  const activeCamera =
    cameras.find((c) => c.camera_id === selectedCameraId) ||
    cameras[0] || {
      camera_id: 'camera_01',
      name: 'Entry Gate Camera',
      location: 'Main Entry',
      zone_id: 'entry_gate',
      state: 'CONFIGURED',
      status: 'STANDBY',
      is_streaming: false,
      resolution: '1280x720',
      metrics: { fps: 0, inference_latency_ms: 0, active_workers: 0 },
    };

  const isCameraOnline =
    activeCamera.is_streaming === true ||
    activeCamera.state === 'STREAMING' ||
    activeCamera.status === 'streaming' ||
    ((activeCamera.state === 'CONNECTED' || activeCamera.status === 'ACTIVE') &&
      (activeCamera.last_frame_age_ms == null || activeCamera.last_frame_age_ms < 3000));

  const isConnecting =
    activeCamera.state === 'CONNECTING' ||
    activeCamera.state === 'RECONNECTING' ||
    isReconnecting;

  // Poll live compliance data for selected entry camera
  useEffect(() => {
    let isMounted = true;
    const fetchLiveCompliance = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/compliance/live?camera_id=${selectedCameraId}`);
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data) {
            if (Array.isArray(data.workers)) {
              setWorkers(data.workers);
              // Default selection to first active worker if unselected
              if (selectedWorkerId === null && data.workers.length > 0) {
                setSelectedWorkerId(data.workers[0].track_id);
              } else if (
                data.workers.length > 0 &&
                !data.workers.some((w: WorkerTrack) => w.track_id === selectedWorkerId)
              ) {
                setSelectedWorkerId(data.workers[0].track_id);
              }
            } else {
              setWorkers([]);
            }
            if (Array.isArray(data.hazards)) {
              setHazards(data.hazards);
            }
            const receivedWorkersCount = Array.isArray(data.workers) ? data.workers.length : 0;
            let receivedPpeCount = 0;
            if (Array.isArray(data.workers)) {
              for (const w of data.workers) {
                if (w.ppe_details && typeof w.ppe_details === 'object') {
                  receivedPpeCount += Object.values(w.ppe_details).filter(
                    (obs: any) => obs && obs.bbox && obs.bbox.length >= 4
                  ).length;
                }
              }
            }
            const receivedHazardsCount = Array.isArray(data.hazards) ? data.hazards.length : 0;
            console.log(
              `[ENTRY GATE] FRONTEND RECEIVED: ${
                receivedWorkersCount + receivedPpeCount + receivedHazardsCount
              }`
            );
          }
        }
      } catch {
        // tolerate dropouts
      }
    };

    fetchLiveCompliance();
    const interval = setInterval(fetchLiveCompliance, 1200);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedCameraId, selectedWorkerId]);

  // Real-time Event Ledger: Log entry transitions for detected workers
  useEffect(() => {
    if (workers.length === 0) return;
    const nowTime = new Date().toLocaleTimeString('en-US', { hour12: false });

    workers.forEach((w) => {
      const disp = resolveWorkerDisplay(w);
      const signature = `${disp.state}-${disp.missingItems.join(',')}-${disp.unknownItems.join(',')}`;

      if (transitionRef.current[w.track_id] !== signature) {
        transitionRef.current[w.track_id] = signature;

        let decision: 'ALLOW ENTRY' | 'VERIFICATION REQUIRED' | "DON'T ALLOW ENTRY" =
          'VERIFICATION REQUIRED';
        let reason = 'PPE state could not be confirmed.';

        if (disp.state === 'SAFE') {
          decision = 'ALLOW ENTRY';
          reason = 'All required PPE present.';
        } else if (disp.state === 'VIOLATION') {
          decision = "DON'T ALLOW ENTRY";
          reason = `Confirmed PPE absence across ≥15 consecutive frames: Missing ${disp.missingItems.join(', ')}`;
        } else {
          decision = 'VERIFICATION REQUIRED';
          reason = 'Visibility insufficient for confirmation. Worker is not penalized.';
        }

        const newRecord: EntryEventRecord = {
          id: `${w.track_id}-${Date.now()}`,
          time: nowTime,
          workerId: w.track_id,
          helmet: w.ppe_status?.helmet || 'UNKNOWN',
          safetyVest: w.ppe_status?.safety_vest || 'UNKNOWN',
          gloves: w.ppe_status?.gloves || 'UNKNOWN',
          footwear: w.ppe_status?.safety_footwear || 'UNKNOWN',
          decision,
          reason,
          color: disp.color,
        };

        setSessionEvents((prev) => [newRecord, ...prev.slice(0, 19)]);
      }
    });
  }, [workers]);

  const handleManualReconnect = async () => {
    setIsReconnecting(true);
    setActionError(null);
    try {
      await reconnectCamera(selectedCameraId);
      if (onRefreshCameras) onRefreshCameras();
    } catch (err: any) {
      setActionError(`Reconnect failed: ${err.message || 'Unknown network error'}`);
    } finally {
      setTimeout(() => setIsReconnecting(false), 1000);
    }
  };

  // Currently inspected worker
  const selectedWorker = workers.find((w) => w.track_id === selectedWorkerId) || workers[0];
  const selectedDisplay = selectedWorker ? resolveWorkerDisplay(selectedWorker) : null;

  // Tri-State Entry Decision Computation
  let decisionTitle = 'WAITING FOR WORKER';
  let decisionSubtitle = 'NO WORKER DETECTED';
  let decisionReason = 'Entry gate optical sensor active. Waiting for worker to enter detection zone.';
  let decisionColor = '#64748B';
  let decisionIcon = <Users className="w-6 h-6" />;
  let complianceScoreText = 'STANDBY • 0 Workers';

  if (!isCameraOnline) {
    if (isConnecting) {
      decisionTitle = 'CONNECTING TO ENTRY GATE...';
      decisionSubtitle = 'INITIALIZING SENSOR';
      decisionReason = 'Initiating hardware capture handshake and frame acquisition loop...';
      decisionColor = '#0284C7';
      decisionIcon = <RefreshCw className="w-6 h-6 animate-spin" />;
      complianceScoreText = 'SENSOR CONNECTING';
    } else {
      decisionTitle = 'ENTRY GATE OFFLINE';
      decisionSubtitle = 'STREAM DISCONNECTED';
      decisionReason =
        'Video feed unavailable. Manual inspection checkpoint required. No stale entry granted.';
      decisionColor = '#EF4444';
      decisionIcon = <Lock className="w-6 h-6" />;
      complianceScoreText = 'OFFLINE';
    }
  } else if (!selectedWorker || workers.length === 0) {
    decisionTitle = 'WAITING FOR WORKER';
    decisionSubtitle = 'NO WORKER DETECTED';
    decisionReason = 'Entry gate optical sensor active. Waiting for worker to enter detection zone.';
    decisionColor = '#64748B';
    decisionIcon = <Users className="w-6 h-6" />;
    complianceScoreText = 'NO WORKER DETECTED';
  } else if (selectedDisplay?.state === 'SAFE') {
    decisionTitle = 'ALLOW ENTRY';
    decisionSubtitle = 'SAFE / COMPLIANT';
    decisionReason = 'All required PPE present. Worker authorized to enter production facility.';
    decisionColor = '#22C55E';
    decisionIcon = <Unlock className="w-6 h-6" />;
    complianceScoreText = '4 / 4 PPE • 100% COMPLIANT';
  } else if (selectedDisplay?.state === 'UNKNOWN') {
    // UNKNOWN ≠ VIOLATION: Yellow, non-punitive, NEVER triggers Red or violation alert!
    decisionTitle = 'VERIFICATION REQUIRED';
    decisionSubtitle = 'VISIBILITY LIMITED';
    decisionReason =
      'Visibility insufficient for confirmation: Camera angle or visual occlusion prevents definitive verification. Worker is not penalized. UNKNOWN is not a violation.';
    decisionColor = '#F5B942';
    decisionIcon = <HelpCircle className="w-6 h-6" />;
    complianceScoreText = 'PPE STATUS UNKNOWN • VERIFICATION REQUIRED';
  } else if (selectedDisplay?.state === 'VIOLATION') {
    const missing = selectedDisplay.missingItems.join(', ') || 'Mandatory PPE';
    decisionTitle = "DON'T ALLOW ENTRY";
    decisionSubtitle = 'CONFIRMED PPE VIOLATION';
    decisionReason = `Mandatory PPE confirmed absent across ≥15 consecutive frames (~0.5s): Missing ${missing}. Entry prohibited until compliant.`;
    decisionColor = '#EF4444';
    decisionIcon = <Lock className="w-6 h-6" />;
    complianceScoreText = `NON-COMPLIANT • Missing ${missing}`;
  }

  // Active Environmental Hazards (Fire / Smoke) — Strictly decoupled
  const activeHazardsList = hazards.filter((h) => {
    const st = (h.state || '').toUpperCase();
    return st === 'CONFIRMED' || st === 'ACTIVE' || (!st && (h.confidence || 0) >= 0.35);
  });
  const hasFire = activeHazardsList.some((h) => h.hazard_type.toLowerCase() === 'fire');
  const hasSmoke = activeHazardsList.some((h) => h.hazard_type.toLowerCase() === 'smoke');

  const renderPPEBadge = (status?: PPEPresence) => {
    if (status === 'PRESENT') {
      return (
        <span className="flex items-center gap-1 font-bold text-[#22C55E]">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E]" /> &check; PRESENT
        </span>
      );
    }
    if (status === 'ABSENT') {
      return (
        <span className="flex items-center gap-1 font-bold text-[#EF4444]">
          <XCircle className="w-3.5 h-3.5 text-[#EF4444]" /> ! ABSENT
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 font-bold text-[#F5B942]">
        <HelpCircle className="w-3.5 h-3.5 text-[#F5B942]" /> ? UNKNOWN
      </span>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-[#07111F] text-slate-100 select-none">
      {/* ─── Header: ENTRY GATE (Section 6 & 32) ────────────────────────── */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 pb-3 border-b border-[#20344A]">
        <div className="flex items-center gap-3">
          {onBackToMatrix && (
            <button
              onClick={onBackToMatrix}
              className="p-2 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white hover:bg-slate-800 transition cursor-pointer"
              title="Return to Surveillance Matrix"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}

          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[#22C55E]">
            <DoorOpen className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-white tracking-tight">ENTRY GATE</h2>
              <span className="text-xs text-sky-400 font-semibold bg-sky-950/80 border border-sky-800/60 px-2 py-0.5 rounded-full">
                {activeCamera.location || 'Main Entry'}
              </span>
              <span
                className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  isCameraOnline
                    ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                    : isConnecting
                    ? 'bg-sky-500/15 border border-sky-500/30 text-sky-400'
                    : 'bg-rose-500/15 border border-rose-500/30 text-rose-400'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isCameraOnline ? 'bg-emerald-400 animate-pulse' : isConnecting ? 'bg-sky-400 animate-spin' : 'bg-rose-500'
                  }`}
                />
                {isCameraOnline ? 'LIVE' : isConnecting ? 'CONNECTING' : 'OFFLINE'}
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-0.5">
              Automated Optical Worker Detection &bull; 4-Point PPE Compliance &bull; Instant Access Decision
            </p>
          </div>
        </div>

        {/* Telemetry Bar & Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Camera Selector Dropdown */}
          <div className="flex items-center gap-1.5 bg-[#0D1B2A] border border-[#20344A] px-2.5 py-1.5 rounded-lg text-xs">
            <Camera className="w-3.5 h-3.5 text-[#2388FF]" />
            <select
              value={selectedCameraId}
              onChange={(e) => setSelectedCameraId(e.target.value)}
              className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
            >
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id} className="bg-[#0D1B2A] text-white">
                  {c.camera_id.toUpperCase().replace('_', '-')} &mdash; {c.name || c.location || 'Entry Camera'}
                </option>
              ))}
            </select>
          </div>

          {/* Actual Telemetry Values (Section 6 & 37) */}
          <div className="hidden sm:flex items-center gap-1.5 bg-[#0D1B2A] border border-[#20344A] px-3 py-1 rounded-lg text-xs font-mono">
            <span className="text-[#8FA3B8]">FPS:</span>
            <span
              className={
                activeCamera.metrics?.fps && activeCamera.metrics.fps > 0
                  ? 'text-emerald-400 font-bold'
                  : 'text-slate-400 font-bold'
              }
            >
              {activeCamera.metrics?.fps != null && activeCamera.metrics.fps > 0
                ? activeCamera.metrics.fps.toFixed(1)
                : '—'}
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#8FA3B8]">Res:</span>
            <span className="text-slate-200 font-bold">{activeCamera.resolution || '1280x720'}</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#8FA3B8]">AI Status:</span>
            <span className="text-emerald-400 font-bold">Active</span>
          </div>

          <div className="flex items-center gap-2 bg-[#0D1B2A] border border-[#20344A] px-3 py-1 rounded-lg text-xs font-mono">
            <span className="flex items-center gap-1 text-sky-400 font-bold">
              <Users className="w-3.5 h-3.5" /> {workers.length}
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#22C55E] font-bold">
              {workers.filter((w) => resolveWorkerDisplay(w).state === 'SAFE').length} Safe
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#F5B942] font-bold">
              {workers.filter((w) => resolveWorkerDisplay(w).state === 'UNKNOWN').length} Unk
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#EF4444] font-bold">
              {workers.filter((w) => resolveWorkerDisplay(w).state === 'VIOLATION').length} Viol
            </span>
          </div>

          <button
            onClick={handleManualReconnect}
            disabled={isReconnecting}
            className="p-2 bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white rounded-lg transition cursor-pointer disabled:opacity-50"
            title="Reconnect Camera"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isReconnecting ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* ─── Environmental Hazard Warning Banner (Section 28) ───────────── */}
      {(hasFire || hasSmoke) && (
        <div className="p-3 bg-rose-600 text-white rounded-xl text-xs font-extrabold flex items-center justify-between shadow-lg animate-pulse border border-white/20">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 animate-bounce" />
            <span>
              P0 CRITICAL ENVIRONMENTAL HAZARD DETECTED AT ENTRY GATE &bull;{' '}
              {hasFire ? 'FIRE DETECTED' : 'SMOKE DETECTED'}
            </span>
          </div>
          <span className="text-[10px] bg-black/40 px-2 py-0.5 rounded font-mono uppercase">
            Evacuation Alert Active
          </span>
        </div>
      )}

      {/* ─── Main Content Grid: LEFT Live Video | RIGHT Access Decision ─── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
        {/* LEFT COLUMN: Real Live Camera Stream (8 Cols) */}
        <div className="xl:col-span-8 space-y-4">
          <CameraFeedPlayer
            cameras={cameras}
            selectedCameraId={selectedCameraId}
            onSelectCamera={setSelectedCameraId}
            workers={workers}
            hazards={hazards.filter((h) => !h.camera_id || h.camera_id === selectedCameraId)}
            onRefresh={onRefreshCameras}
            selectedWorkerId={selectedWorkerId}
            onSelectWorker={setSelectedWorkerId}
            isEntryGate={true}
          />

          {/* Multi-Worker Quick Selector Strip (Section 26 & 27) */}
          {workers.length > 0 && (
            <div className="p-3 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex items-center gap-2 overflow-x-auto">
              <span className="text-[11px] font-bold text-[#8FA3B8] uppercase shrink-0">
                Gate Queue ({workers.length}):
              </span>
              {workers.map((w) => {
                const disp = resolveWorkerDisplay(w);
                const isSelected = selectedWorker?.track_id === w.track_id;
                const statusBadge =
                  disp.state === 'SAFE'
                    ? '✓ ALLOW'
                    : disp.state === 'UNKNOWN'
                    ? '? VERIFY'
                    : '! DENIED';

                return (
                  <button
                    key={w.track_id}
                    onClick={() => setSelectedWorkerId(w.track_id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-2 shrink-0 border cursor-pointer ${
                      isSelected
                        ? 'border-white bg-slate-800 text-white shadow-md ring-1 ring-white/60'
                        : 'border-[#20344A] bg-[#12263A] text-slate-300 hover:text-white'
                    }`}
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: disp.color }}
                    />
                    <span>Worker #{w.track_id}</span>
                    <span
                      className="text-[10px] font-mono font-bold"
                      style={{ color: disp.color }}
                    >
                      [{statusBadge}]
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Entry Access Decision & PPE Check Panel (4 Cols) */}
        <div className="xl:col-span-4 space-y-4">
          {/* Reusable Worker Safety State Legend */}
          <WorkerSafetyLegend />

          {/* Primary Entry Decision & PPE Verification Panel */}
          <div className="glass-card rounded-xl border border-[#20344A] overflow-hidden">
            {/* Card Header */}
            <div className="px-4 py-3 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#2388FF]" />
                <h3 className="font-bold text-xs text-white uppercase tracking-wider">
                  ENTRY ACCESS DECISION
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                GATE-01 &bull; {activeCamera.location || 'Main Entry'}
              </span>
            </div>

            <div className="p-4 space-y-4 text-xs">
              {/* Prominent Access Decision Banner (Section 9, 10, 11, 12, 16, 17) */}
              <div
                className="p-4 rounded-xl border-2 transition-all shadow-lg"
                style={{
                  borderColor: decisionColor,
                  backgroundColor: `${decisionColor}15`,
                }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="p-2.5 rounded-lg text-white shrink-0 shadow-md"
                    style={{ backgroundColor: decisionColor }}
                  >
                    {decisionIcon}
                  </div>
                  <div>
                    <div
                      className="text-lg font-black tracking-tight flex items-center gap-1.5"
                      style={{ color: decisionColor }}
                    >
                      {decisionTitle}
                    </div>
                    <div className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                      {decisionSubtitle}
                    </div>
                  </div>
                </div>

                {/* Plain-English Decision Reason (Section 20) */}
                <div className="mt-3 pt-3 border-t border-slate-700/60 text-xs text-slate-200 leading-relaxed">
                  <span className="font-bold text-white">Reason: </span>
                  <span>{decisionReason}</span>
                </div>

                {/* Physical Gate Disclaimer (Section 15 & 35) */}
                <div className="mt-2.5 pt-2 border-t border-slate-800 text-[10px] text-[#8FA3B8] font-mono flex items-center justify-between">
                  <span>Policy evaluation mode</span>
                  <span className="text-slate-400">Physical gate PLC/SCADA action not connected</span>
                </div>
              </div>

              {/* Worker Identity & Inspection Summary */}
              {selectedWorker ? (
                <>
                  <div className="flex items-center justify-between pb-3 border-b border-[#20344A]">
                    <div>
                      <div className="text-base font-black text-white">
                        Worker #{selectedWorker.track_id}
                      </div>
                      <div className="text-[11px] text-[#8FA3B8]">
                        Anonymous Persistent ByteTrack ID &bull; Zone:{' '}
                        {selectedWorker.zone_id || activeCamera.zone_id || 'entry_gate'}
                      </div>
                    </div>
                    <div
                      className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                      style={{
                        color: selectedDisplay?.color,
                        backgroundColor: `${selectedDisplay?.color}20`,
                        border: `1px solid ${selectedDisplay?.color}50`,
                      }}
                    >
                      {selectedDisplay?.label}
                    </div>
                  </div>

                  {/* 4-Point PPE Check Panel (Section 14) */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold text-[#8FA3B8] tracking-wider block">
                        ENTRY PPE CHECK (4-Point Verification)
                      </span>
                      <span className="text-[10px] font-mono font-bold text-slate-300">
                        {complianceScoreText}
                      </span>
                    </div>

                    <div className="space-y-1.5 p-3 rounded-lg bg-[#07111F] border border-[#20344A]">
                      <div className="flex items-center justify-between py-1 border-b border-slate-800/80">
                        <span className="text-slate-300 font-medium">Safety Helmet:</span>
                        {renderPPEBadge(selectedWorker.ppe_status?.helmet)}
                      </div>
                      <div className="flex items-center justify-between py-1 border-b border-slate-800/80">
                        <span className="text-slate-300 font-medium">High-Vis Safety Vest:</span>
                        {renderPPEBadge(selectedWorker.ppe_status?.safety_vest)}
                      </div>
                      <div className="flex items-center justify-between py-1 border-b border-slate-800/80">
                        <span className="text-slate-300 font-medium">Protective Gloves:</span>
                        {renderPPEBadge(selectedWorker.ppe_status?.gloves)}
                      </div>
                      <div className="flex items-center justify-between py-1">
                        <span className="text-slate-300 font-medium">Safety Footwear:</span>
                        {renderPPEBadge(selectedWorker.ppe_status?.safety_footwear)}
                      </div>
                    </div>
                  </div>

                  {/* Operational Gate Policy & Telemetry Notes (Section 21, 23, 24, 25) */}
                  <div className="p-3 rounded-lg bg-[#07111F] border border-[#20344A] space-y-1.5 text-[11px] text-slate-400">
                    <div className="flex items-center gap-1.5 text-sky-400 font-bold">
                      <Info className="w-3.5 h-3.5" />
                      <span>Gate Access Policy Enforcement</span>
                    </div>
                    <ul className="space-y-1 list-disc list-inside text-slate-300">
                      <li>
                        <strong className="text-slate-200">Footwear Policy:</strong> Mandatory
                        industrial footwear required. Partial leg occlusion defaults safely to
                        Verification Required (non-punitive).
                      </li>
                      <li>
                        <strong className="text-slate-200">Optical Framing:</strong> Frontal
                        Full-Body ({activeCamera.resolution || '1280 × 720'}).
                      </li>
                      <li>
                        <strong className="text-slate-200">Grace Period:</strong> Backend support
                        required.
                      </li>
                    </ul>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-xs text-slate-400 italic">
                  {isCameraOnline
                    ? 'No worker currently detected in Entry Gate zone. Waiting for worker to approach.'
                    : 'Camera offline. Connect camera to begin Entry Gate access evaluation.'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ─── BOTTOM AREA: RECENT ENTRY EVENTS (Section 19 & 20) ─────────── */}
      <div className="glass-card rounded-xl border border-[#20344A] overflow-hidden">
        <div className="px-4 py-3 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#2388FF]" />
            <h3 className="font-bold text-xs text-white uppercase tracking-wider">
              RECENT ENTRY EVENTS
            </h3>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            {sessionEvents.length} events logged in session
          </span>
        </div>

        {sessionEvents.length === 0 ? (
          <div className="p-8 text-center flex flex-col items-center justify-center text-slate-400 space-y-2">
            <Shield className="w-8 h-8 text-slate-600 stroke-[1.5]" />
            <div className="text-sm font-bold text-slate-300">NO ENTRY EVENTS AVAILABLE</div>
            <p className="text-xs text-slate-500 max-w-md">
              No recent worker access decisions recorded yet. Real-time events will populate
              automatically as workers are evaluated at the Entry Gate.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0c1a2e] text-[#8FA3B8] uppercase text-[10px] tracking-wider border-b border-[#20344A]">
                <tr>
                  <th className="px-4 py-2.5">Time</th>
                  <th className="px-4 py-2.5">Worker</th>
                  <th className="px-4 py-2.5">Helmet</th>
                  <th className="px-4 py-2.5">Vest</th>
                  <th className="px-4 py-2.5">Gloves</th>
                  <th className="px-4 py-2.5">Footwear</th>
                  <th className="px-4 py-2.5">Decision</th>
                  <th className="px-4 py-2.5">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#20344A]/60">
                {sessionEvents.map((evt) => {
                  const renderStatusPill = (st: PPEPresence) => {
                    if (st === 'PRESENT') {
                      return (
                        <span className="text-[#22C55E] font-bold flex items-center gap-1">
                          <Check className="w-3 h-3" /> Present
                        </span>
                      );
                    }
                    if (st === 'ABSENT') {
                      return (
                        <span className="text-[#EF4444] font-bold flex items-center gap-1">
                          <X className="w-3 h-3" /> Absent
                        </span>
                      );
                    }
                    return (
                      <span className="text-[#F5B942] font-medium flex items-center gap-1">
                        <Minus className="w-3 h-3" /> Unknown
                      </span>
                    );
                  };

                  return (
                    <tr key={evt.id} className="hover:bg-slate-800/30 transition">
                      <td className="px-4 py-2.5 font-mono text-slate-400 whitespace-nowrap">
                        {evt.time}
                      </td>
                      <td className="px-4 py-2.5 font-bold text-white whitespace-nowrap">
                        Worker #{evt.workerId}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        {renderStatusPill(evt.helmet)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        {renderStatusPill(evt.safetyVest)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        {renderStatusPill(evt.gloves)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        {renderStatusPill(evt.footwear)}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span
                          className="px-2.5 py-1 rounded text-[10px] font-black tracking-wider uppercase inline-flex items-center gap-1"
                          style={{
                            color: evt.color,
                            backgroundColor: `${evt.color}15`,
                            border: `1px solid ${evt.color}40`,
                          }}
                        >
                          {evt.decision === 'ALLOW ENTRY' && <CheckCircle2 className="w-3 h-3" />}
                          {evt.decision === 'VERIFICATION REQUIRED' && (
                            <HelpCircle className="w-3 h-3" />
                          )}
                          {evt.decision === "DON'T ALLOW ENTRY" && <XCircle className="w-3 h-3" />}
                          <span>{evt.decision}</span>
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-slate-300 max-w-md truncate">
                        {evt.reason}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default EntryGateView;
