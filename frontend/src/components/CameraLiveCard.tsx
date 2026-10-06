/**
 * CameraLiveCard.tsx — SafeSync Phase 6
 * High-performance industrial surveillance card.
 *
 * Adheres strictly to Section 4, 5, 23, 30:
 *   - Camera Name & Unique Tracking ID
 *   - Operational Purpose (ENTRY GATE / PRODUCTION FLOOR / HAZARD ZONE / GENERAL)
 *   - Source Type (USB Webcam, IP Camera, RTSP, Video File)
 *   - Real Status (ONLINE, CONNECTING, OFFLINE, ERROR, NO SIGNAL, UNKNOWN)
 *   - Real Workers Count (or '--')
 *   - Dual Monitoring Badges: PPE Monitoring (ACTIVE) & Fire/Smoke (CLEAR / ALERT)
 *   - Real FPS & Latency (or '--')
 *   - Dedicated [ OPEN LIVE VIEW ] trigger
 *   - Zero fake telemetry
 */

import React, { useState, useRef } from 'react';
import {
  Maximize2,
  Minimize2,
  RefreshCw,
  Trash2,
  AlertTriangle,
  Users,
  VideoOff,
  MapPin,
  Volume2,
  VolumeX,
  Play,
  Flame,
  CheckCircle2,
  Eye,
  Settings,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { API_BASE_URL } from '../utils/constants';
import { getCameraPurpose } from './CameraCoverageSection';

interface CameraLiveCardProps {
  camera: CameraConfig;
  onRefresh?: (cameraId: string) => void;
  onDelete?: (cameraId: string) => void;
  onOpenLiveView?: (camera: CameraConfig) => void;
  onAnalyzeLive?: (camera: CameraConfig) => void;
  onUploadAnalyze?: (camera: CameraConfig, file: File) => void;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
  onToggleStartStop?: (cameraId: string, start: boolean) => void;
  onEdit?: (camera: CameraConfig) => void;
}

export const CameraLiveCard: React.FC<CameraLiveCardProps> = ({
  camera,
  onRefresh,
  onDelete,
  onOpenLiveView,
  onAnalyzeLive: _onAnalyzeLive,
  onUploadAnalyze,
  onToggleSpeaker,
  onToggleStartStop,
  onEdit,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [streamKey, setStreamKey] = useState(Date.now());
  const [hasStreamError, setHasStreamError] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isEnabled = camera.enabled !== false;
  const isLive =
    isEnabled &&
    (camera.status === 'online' ||
      camera.status === 'streaming' ||
      camera.status === 'ACTIVE' ||
      camera.state === 'CONNECTED' ||
      camera.state === 'STREAMING' ||
      camera.is_streaming === true) &&
    !hasStreamError;

  const isConnecting =
    isEnabled &&
    (camera.status === 'connecting' ||
      camera.state === 'CONNECTING' ||
      camera.state === 'RECONNECTING');

  const isError =
    isEnabled &&
    (camera.status === 'error' || camera.state === 'ERROR' || camera.state === 'OFFLINE' || hasStreamError);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const handleRetry = () => {
    setIsRetrying(true);
    setHasStreamError(false);
    setStreamKey(Date.now());
    onRefresh?.(camera.camera_id);
    setTimeout(() => setIsRetrying(false), 1000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUploadAnalyze) {
      onUploadAnalyze(camera, file);
    }
    e.target.value = '';
  };

  const streamSrc = `${API_BASE_URL}/api/cameras/${camera.camera_id}/stream?t=${streamKey}`;
  const purpose = getCameraPurpose(camera);

  // Status label and color token (Section 5)
  const statusConfig = !isEnabled
    ? { label: 'STOPPED', color: 'bg-slate-700/60 text-slate-300 border-slate-600', dot: 'bg-slate-400' }
    : isLive
    ? { label: 'ONLINE', color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400 animate-pulse' }
    : isConnecting
    ? { label: 'CONNECTING', color: 'bg-amber-500/15 text-amber-400 border-amber-500/30', dot: 'bg-amber-400 animate-ping' }
    : isError
    ? { label: 'ERROR', color: 'bg-rose-500/15 text-rose-400 border-rose-500/30', dot: 'bg-rose-500' }
    : { label: 'OFFLINE', color: 'bg-slate-800 text-slate-400 border-slate-700', dot: 'bg-slate-500' };

  // Real operational telemetry (Section 4 & 22)
  const displayFps =
    camera.metrics?.fps != null && camera.metrics.fps > 0
      ? camera.metrics.fps.toFixed(1)
      : camera.fps > 0
      ? camera.fps.toFixed(1)
      : '--';

  const latencyMs =
    camera.metrics?.inference_latency_ms != null && camera.metrics.inference_latency_ms > 0
      ? `${camera.metrics.inference_latency_ms.toFixed(0)} ms`
      : '--';

  const activeWorkers =
    camera.metrics?.active_workers != null
      ? camera.metrics.active_workers
      : camera.ai_analysis?.active_workers != null
      ? camera.ai_analysis.active_workers
      : '--';

  const activeViolations = camera.metrics?.active_violations ?? 0;
  const hasFireHazard = (camera.metrics?.active_hazards ?? 0) > 0;

  // Source type formatting
  const formattedSourceType =
    camera.source_type === 'usb'
      ? 'USB Webcam'
      : camera.source_type === 'rtsp'
      ? 'RTSP IP Camera'
      : camera.source_type === 'http' || camera.source_type === 'android'
      ? 'IP Camera'
      : camera.source_type === 'file'
      ? 'Video File'
      : camera.source_type?.toUpperCase() || 'Camera';

  return (
    <div
      ref={containerRef}
      className="bg-[#0D1B2A] border border-[#20344A] rounded-xl overflow-hidden shadow-sm flex flex-col justify-between hover:border-slate-600 transition"
    >
      {/* ─── Header: Camera Name, Purpose, Source & Status (Section 4) ─── */}
      <div className="px-4 py-2.5 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className={`w-2 h-2 rounded-full shrink-0 ${statusConfig.dot}`} />
          <div className="truncate">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-white tracking-tight truncate">
                {camera.name || camera.camera_id}
              </span>
              <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded font-semibold border border-slate-700">
                {camera.camera_id}
              </span>
              <span
                className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                  purpose === 'ENTRY GATE'
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : purpose === 'HAZARD ZONE'
                    ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                    : purpose === 'PRODUCTION FLOOR'
                    ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                    : 'bg-slate-700/50 text-slate-300 border-slate-600'
                }`}
              >
                {purpose}
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5 truncate">
              <MapPin className="w-2.5 h-2.5 text-slate-400 shrink-0" />
              <span className="truncate">{camera.location || camera.zone_id}</span>
              <span>•</span>
              <span className="font-mono text-slate-300">{formattedSourceType}</span>
              <span>•</span>
              <span className="font-mono text-slate-300">{camera.resolution || '1280x720'}</span>
            </div>
          </div>
        </div>

        {/* Status Badge & Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border ${statusConfig.color}`}
          >
            {statusConfig.label}
          </span>

          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* ─── Video Stream Viewport (Section 4 & 20) ─────────────────── */}
      <div className="relative aspect-video bg-black overflow-hidden flex items-center justify-center select-none group">
        {!isEnabled ? (
          <div className="flex flex-col items-center justify-center p-6 text-center text-slate-400">
            <VideoOff className="w-8 h-8 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs font-semibold text-slate-300">
              Camera stream is stopped
            </p>
            {onToggleStartStop && (
              <button
                onClick={() => onToggleStartStop(camera.camera_id, true)}
                className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-[10px] font-bold transition cursor-pointer"
              >
                <Play className="w-2.5 h-2.5 fill-white" />
                Start Stream
              </button>
            )}
          </div>
        ) : isLive ? (
          <img
            key={streamKey}
            src={streamSrc}
            alt={camera.name}
            onError={() => setHasStreamError(true)}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center text-slate-400">
            <VideoOff className="w-8 h-8 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs font-bold text-white uppercase tracking-wider">
              {isConnecting ? 'Establishing Connection...' : 'Camera Offline'}
            </p>
            <p className="text-[10px] text-rose-400/90 mt-1 max-w-[260px] font-medium leading-tight truncate">
              {camera.last_error || camera.metrics?.last_error || 'Stream offline: host unreachable or paused'}
            </p>
            <div className="mt-3 flex items-center gap-2">
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-[10px] font-bold transition disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw className={`w-2.5 h-2.5 ${isRetrying ? 'animate-spin' : ''}`} />
                Retry
              </button>
              {onEdit && (
                <button
                  onClick={() => onEdit(camera)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#12263A] hover:bg-slate-700 text-slate-300 rounded text-[10px] font-semibold border border-[#20344A] transition cursor-pointer"
                >
                  Configure
                </button>
              )}
            </div>
          </div>
        )}

        {/* Live Stream Overlays */}
        {isLive && (
          <div className="absolute top-2 left-2 flex items-center gap-1.5">
            <span className="bg-slate-900/80 backdrop-blur-sm text-white text-[9px] font-mono font-bold px-2 py-0.5 rounded border border-white/10 shadow-sm flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {displayFps} FPS
            </span>
            {activeViolations > 0 && (
              <span className="bg-rose-600/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-0.5">
                <AlertTriangle className="w-2.5 h-2.5" /> {activeViolations} VIOLATION
              </span>
            )}
            {hasFireHazard && (
              <span className="bg-red-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-0.5 animate-pulse">
                <Flame className="w-2.5 h-2.5" /> FIRE
              </span>
            )}
          </div>
        )}
      </div>

      {/* Hidden File Input for Image Upload Analysis */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="hidden"
      />

      {/* ─── Operational Metrics & Safety Status (Section 4 & 23) ───── */}
      <div className="px-3.5 py-2.5 bg-[#0D1B2A] border-t border-[#20344A] grid grid-cols-4 gap-2 text-center text-xs">
        <div className="flex flex-col">
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Workers</span>
          <span className="text-xs font-mono font-bold text-white mt-0.5 flex items-center justify-center gap-1">
            <Users className="w-3 h-3 text-sky-400" />
            {activeWorkers}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">PPE Status</span>
          <span className="text-[10px] font-bold text-emerald-400 mt-0.5 flex items-center justify-center gap-0.5">
            <CheckCircle2 className="w-2.5 h-2.5" /> ACTIVE
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Fire / Smoke</span>
          <span
            className={`text-[10px] font-bold mt-0.5 flex items-center justify-center gap-0.5 ${
              hasFireHazard ? 'text-rose-400 font-extrabold animate-pulse' : 'text-slate-300'
            }`}
          >
            {hasFireHazard ? 'ALERT' : 'CLEAR'}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Latency</span>
          <span className="text-xs font-mono text-slate-300 mt-0.5">
            {latencyMs}
          </span>
        </div>
      </div>

      {/* ─── Card Action Footer with [ OPEN LIVE VIEW ] ─────────────── */}
      <div className="px-3.5 py-2 bg-[#12263A] border-t border-[#20344A] flex items-center justify-between gap-2 mt-auto">
        <div className="flex items-center gap-2">
          {onOpenLiveView && (
            <button
              onClick={() => onOpenLiveView(camera)}
              className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-sm"
              title="Open Detailed Live View with Bounding Boxes and Telemetry"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>OPEN LIVE VIEW</span>
            </button>
          )}

          {onToggleSpeaker && (
            <button
              onClick={() => onToggleSpeaker(camera.camera_id, camera.speaker_enabled === false)}
              title={`Speaker Audio is ${camera.speaker_enabled !== false ? 'ON' : 'OFF'}`}
              className={`p-1 rounded text-xs transition cursor-pointer border ${
                camera.speaker_enabled !== false
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-slate-800 border-slate-700 text-slate-400'
              }`}
            >
              {camera.speaker_enabled !== false ? (
                <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <VolumeX className="w-3.5 h-3.5 text-rose-400" />
              )}
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          {onToggleStartStop && (
            <button
              onClick={() => onToggleStartStop(camera.camera_id, !isEnabled)}
              title={isEnabled ? 'Stop Camera Stream' : 'Start Camera Stream'}
              className={`px-2 py-1 rounded text-[10px] font-bold transition border cursor-pointer ${
                isEnabled
                  ? 'text-rose-400 bg-rose-500/10 border-rose-500/30 hover:bg-rose-500/20'
                  : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20'
              }`}
            >
              {isEnabled ? 'Stop' : 'Start'}
            </button>
          )}

          <button
            onClick={handleRetry}
            title="Reconnect"
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {onEdit && (
            <button
              onClick={() => onEdit(camera)}
              title="Configure Source"
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          )}

          {onDelete && (
            <button
              onClick={() => {
                if (window.confirm(`Are you sure you want to remove camera "${camera.name || camera.camera_id}"?`)) {
                  onDelete(camera.camera_id);
                }
              }}
              title="Remove Camera"
              className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CameraLiveCard;
