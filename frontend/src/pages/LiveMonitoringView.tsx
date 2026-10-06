/**
 * LiveMonitoringView.tsx — SafeSync Professional SOC
 * Premier Hackathon Live Monitor Screen (Section 11 & 12).
 * Integrates:
 *   - Camera Selector & Live Stream HUD
 *   - Telemetry Bar: FPS, Resolution, Workers, Safe, Unknown, Violations
 *   - Real live camera stream with validated tri-state bounding boxes
 *   - Worker Details Panel with live Explainability & 4-Point PPE audit
 *   - WorkerSafetyLegend
 *   - Optional Multi-Camera Surveillance Wall switcher
 */

import React, { useState, useEffect } from 'react';
import {
  Tv,
  RefreshCw,
  Camera,
  Users,
  RotateCcw,
  Download,
  Info,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  Flame,
  Award,
  Sparkles,
} from 'lucide-react';
import { CameraConfig, WorkerTrack, PPEPresence, HazardEventDetail } from '../types';
import { CameraFeedPlayer } from '../components/CameraFeedPlayer';
import { WorkerSafetyLegend } from '../components/WorkerSafetyLegend';
import { resolveWorkerDisplay } from '../utils/workerDisplay';
import { EmptyState } from '../components/ui/EmptyState';
import { API_BASE_URL } from '../utils/constants';
import { reconnectCamera } from '../services/api';
import { DEMO_SCENARIOS } from '../utils/demoScenarios';

interface LiveMonitoringViewProps {
  cameras: CameraConfig[];
  onRefresh?: () => void;
  onNavigateCameras?: () => void;
  isDemoMode?: boolean;
  demoScenario?: string;
  onOpenDemoGuide?: () => void;
}

export const LiveMonitoringView: React.FC<LiveMonitoringViewProps> = ({
  cameras = [],
  onRefresh,
  onNavigateCameras,
  isDemoMode = false,
  demoScenario = 'safe_worker',
  onOpenDemoGuide,
}) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    cameras[0]?.camera_id || 'camera_01'
  );
  const [viewMode, setViewMode] = useState<'focused' | 'matrix'>('focused');
  const [gridLayout, setGridLayout] = useState<'1x1' | '2x2' | '3x3'>('2x2');
  const [liveWorkers, setLiveWorkers] = useState<WorkerTrack[]>([]);
  const [liveHazards, setLiveHazards] = useState<HazardEventDetail[]>([]);
  const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
  const [reconnectingId, setReconnectingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (cameras.length > 0 && !cameras.some((c) => c.camera_id === selectedCameraId)) {
      setSelectedCameraId(cameras[0].camera_id);
    }
  }, [cameras, selectedCameraId]);

  // Fetch live compliance telemetry
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
              if (selectedWorkerId === null && data.workers.length > 0) {
                setSelectedWorkerId(data.workers[0].track_id);
              }
            }
            if (Array.isArray(data.hazards)) {
              setLiveHazards(data.hazards);
            }
          }
        }
      } catch {
        // tolerate dropouts
      }
    };

    fetchLiveCompliance();
    const interval = setInterval(fetchLiveCompliance, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedWorkerId]);

  const activeCamera =
    cameras.find((c) => c.camera_id === selectedCameraId) || cameras[0];

  const handleReconnect = async (e: React.MouseEvent, cameraId: string) => {
    e.stopPropagation();
    setReconnectingId(cameraId);
    setActionError(null);
    try {
      await reconnectCamera(cameraId);
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setActionError(`Reconnect failed: ${err.message}`);
    } finally {
      setTimeout(() => setReconnectingId(null), 1000);
    }
  };

  const handleDownloadSnapshot = (e: React.MouseEvent, cameraId: string) => {
    e.stopPropagation();
    const url = `${API_BASE_URL}/api/cameras/${cameraId}/snapshot?download=1&t=${Date.now()}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = `snapshot_${cameraId}_${Date.now()}.jpg`;
    link.click();
  };

  // Effective workers & hazards: prioritize Demo Mode scenario if active
  const currentScenarioData = isDemoMode && demoScenario ? DEMO_SCENARIOS[demoScenario] : null;
  const effectiveWorkers = currentScenarioData ? currentScenarioData.workers : liveWorkers;
  const effectiveHazards = currentScenarioData ? currentScenarioData.hazards : liveHazards;

  // Metrics computation from effective state
  const displays = effectiveWorkers.map((w) => resolveWorkerDisplay(w));
  const safeCount = displays.filter((d) => d.state === 'SAFE').length;
  const unknownCount = displays.filter((d) => d.state === 'UNKNOWN').length;
  const violationCount = displays.filter((d) => d.state === 'VIOLATION').length;

  const selectedWorker = effectiveWorkers.find((w) => w.track_id === selectedWorkerId) || effectiveWorkers[0];
  const selectedDisplay = selectedWorker ? resolveWorkerDisplay(selectedWorker) : null;

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
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4 bg-[#07111F] text-slate-100 select-none">
      {/* ─── Header: LIVE MONITOR (Section 11) ────────────────────────────── */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 pb-3 border-b border-[#20344A]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-[#2388FF]">
            <Tv className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-white tracking-tight">LIVE MONITOR</h2>
              <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                LIVE
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-0.5">
              Real-time multi-point PPE compliance validation &amp; optical hazard observation
            </p>
          </div>
        </div>

        {/* Telemetry Bar & Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Camera Selector */}
          <div className="flex items-center gap-1.5 bg-[#0D1B2A] border border-[#20344A] px-2.5 py-1.5 rounded-lg text-xs">
            <Camera className="w-3.5 h-3.5 text-[#2388FF]" />
            <select
              value={selectedCameraId}
              onChange={(e) => setSelectedCameraId(e.target.value)}
              className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
            >
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id} className="bg-[#0D1B2A] text-white">
                  {c.camera_id.toUpperCase().replace('_', '-')} &mdash; {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Telemetry Pills (Section 11: FPS, Resolution, Latency, Workers, Safe, Unknown, Violations) */}
          <div className="hidden sm:flex items-center gap-1.5 bg-[#0D1B2A] border border-[#20344A] px-3 py-1 rounded-lg text-xs font-mono">
            <span className="text-[#8FA3B8]">FPS:</span>
            <span className={activeCamera?.metrics?.fps && activeCamera.metrics.fps > 0 ? "text-emerald-400 font-bold" : "text-slate-400 font-bold"}>
              {activeCamera?.metrics?.fps != null && activeCamera.metrics.fps > 0 ? activeCamera.metrics.fps.toFixed(1) : '—'}
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#8FA3B8]">Res:</span>
            <span className="text-slate-200 font-bold">{activeCamera?.resolution || '1280x720'}</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#8FA3B8]">Lat:</span>
            <span className="text-slate-200 font-bold">
              {activeCamera?.metrics?.inference_latency_ms != null && activeCamera.metrics.inference_latency_ms > 0
                ? `${activeCamera.metrics.inference_latency_ms.toFixed(0)}ms`
                : '—'}
            </span>
          </div>

          <div className="flex items-center gap-2 bg-[#0D1B2A] border border-[#20344A] px-3 py-1 rounded-lg text-xs font-mono">
            <span className="flex items-center gap-1 text-sky-400 font-bold">
              <Users className="w-3.5 h-3.5" /> {effectiveWorkers.length}
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#22C55E] font-bold">{safeCount} Safe</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#F5B942] font-bold">{unknownCount} Unk</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-[#EF4444] font-bold">{violationCount} Viol</span>
          </div>

          {/* Active Environmental Hazard Badge (if Fire/Smoke detected) */}
          {effectiveHazards.some(
            (h) => (h.state || '').toUpperCase() === 'CONFIRMED' || (h.confidence || 0) >= 0.35
          ) && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-black bg-[#FF5A36] text-white animate-pulse shadow-md">
              <Flame className="w-3.5 h-3.5 animate-bounce" />
              <span>P0 HAZARD</span>
            </div>
          )}

          {/* View Mode Toggle */}
          <div className="flex items-center p-0.5 rounded-lg bg-[#0D1B2A] border border-[#20344A]">
            <button
              onClick={() => setViewMode('focused')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'focused'
                  ? 'bg-[#2388FF] text-white shadow-xs'
                  : 'text-[#8FA3B8] hover:text-white'
              }`}
            >
              Focused
            </button>
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'matrix'
                  ? 'bg-[#2388FF] text-white shadow-xs'
                  : 'text-[#8FA3B8] hover:text-white'
              }`}
            >
              Matrix
            </button>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white rounded-lg transition"
              title="Refresh Stream Telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Demo Mode Scenario Banner */}
      {isDemoMode && currentScenarioData && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] uppercase font-black px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  DEMO SCENARIO BENCHMARK
                </span>
                <span className="font-bold text-white text-sm">{currentScenarioData.title}</span>
                <span className="text-slate-400 text-xs hidden sm:inline">&bull; {currentScenarioData.subtitle}</span>
              </div>
              <p className="text-slate-300 mt-1 text-xs leading-relaxed max-w-3xl">
                {currentScenarioData.description}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] font-mono">
                <span className="text-[#8FA3B8]">
                  Expected State: <strong className="text-white">{currentScenarioData.expectedSafetyState}</strong>
                </span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-[#8FA3B8]">
                  Tolerance: <strong className="text-sky-300">{currentScenarioData.toleranceFrames} frames (~0.5s)</strong>
                </span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-amber-300/90 italic">{currentScenarioData.highlightNote}</span>
              </div>
            </div>
          </div>
          {onOpenDemoGuide && (
            <button
              onClick={onOpenDemoGuide}
              className="px-3 py-1.5 rounded-lg bg-[#12263A] hover:bg-[#1B3A5C] border border-amber-500/40 text-amber-300 text-xs font-bold transition flex items-center gap-1.5 shrink-0 self-start md:self-center cursor-pointer shadow-sm"
            >
              <span>Hackathon Guide</span>
              <Award className="w-3.5 h-3.5 text-amber-400" />
            </button>
          )}
        </div>
      )}

      {cameras.length === 0 ? (
        <EmptyState
          icon={Camera}
          title="No Cameras Configured"
          description="There are currently no active video streams configured in the SafeSync camera matrix."
          actionText={onNavigateCameras ? 'Configure Camera Matrix' : undefined}
          onAction={onNavigateCameras}
        />
      ) : viewMode === 'focused' ? (
        /* ─── PRIMARY DEMO SCREEN: Focused Feed & Worker Details Panel ─────── */
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
          {/* Main Area: Real Live Video with Bounding Boxes (8 Cols) */}
          <div className="xl:col-span-8 space-y-4">
            <CameraFeedPlayer
              cameras={cameras}
              selectedCameraId={selectedCameraId}
              onSelectCamera={setSelectedCameraId}
              workers={effectiveWorkers}
              hazards={effectiveHazards.filter((h) => !h.camera_id || h.camera_id === selectedCameraId)}
              onRefresh={onRefresh ? () => onRefresh() : undefined}
              selectedWorkerId={selectedWorkerId}
              onSelectWorker={setSelectedWorkerId}
            />

            {/* Quick Worker Selector Strip */}
            {effectiveWorkers.length > 0 && (
              <div className="p-3 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex items-center gap-2 overflow-x-auto">
                <span className="text-[11px] font-bold text-[#8FA3B8] uppercase shrink-0">
                  Select Worker:
                </span>
                {effectiveWorkers.map((w) => {
                  const disp = resolveWorkerDisplay(w);
                  const isSelected = selectedWorker?.track_id === w.track_id;
                  const statusBadge = disp.state === 'SAFE' ? '✓ SAFE' : disp.state === 'UNKNOWN' ? '? UNK' : '! VIOL';
                  return (
                    <button
                      key={w.track_id}
                      onClick={() => setSelectedWorkerId(w.track_id)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shrink-0 border cursor-pointer ${
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
                      <span className="text-[10px] font-mono font-bold" style={{ color: disp.color }}>
                        [{statusBadge}]
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Area: Worker Safety Legend & Worker Details Panel (4 Cols) */}
          <div className="xl:col-span-4 space-y-4">
            {/* Reusable Worker Safety State Legend (Section 10) */}
            <WorkerSafetyLegend />

            {/* Worker Details Panel (Section 11 & 12) */}
            <div className="glass-card rounded-xl border border-[#20344A] overflow-hidden">
              <div className="px-4 py-3 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-[#2388FF]" />
                  <h3 className="font-bold text-xs text-white uppercase tracking-wider">
                    Worker Audit &amp; Explainability
                  </h3>
                </div>
                {selectedWorker && (
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"
                    style={{
                      color: selectedDisplay?.color,
                      backgroundColor: `${selectedDisplay?.color}15`,
                      border: `1px solid ${selectedDisplay?.color}40`,
                    }}
                  >
                    {selectedDisplay?.state === 'SAFE' && '✓ SAFE'}
                    {selectedDisplay?.state === 'UNKNOWN' && '? UNKNOWN'}
                    {selectedDisplay?.state === 'VIOLATION' && '! CONFIRMED VIOLATION'}
                  </span>
                )}
              </div>

              {selectedWorker ? (
                <div className="p-4 space-y-4 text-xs">
                  {/* Worker Title */}
                  <div className="flex items-center justify-between pb-3 border-b border-[#20344A]">
                    <div>
                      <div className="text-base font-black text-white">
                        Worker #{selectedWorker.track_id}
                      </div>
                      <div className="text-[11px] text-[#8FA3B8]">
                        Anonymous Persistent ByteTrack ID &bull; {selectedWorker.zone_id || activeCamera?.zone_id || 'production_floor'}
                      </div>
                    </div>
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: selectedDisplay?.color }}
                    />
                  </div>

                  {/* 4-Point PPE Status Table (Section 11) */}
                  <div className="space-y-2">
                    <span className="text-[10px] uppercase font-bold text-[#8FA3B8] tracking-wider block">
                      4-Point PPE Compliance Checklist
                    </span>
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

                  {/* Explainability Section (Section 12) */}
                  <div className="p-3 rounded-lg bg-[#07111F] border border-[#20344A] space-y-1.5">
                    <div className="flex items-center gap-1.5 text-sky-400 font-bold text-[11px]">
                      <Info className="w-3.5 h-3.5" />
                      <span>Validation Assessment &amp; Explainability</span>
                    </div>
                    <div className="text-[11px] text-slate-300 leading-relaxed">
                      {selectedDisplay?.state === 'SAFE' && (
                        <span>
                          Worker confirmed 100% compliant. All 4 required PPE classes detected above approved confidence thresholds.
                        </span>
                      )}
                      {selectedDisplay?.state === 'UNKNOWN' && (
                        <span>
                          Visibility insufficient for confirmation: Camera angle or visual occlusion prevents definitive verification. Worker is not penalized.
                        </span>
                      )}
                      {selectedDisplay?.state === 'VIOLATION' && (
                        <span>
                          Mandatory PPE confirmed absent across &ge;15 consecutive frames (~0.5s) in clearly visible anatomical zones.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-400 italic">
                  No worker currently selected. Click a worker box in the video to inspect.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* ─── MULTI-CAMERA MATRIX GRID (Optional Wall Switcher) ──────────── */
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300">Surveillance Wall Matrix</span>
            <div className="flex items-center p-1 rounded-lg bg-[#0D1B2A] border border-[#20344A]">
              {(['1x1', '2x2', '3x3'] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setGridLayout(l)}
                  className={`px-2 py-0.5 text-xs font-semibold rounded ${
                    gridLayout === l ? 'bg-[#2388FF] text-white' : 'text-[#8FA3B8]'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div
            className={`grid gap-4 ${
              gridLayout === '1x1'
                ? 'grid-cols-1'
                : gridLayout === '2x2'
                ? 'grid-cols-1 md:grid-cols-2'
                : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
            }`}
          >
            {cameras.map((camera) => {
              const isOnline =
                camera.state === 'CONNECTED' || camera.state === 'STREAMING' || camera.status === 'ACTIVE';
              const isReconnecting = reconnectingId === camera.camera_id;

              return (
                <div
                  key={camera.camera_id}
                  onClick={() => {
                    setSelectedCameraId(camera.camera_id);
                    setViewMode('focused');
                  }}
                  className="glass-card rounded-xl border border-[#20344A] overflow-hidden flex flex-col hover:border-[#2388FF] transition cursor-pointer"
                >
                  <div className="px-3 py-2 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between text-xs font-bold">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
                        }`}
                      />
                      <span className="text-white">
                        {camera.camera_id.toUpperCase().replace('_', '-')} &mdash; {camera.name}
                      </span>
                    </div>
                    <span
                      className={`text-[9px] px-2 py-0.5 rounded font-mono font-bold ${
                        isOnline ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                      }`}
                    >
                      {isReconnecting ? 'RECONNECTING' : isOnline ? 'LIVE' : 'OFFLINE'}
                    </span>
                  </div>

                  <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden group">
                    {isOnline ? (
                      <img
                        alt={camera.name}
                        src={`${API_BASE_URL}/api/cameras/${camera.camera_id}/stream`}
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = `${API_BASE_URL}/api/cameras/${camera.camera_id}/snapshot?t=${Date.now()}`;
                        }}
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-500 p-6 text-center">
                        <Camera className="w-8 h-8 text-slate-600 mb-1" />
                        <span className="text-xs font-semibold text-slate-400">Stream Offline</span>
                      </div>
                    )}

                    <div className="absolute bottom-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition bg-black/80 p-1 rounded border border-slate-700">
                      <button
                        onClick={(e) => handleReconnect(e, camera.camera_id)}
                        className="p-1 text-slate-300 hover:text-white"
                        title="Reconnect"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => handleDownloadSnapshot(e, camera.camera_id)}
                        className="p-1 text-slate-300 hover:text-white"
                        title="Snapshot"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveMonitoringView;
