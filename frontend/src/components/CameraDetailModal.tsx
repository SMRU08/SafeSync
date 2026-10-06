/**
 * CameraDetailModal.tsx — SafeSync Phase 6
 * Full Detailed Live Camera Inspector & Safety Diagnostic Modal.
 *
 * Adheres strictly to Section 6, 7, 8, 9, 20 & 22:
 *   - Live Video stream with real bounding boxes (Safe = Green, Unknown = Yellow, Violation = Red)
 *   - Decoupled Fire / Smoke hazard overlays
 *   - Hardware & Stream Information (Source, Resolution, FPS, Latency, Connection, V3 Model)
 *   - Safety Status breakdown (Safe, Unknown, Violations, Fire, Smoke)
 *   - Qualitative Coverage & Visibility suitability explanation (Good, Limited, Insufficient)
 *   - Offline Diagnostic error card with actionable causes
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  RefreshCw,
  Camera,
  DoorOpen,
  Volume2,
  VolumeX,
  Settings,
  Eye,
  Info,
  Shield,
  VideoOff,
} from 'lucide-react';
import { CameraConfig, WorkerTrack, HazardEventDetail } from '../types';
import { CameraFeedPlayer } from './CameraFeedPlayer';
import { getCameraPurpose, getCameraCoverageStatus } from './CameraCoverageSection';
import { API_BASE_URL } from '../utils/constants';

interface CameraDetailModalProps {
  camera: CameraConfig | null;
  isOpen: boolean;
  onClose: () => void;
  onReconnect?: (cameraId: string) => void;
  onEdit?: (camera: CameraConfig) => void;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
  onLaunchEntryGate?: () => void;
}

export const CameraDetailModal: React.FC<CameraDetailModalProps> = ({
  camera,
  isOpen,
  onClose,
  onReconnect,
  onEdit,
  onToggleSpeaker,
  onLaunchEntryGate,
}) => {
  const [liveWorkers, setLiveWorkers] = useState<WorkerTrack[]>([]);
  const [liveHazards, setLiveHazards] = useState<HazardEventDetail[]>([]);
  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    if (!camera || !isOpen) return;

    let isMounted = true;
    const fetchCameraLive = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/compliance/live?camera_id=${encodeURIComponent(camera.camera_id)}`);
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data) {
            if (Array.isArray(data.workers)) setLiveWorkers(data.workers);
            if (Array.isArray(data.hazards)) setLiveHazards(data.hazards);
          }
        }
      } catch {
        // tolerate dropouts
      }
    };

    fetchCameraLive();
    const interval = setInterval(fetchCameraLive, 1200);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [camera?.camera_id, isOpen]);

  if (!isOpen || !camera) return null;

  const purpose = getCameraPurpose(camera);
  const coverage = getCameraCoverageStatus(camera);

  const isEnabled = camera.enabled !== false;
  const isOnline =
    isEnabled &&
    (camera.status === 'online' ||
      camera.status === 'ACTIVE' ||
      camera.status === 'streaming' ||
      camera.state === 'CONNECTED' ||
      camera.state === 'STREAMING');
  const isConnecting =
    isEnabled &&
    (camera.status === 'connecting' ||
      camera.state === 'CONNECTING' ||
      camera.state === 'RECONNECTING');
  const isError =
    isEnabled && (camera.status === 'error' || camera.state === 'ERROR');

  const statusLabel = !isOnline && !isConnecting && !isError
    ? 'OFFLINE'
    : isOnline
    ? 'ONLINE'
    : isConnecting
    ? 'CONNECTING'
    : 'ERROR';

  // Live safety metrics from real workers
  const safeWorkersCount = liveWorkers.filter((w) => w.overall_status === 'COMPLIANT' || w.overall_compliant).length;
  const violationWorkersCount = liveWorkers.filter(
    (w) => w.overall_status === 'NON_COMPLIANT' || (w.missing_items && w.missing_items.length > 0)
  ).length;
  const unknownWorkersCount = liveWorkers.filter(
    (w) => w.overall_status === 'UNKNOWN' || (!w.overall_compliant && violationWorkersCount === 0)
  ).length;

  const hasFire = liveHazards.some((h) => h.hazard_type === 'fire') || (camera.metrics?.active_hazards ?? 0) > 0;
  const hasSmoke = liveHazards.some((h) => h.hazard_type === 'smoke');

  const handleRetry = async () => {
    setIsReconnecting(true);
    try {
      await onReconnect?.(camera.camera_id);
    } finally {
      setTimeout(() => setIsReconnecting(false), 800);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0D1B2A] text-[#E8F0F7] rounded-2xl shadow-2xl border border-[#20344A] w-full max-w-5xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* ─── Modal Header Bar (Section 6) ─────────────────────────────── */}
        <div className="px-5 py-3.5 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm border shrink-0 ${
                isOnline
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : isConnecting
                  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                  : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
              }`}
            >
              <Camera className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-white tracking-tight truncate">
                  {camera.name || camera.camera_id}
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 uppercase font-semibold">
                  {camera.camera_id}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                    statusLabel === 'ONLINE'
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : statusLabel === 'CONNECTING'
                      ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      statusLabel === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                    }`}
                  />
                  {statusLabel}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5 truncate">
                <span className="text-sky-400 font-bold">{purpose}</span>
                <span>•</span>
                <span>{camera.location || camera.zone_id || 'Facility Floor'}</span>
                <span>•</span>
                <span className="font-mono text-slate-300">{camera.resolution || '1280x720'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onToggleSpeaker && (
              <button
                onClick={() => onToggleSpeaker(camera.camera_id, camera.speaker_enabled === false)}
                title={`Speaker Audio ${camera.speaker_enabled !== false ? 'ON' : 'OFF'}`}
                className={`p-1.5 rounded-lg border text-xs font-bold transition flex items-center gap-1 cursor-pointer ${
                  camera.speaker_enabled !== false
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
              >
                {camera.speaker_enabled !== false ? (
                  <Volume2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <VolumeX className="w-4 h-4 text-rose-400" />
                )}
              </button>
            )}

            <button
              onClick={handleRetry}
              disabled={isReconnecting}
              title="Reconnect Stream"
              className="p-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white hover:border-slate-600 transition cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${isReconnecting ? 'animate-spin text-sky-400' : ''}`} />
            </button>

            {purpose === 'ENTRY GATE' && onLaunchEntryGate && (
              <button
                onClick={() => {
                  onClose();
                  onLaunchEntryGate();
                }}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-sm"
              >
                <DoorOpen className="w-3.5 h-3.5" /> Launch Gate
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ─── Modal Scrollable Content Surface ───────────────────────────── */}
        <div className="overflow-y-auto p-5 space-y-5 flex-1">
          {/* Main Video Viewport (Section 6 & 7) */}
          <div className="relative rounded-xl overflow-hidden border border-[#20344A] bg-black aspect-video flex items-center justify-center">
            {isOnline ? (
              <CameraFeedPlayer
                cameras={[camera]}
                selectedCameraId={camera.camera_id}
                workers={liveWorkers}
                hazards={liveHazards}
                onRefresh={handleRetry}
              />
            ) : (
              /* Diagnostic Offline Error Card (Section 20) */
              <div className="flex flex-col items-center justify-center p-8 text-center max-w-md">
                <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mb-3">
                  <VideoOff className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  CAMERA OFFLINE
                </h3>
                <p className="text-xs text-rose-300 mt-1 font-semibold">
                  {camera.last_error || camera.metrics?.last_error || 'Unable to receive frames from source.'}
                </p>

                <div className="mt-4 p-3 rounded-xl bg-[#12263A] border border-[#20344A] text-left text-[11px] text-slate-300 space-y-1 w-full">
                  <span className="font-bold text-slate-200 block text-xs mb-1">Possible Causes:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                    <li>Camera hardware is powered off or unplugged</li>
                    <li>IP address or phone IPv4 is unreachable on the network</li>
                    <li>RTSP / MJPEG stream URL or port is incorrect</li>
                    <li>Camera worker loop is paused or stopped</li>
                  </ul>
                </div>

                <div className="mt-5 flex items-center gap-2">
                  <button
                    onClick={handleRetry}
                    disabled={isReconnecting}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isReconnecting ? 'animate-spin' : ''}`} />
                    Retry Connection
                  </button>
                  {onEdit && (
                    <button
                      onClick={() => onEdit(camera)}
                      className="px-4 py-2 bg-[#12263A] hover:bg-slate-700 text-slate-200 border border-[#20344A] rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
                    >
                      <Settings className="w-3.5 h-3.5" />
                      Configure Source
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* ─── Telemetry & Safety Panels Grid (Section 6, 8, 9, 23) ──────── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 1. Camera Information Panel */}
            <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-2.5">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-[#20344A] pb-2">
                <Info className="w-4 h-4 text-sky-400" />
                Camera Information
              </h4>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Source:</span>
                  <span className="font-mono text-slate-200 text-[11px] truncate max-w-[180px]">
                    {camera.safe_source || camera.source_type || 'Hardware USB / Network'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Resolution:</span>
                  <span className="font-mono text-slate-200">{camera.resolution || '1280x720'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Live FPS:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {camera.metrics?.fps != null && camera.metrics.fps > 0
                      ? camera.metrics.fps.toFixed(1)
                      : camera.fps > 0
                      ? camera.fps.toFixed(1)
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Latency:</span>
                  <span className="font-mono text-slate-200">
                    {camera.metrics?.inference_latency_ms != null && camera.metrics.inference_latency_ms > 0
                      ? `${camera.metrics.inference_latency_ms.toFixed(0)} ms`
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Connection State:</span>
                  <span className="font-mono text-sky-400 font-bold">{camera.state || statusLabel}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">AI Model:</span>
                  <span className="text-emerald-400 font-semibold font-mono text-[11px]">SafeSync V3 (LOCKED)</span>
                </div>
              </div>
            </div>

            {/* 2. Safety Status Panel (Decoupled Fire/Smoke) */}
            <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-2.5">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-[#20344A] pb-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                Live Safety Status
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Workers Monitored:</span>
                  <span className="font-mono font-bold text-white">{liveWorkers.length}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-emerald-400 font-medium">Safe (Compliant):</span>
                  <span className="font-mono font-bold text-emerald-400">{safeWorkersCount}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-[#F5B942] font-medium">Unknown / Occluded:</span>
                  <span className="font-mono font-bold text-[#F5B942]">{unknownWorkersCount}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-rose-400 font-medium">Confirmed Violations:</span>
                  <span className="font-mono font-bold text-rose-400">{violationWorkersCount}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Optical Fire State:</span>
                  <span className={`font-bold ${hasFire ? 'text-rose-400 animate-pulse' : 'text-slate-300'}`}>
                    {hasFire ? 'FIRE DETECTED' : 'CLEAR'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">Optical Smoke State:</span>
                  <span className={`font-bold ${hasSmoke ? 'text-amber-400 animate-pulse' : 'text-slate-300'}`}>
                    {hasSmoke ? 'SMOKE DETECTED' : 'CLEAR'}
                  </span>
                </div>
              </div>
            </div>

            {/* 3. Coverage & Optical Visibility Suitability */}
            <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-2.5">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-[#20344A] pb-2">
                <Eye className="w-4 h-4 text-amber-400" />
                Coverage &amp; Visibility
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Coverage Suitability:</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${coverage.color}`}>
                    {coverage.status}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#20344A]/50">
                  <span className="text-slate-400">Configured View:</span>
                  <span className="font-mono text-slate-200 text-[11px]">{coverage.configuredView}</span>
                </div>
                <div className="pt-1">
                  <span className="text-[10px] font-bold text-slate-400 block mb-1">Optical Geometry Assessment:</span>
                  <p className="text-[11px] text-slate-300 leading-relaxed bg-[#0D1B2A] p-2.5 rounded-lg border border-[#20344A]">
                    {coverage.explanation}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraDetailModal;
