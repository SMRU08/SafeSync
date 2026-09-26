/**
 * CameraLiveCard.tsx — SafeSync Professional SOC
 * High-performance, fault-isolated surveillance card with real MJPEG live stream,
 * real operational metrics (FPS, Latency, Dropped Frames, Reconnects),
 * independent error boundary with retry, and full surveillance controls.
 */

import React, { useState, useRef } from 'react';
import {
  Maximize2,
  Minimize2,
  RefreshCw,
  Cpu,
  Trash2,
  Upload,
  AlertTriangle,
  Users,
  VideoOff,
  MapPin,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface CameraLiveCardProps {
  camera: CameraConfig;
  onRefresh?: (cameraId: string) => void;
  onDelete?: (cameraId: string) => void;
  onAnalyzeLive?: (camera: CameraConfig) => void;
  onUploadAnalyze?: (camera: CameraConfig, file: File) => void;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
}

export const CameraLiveCard: React.FC<CameraLiveCardProps> = ({
  camera,
  onRefresh,
  onDelete,
  onAnalyzeLive,
  onUploadAnalyze,
  onToggleSpeaker,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [streamKey, setStreamKey] = useState(Date.now());
  const [hasStreamError, setHasStreamError] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isLive =
    (camera.status === 'online' || camera.status === 'ACTIVE' || camera.state === 'CONNECTED') &&
    !hasStreamError;
  const isConnecting =
    camera.status === 'connecting' ||
    camera.state === 'CONNECTING' ||
    camera.state === 'RECONNECTING';
  const isError =
    camera.status === 'error' || camera.state === 'ERROR' || hasStreamError;

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

  const handleRetry = async () => {
    setIsRetrying(true);
    setHasStreamError(false);
    setStreamKey(Date.now());
    if (onRefresh) {
      await onRefresh(camera.camera_id);
    }
    setTimeout(() => setIsRetrying(false), 1000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUploadAnalyze) {
      onUploadAnalyze(camera, file);
    }
    if (e.target) e.target.value = '';
  };

  const streamSrc = `${API_BASE_URL}/api/cameras/${camera.camera_id}/stream?t=${streamKey}`;
  const displayFps = camera.fps > 0 ? camera.fps.toFixed(1) : (camera.metrics?.fps?.toFixed(1) ?? '0.0');
  const droppedFrames = camera.metrics?.dropped_frames ?? 0;
  const reconnects = camera.metrics?.reconnect_count ?? 0;
  const latencyMs = camera.metrics?.inference_latency_ms ?? 0;
  const activeWorkers = camera.metrics?.active_workers ?? 0;
  const violations = camera.metrics?.active_violations ?? 0;

  return (
    <div
      ref={containerRef}
      className={`bg-white rounded-xl border border-slate-200/90 shadow-sm overflow-hidden flex flex-col transition duration-150 hover:shadow-md ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none w-screen h-screen' : ''
      }`}
    >
      {/* ─── Card Header Bar ─────────────────────────────────────────── */}
      <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-2 h-2 rounded-full shrink-0 ${
              isLive
                ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)] animate-pulse'
                : isConnecting
                ? 'bg-amber-500 animate-ping'
                : 'bg-rose-500'
            }`}
          />
          <div className="truncate">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-slate-800 tracking-tight truncate">
                {camera.name || camera.camera_id}
              </span>
              <span className="text-[10px] font-mono uppercase bg-slate-200/80 text-slate-600 px-1.5 py-0.2 rounded font-semibold">
                {camera.camera_id}
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5 truncate">
              <MapPin className="w-2.5 h-2.5 text-slate-400 shrink-0" />
              <span className="truncate">{camera.location || camera.zone_id}</span>
              <span>•</span>
              <span className="font-mono">{camera.resolution || '1280x720'}</span>
            </div>
          </div>
        </div>

        {/* Status Badge & Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
              isLive
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : isConnecting
                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            {isLive ? '🟢 LIVE' : isConnecting ? '🟡 CONNECTING' : isError ? '⚠️ ERROR' : '🔴 OFFLINE'}
          </span>

          {onToggleSpeaker && (
            <button
              onClick={() => onToggleSpeaker(camera.camera_id, camera.speaker_enabled === false)}
              title={`Camera Speaker is ${camera.speaker_enabled !== false ? 'ON (Speech Alerts Enabled)' : 'OFF (Audio Alerts Suppressed)'}`}
              className={`p-1 rounded transition cursor-pointer flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 ${
                camera.speaker_enabled !== false
                  ? 'text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100'
                  : 'text-slate-500 bg-slate-100 border border-slate-200 hover:bg-slate-200'
              }`}
            >
              {camera.speaker_enabled !== false ? (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>SPEAKER ON</span>
                </>
              ) : (
                <>
                  <VolumeX className="w-3.5 h-3.5 text-rose-500" />
                  <span>SPEAKER OFF</span>
                </>
              )}
            </button>
          )}

          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* ─── Video Stream Viewport ───────────────────────────────────── */}
      <div className="relative aspect-video bg-slate-950 overflow-hidden flex items-center justify-center select-none group">
        {isLive ? (
          <img
            key={streamKey}
            src={streamSrc}
            alt={camera.name}
            onError={() => setHasStreamError(true)}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center text-slate-400">
            <VideoOff className="w-10 h-10 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs font-semibold text-slate-300">
              {isConnecting ? 'Establishing camera connection...' : `Camera ${camera.camera_id} connection failed`}
            </p>
            <p className="text-[10px] text-slate-500 mt-1 max-w-[240px]">
              {camera.safe_source ? `Source: ${camera.safe_source}` : 'Hardware feed unreachable'}
            </p>
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-md text-[11px] font-semibold transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${isRetrying ? 'animate-spin' : ''}`} />
              Retry Connection
            </button>
          </div>
        )}

        {/* Live HUD Badges Overlay */}
        {isLive && (
          <>
            <div className="absolute top-2 left-2 flex items-center gap-1.5">
              <span className="bg-slate-900/80 backdrop-blur-sm text-white text-[9px] font-mono font-bold px-2 py-0.5 rounded border border-white/10 shadow-sm flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                {displayFps} FPS
              </span>
              {violations > 0 && (
                <span className="bg-rose-600/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-0.5">
                  <AlertTriangle className="w-2.5 h-2.5" /> {violations} VIOLATION
                </span>
              )}
            </div>

            <div className="absolute top-2 right-2">
              <span className="bg-slate-900/80 backdrop-blur-sm text-slate-300 text-[9px] font-mono px-2 py-0.5 rounded border border-white/10">
                {camera.zone_id}
              </span>
            </div>
          </>
        )}

        {/* Hover Quick Action Overlay */}
        <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition duration-150 flex items-center gap-1 bg-slate-900/80 backdrop-blur-sm p-1 rounded-lg border border-white/10">
          <button
            onClick={handleRetry}
            title="Refresh Live Stream"
            className="p-1.5 rounded text-slate-300 hover:text-white hover:bg-white/10 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onAnalyzeLive?.(camera)}
            title="Analyze Live Feed with AI"
            className="p-1.5 rounded text-sky-400 hover:text-sky-300 hover:bg-white/10 transition"
          >
            <Cpu className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Upload Frame for AI Analysis"
            className="p-1.5 rounded text-amber-400 hover:text-amber-300 hover:bg-white/10 transition"
          >
            <Upload className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Hidden File Input for Image Upload Analysis */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="hidden"
      />

      {/* ─── Operational Telemetry Bar ───────────────────────────────── */}
      <div className="px-3 py-2 bg-white border-t border-slate-100 grid grid-cols-5 gap-1 text-center text-slate-600">
        <div className="flex flex-col">
          <span className="text-[9px] font-medium text-slate-400">FPS</span>
          <span className="text-xs font-bold font-mono text-slate-800">
            {displayFps}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[9px] font-medium text-slate-400">Latency</span>
          <span className="text-xs font-bold font-mono text-slate-800">
            {latencyMs > 0 ? `${latencyMs.toFixed(0)}ms` : '--'}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[9px] font-medium text-slate-400">Workers</span>
          <span className="text-xs font-bold font-mono text-sky-700 flex items-center justify-center gap-0.5">
            <Users className="w-2.5 h-2.5" /> {activeWorkers}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[9px] font-medium text-slate-400">Drops</span>
          <span className={`text-xs font-bold font-mono ${droppedFrames > 0 ? 'text-amber-600' : 'text-slate-500'}`}>
            {droppedFrames}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[9px] font-medium text-slate-400">Retries</span>
          <span className={`text-xs font-bold font-mono ${reconnects > 0 ? 'text-rose-600' : 'text-slate-500'}`}>
            {reconnects}
          </span>
        </div>
      </div>

      {/* ─── Control Toolbar Footer ──────────────────────────────────── */}
      <div className="px-3 py-2 bg-slate-50/80 border-t border-slate-200 flex items-center justify-between gap-2 mt-auto">
        <div className="flex items-center gap-1">
          <button
            onClick={() => onAnalyzeLive?.(camera)}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-50 border border-sky-200 hover:bg-sky-100 text-sky-800 text-[10px] font-bold transition"
          >
            <Cpu className="w-3 h-3" /> Analyze Live
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 border border-slate-200 hover:bg-slate-200 text-slate-700 text-[10px] font-semibold transition"
          >
            <Upload className="w-3 h-3" /> Upload
          </button>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleRetry}
            title="Reconnect Camera"
            className="p-1 rounded text-slate-500 hover:text-sky-700 hover:bg-slate-200 transition"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
          {onDelete && (
            <button
              onClick={() => {
                if (window.confirm(`Are you sure you want to remove camera "${camera.name || camera.camera_id}"?`)) {
                  onDelete(camera.camera_id);
                }
              }}
              title="Remove Camera"
              className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
