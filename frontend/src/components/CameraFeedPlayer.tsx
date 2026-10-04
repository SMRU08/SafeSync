/**
 * CameraFeedPlayer.tsx — SafeSync Professional SOC
 * High-performance live camera monitor with dynamic camera switcher,
 * real-time ByteTrack worker PPE detection HUD, telemetry bar, and stream controls.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Maximize2,
  Minimize2,
  Pause,
  Play,
  AlertTriangle,
  RefreshCw,
  Check,
  X,
  Minus,
  Flame,
} from 'lucide-react';
import { CameraConfig, WorkerTrack, PPEPresence, HazardEventDetail } from '../types';
import { resolveWorkerDisplay } from '../utils/workerDisplay';
import { API_BASE_URL } from '../utils/constants';
import { reconnectCamera } from '../services/api';

interface CameraFeedPlayerProps {
  cameras: CameraConfig[];
  selectedCameraId?: string;
  onSelectCamera?: (cameraId: string) => void;
  workers?: WorkerTrack[];
  hazards?: HazardEventDetail[];
  onRefresh?: () => void;
}

const getCameraShortTag = (camera?: CameraConfig | null): string => {
  if (!camera) return 'C1';
  const name = camera.name || camera.camera_id || '1';
  const match = name.match(/camera[_\s]*([0-9a-zA-Z]+)/i) || (camera.camera_id && camera.camera_id.match(/camera_?([0-9a-zA-Z]+)/i));
  if (match) {
    const rawId = match[1].replace(/^0+/, '') || '1';
    return `C${rawId.toUpperCase()}`;
  }
  const clean = name.trim();
  if (/^[0-9]+$/.test(clean)) return `C${parseInt(clean, 10)}`;
  return `C${clean.charAt(0).toUpperCase()}`;
};

export const CameraFeedPlayer: React.FC<CameraFeedPlayerProps> = ({
  cameras,
  selectedCameraId,
  onSelectCamera,
  workers = [],
  hazards = [],
  onRefresh,
}) => {
  const [activeCamId, setActiveCamId] = useState<string>(
    selectedCameraId || (cameras[0]?.camera_id ?? 'camera_01')
  );
  const [isPaused, setIsPaused] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hasStreamError, setHasStreamError] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [streamType, setStreamType] = useState<'mjpeg' | 'snapshot'>('mjpeg');
  const [snapshotTimestamp, setSnapshotTimestamp] = useState<number>(Date.now());
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const videoImgRef = useRef<HTMLImageElement>(null);
  const [videoBounds, setVideoBounds] = useState<{
    width: number;
    height: number;
    offsetX: number;
    offsetY: number;
  }>({ width: 0, height: 0, offsetX: 0, offsetY: 0 });

  const updateVideoBounds = useCallback(() => {
    if (!viewportRef.current || !videoImgRef.current) return;
    const container = viewportRef.current.getBoundingClientRect();
    const img = videoImgRef.current;
    const nw = img.naturalWidth || 1280;
    const nh = img.naturalHeight || 720;
    if (container.width === 0 || container.height === 0) return;

    const containerAspect = container.width / container.height;
    const videoAspect = nw / (nh || 1);

    let renderW = container.width;
    let renderH = container.height;
    let offX = 0;
    let offY = 0;

    if (containerAspect > videoAspect) {
      renderH = container.height;
      renderW = renderH * videoAspect;
      offX = (container.width - renderW) / 2;
    } else {
      renderW = container.width;
      renderH = renderW / videoAspect;
      offY = (container.height - renderH) / 2;
    }

    setVideoBounds({
      width: renderW,
      height: renderH,
      offsetX: offX,
      offsetY: offY,
    });
  }, []);

  useEffect(() => {
    updateVideoBounds();
    window.addEventListener('resize', updateVideoBounds);
    return () => window.removeEventListener('resize', updateVideoBounds);
  }, [updateVideoBounds]);

  useEffect(() => {
    if (selectedCameraId && selectedCameraId !== activeCamId) {
      setActiveCamId(selectedCameraId);
      setHasStreamError(false);
    }
  }, [selectedCameraId]);

  const activeCamera =
    cameras.find((c) => c.camera_id === activeCamId) ||
    cameras[0] || {
      camera_id: 'camera_01',
      name: 'Default Camera',
      zone_id: 'production_floor',
      state: 'CONFIGURED',
      status: 'STANDBY',
      is_streaming: false,
      metrics: {
        fps: 0,
        inference_latency_ms: 0,
        active_workers: workers.length,
      },
    };

  const cameraState = activeCamera.state;
  const isConnecting = cameraState === 'CONNECTING' || cameraState === 'RECONNECTING' || isReconnecting;
  const isCameraOnline =
    !isConnecting &&
    (activeCamera.is_streaming === true ||
      activeCamera.state === 'STREAMING' ||
      activeCamera.status === 'streaming' ||
      ((activeCamera.state === 'CONNECTED' || activeCamera.status === 'ACTIVE') &&
        (activeCamera.last_frame_age_ms == null || activeCamera.last_frame_age_ms < 3000)));

  const isStale =
    !isConnecting &&
    activeCamera.last_frame_age_ms != null &&
    activeCamera.last_frame_age_ms > 3000;

  const isDegraded =
    activeCamera.state === 'DEGRADED' ||
    (!isStale && activeCamera.last_frame_age_ms != null && activeCamera.last_frame_age_ms > 2000);

  const isOffline =
    cameraState === 'OFFLINE' ||
    cameraState === 'ERROR' ||
    (!isCameraOnline && !isConnecting);

  // Toggle fullscreen
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

  // Helper for PPE icon & color
  const renderPPEItem = (label: string, status?: PPEPresence) => {
    if (status === 'PRESENT') {
      return (
        <div className="flex items-center justify-between gap-2">
          <span>{label}:</span>
          <span className="text-emerald-400 font-bold flex items-center gap-0.5">
            <Check className="w-2.5 h-2.5" /> Present
          </span>
        </div>
      );
    }
    if (status === 'ABSENT') {
      return (
        <div className="flex items-center justify-between gap-2">
          <span>{label}:</span>
          <span className="text-rose-400 font-bold flex items-center gap-0.5">
            <X className="w-2.5 h-2.5" /> Absent
          </span>
        </div>
      );
    }
    return (
      <div className="flex items-center justify-between gap-2 text-slate-400">
        <span>{label}:</span>
        <span className="font-medium flex items-center gap-0.5">
          <Minus className="w-2.5 h-2.5" /> Unknown
        </span>
      </div>
    );
  };

  const streamUrl =
    streamType === 'mjpeg' && !isPaused
      ? `${API_BASE_URL}/api/cameras/${activeCamId}/stream`
      : `${API_BASE_URL}/api/cameras/${activeCamId}/snapshot?t=${snapshotTimestamp}`;

  return (
    <div
      ref={containerRef}
      className="bg-[#0c1a2e] rounded-xl border border-slate-700 shadow-xl overflow-hidden flex flex-col"
    >
      {/* Feed Header — Dark Industrial SOC Style */}
      <div className="px-4 py-2.5 border-b border-slate-700/80 flex items-center justify-between bg-[#111f35]">
        <div className="flex items-center gap-3">
          <span
            className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
              isCameraOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
            }`}
          />
          <div>
            <span className="font-bold text-white text-xs tracking-tight">
              {activeCamera.name || 'Live Camera Feed'}
            </span>
            {activeCamera.zone_id && (
              <span className="ml-2 text-[9px] font-semibold text-sky-300 bg-sky-900/50 border border-sky-700/50 px-1.5 py-0.5 rounded-full uppercase tracking-wide">
                {activeCamera.zone_id.replace(/_/g, ' ')}
              </span>
            )}
          </div>

          {/* Camera Selector Dropdown */}
          <div className="relative">
            <select
              value={activeCamId}
              onChange={(e) => {
                const newId = e.target.value;
                setActiveCamId(newId);
                onSelectCamera?.(newId);
                setHasStreamError(false);
              }}
              className="text-xs bg-slate-800 border border-slate-600 text-slate-300 rounded-md py-1 pl-2.5 pr-7 font-medium focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
            >
              {cameras.length > 0 ? (
                cameras.map((c) => (
                  <option key={c.camera_id} value={c.camera_id}>
                    {c.camera_id.toUpperCase().replace('_', '-')} — {c.name}
                  </option>
                ))
              ) : (
                <option value="camera_01">CAM-01 — Production Floor South</option>
              )}
            </select>
          </div>
        </div>

        {/* Status & Controls */}
        <div className="flex items-center gap-2">
          {isCameraOnline && !isDegraded && !isStale ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500 text-white tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" /> LIVE
            </span>
          ) : isConnecting ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-600 text-white tracking-wide">
              <RefreshCw className="w-2.5 h-2.5 animate-spin" /> CONNECTING
            </span>
          ) : isStale ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-black tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-black animate-ping" /> STALE
            </span>
          ) : isDegraded ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-black tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-black animate-ping" /> DEGRADED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-600 text-white tracking-wide">
              OFFLINE
            </span>
          )}

          {/* Pause / Resume */}
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-700 transition"
            title={isPaused ? 'Resume Stream' : 'Pause Stream'}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
          </button>

          {/* Manual Snapshot Trigger */}
          <button
            onClick={() => setSnapshotTimestamp(Date.now())}
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-700 transition"
            title="Refresh Frame"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-700 transition"
            title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* Feed Viewport */}
      <div ref={viewportRef} className="relative bg-slate-950 aspect-[16/9] w-full overflow-hidden select-none group flex items-center justify-center">
        {hasStreamError || !isCameraOnline || isStale ? (
          <div className="flex flex-col items-center justify-center text-slate-400 p-6 text-center">
            {isConnecting ? (
              <RefreshCw className="w-10 h-10 text-sky-400 mb-2 animate-spin" />
            ) : isStale ? (
              <AlertTriangle className="w-10 h-10 text-amber-500 mb-2" />
            ) : (
              <AlertTriangle className="w-10 h-10 text-rose-500 mb-2" />
            )}
            <h4 className="text-sm font-bold text-white mb-0.5">
              {isConnecting
                ? 'Connecting to Camera Feed...'
                : isStale
                ? 'Stale Camera Stream'
                : isOffline
                ? `Camera ${activeCamId.toUpperCase()} Offline`
                : 'Camera Signal Standby'}
            </h4>
            <p className="text-xs text-slate-400 max-w-sm">
              {activeCamera.last_error ||
                activeCamera.metrics?.last_error ||
                (isConnecting
                  ? 'Initiating hardware capture handshake and frame acquisition loop...'
                  : isStale
                  ? `No new video frame received in ${(activeCamera.last_frame_age_ms! / 1000).toFixed(1)}s.`
                  : isOffline
                  ? `Cannot reach source (${activeCamera.safe_source || activeCamera.source || 'endpoint offline'}). Click below to retry connection.`
                  : 'Waiting for video frame data from hardware device. Ensure webcam or RTSP feed is operational.')}
            </p>
            <button
              onClick={async () => {
                setIsReconnecting(true);
                setHasStreamError(false);
                try {
                  await reconnectCamera(activeCamId);
                } catch (err) {
                  console.warn('Manual reconnect failed:', err);
                } finally {
                  setIsReconnecting(false);
                  setSnapshotTimestamp(Date.now());
                  onRefresh?.();
                }
              }}
              disabled={isReconnecting}
              className="mt-3 px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${isReconnecting ? 'animate-spin' : ''}`} />
              {isReconnecting ? 'Reconnecting Hardware...' : 'Retry Stream Connection'}
            </button>
          </div>
        ) : (
          <img
            ref={videoImgRef}
            alt={activeCamera.name}
            src={streamUrl}
            onLoad={updateVideoBounds}
            onError={() => {
              if (streamType === 'mjpeg') {
                // Fallback to snapshot polling
                setStreamType('snapshot');
              } else {
                setHasStreamError(true);
              }
            }}
            className="w-full h-full object-contain bg-black"
          />
        )}

        {/* Date-Time Stamp Top Right */}
        <div className="absolute top-2.5 right-3 bg-black/70 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] text-white font-mono-nums border border-white/10">
          {new Date().toISOString().replace('T', ' ').substring(0, 19)}
        </div>

        {/* Dynamic Worker Inspection HUD Overlays */}
        {isCameraOnline &&
          workers.map((worker) => {
            if (!worker.bbox || worker.bbox.length < 4) return null;
            const [x1, y1, x2, y2] = worker.bbox;
            const nw = videoImgRef.current?.naturalWidth || 1280;
            const nh = videoImgRef.current?.naturalHeight || 720;

            let nx1 = worker.normalized_bbox ? worker.normalized_bbox[0] : (x1 > 1 ? x1 / nw : x1);
            let ny1 = worker.normalized_bbox ? worker.normalized_bbox[1] : (y1 > 1 ? y1 / nh : y1);
            let nx2 = worker.normalized_bbox ? worker.normalized_bbox[2] : (x2 > 1 ? x2 / nw : x2);
            let ny2 = worker.normalized_bbox ? worker.normalized_bbox[3] : (y2 > 1 ? y2 / nh : y2);

            nx1 = Math.max(0, Math.min(1, nx1));
            ny1 = Math.max(0, Math.min(1, ny1));
            nx2 = Math.max(nx1 + 0.02, Math.min(1, nx2));
            ny2 = Math.max(ny1 + 0.03, Math.min(1, ny2));

            const hasBounds = videoBounds.width > 0 && videoBounds.height > 0;
            const leftPx = hasBounds ? videoBounds.offsetX + nx1 * videoBounds.width : nx1 * 100;
            const topPx = hasBounds ? videoBounds.offsetY + ny1 * videoBounds.height : ny1 * 100;
            const widthPx = hasBounds ? (nx2 - nx1) * videoBounds.width : (nx2 - nx1) * 100;
            const heightPx = hasBounds ? (ny2 - ny1) * videoBounds.height : (ny2 - ny1) * 100;

            // Color from the FINAL validated worker state (never raw detections).
            // UNKNOWN ≠ VIOLATION: amber, not red.
            const display = resolveWorkerDisplay(worker);
            const stateColor = display.color;

            return (
              <div
                key={worker.track_id}
                className="absolute pointer-events-none transition-all duration-150"
                style={{
                  left: hasBounds ? `${leftPx}px` : `${leftPx}%`,
                  top: hasBounds ? `${topPx}px` : `${topPx}%`,
                  width: hasBounds ? `${widthPx}px` : `${widthPx}%`,
                  height: hasBounds ? `${heightPx}px` : `${heightPx}%`,
                }}
                data-worker-state={display.state}
              >
                <div
                  className={`w-full h-full ${display.state === 'VIOLATION' ? 'border-[3px]' : 'border-2'} relative shadow-sm`}
                  style={{ borderColor: stateColor }}
                >
                  {/* Worker ID Tag — Shortened minimal format [Camera Initial]-[W][Worker_Number] + status */}
                  <div
                    className="absolute -top-4 left-0 text-white text-[8px] font-bold px-1 rounded-t whitespace-nowrap"
                    style={{ backgroundColor: stateColor }}
                  >
                    {getCameraShortTag(activeCamera)}-W{worker.track_id} · {display.label}
                  </div>

                  {/* Itemized PPE Inspection Box */}
                  <div
                    className="absolute top-0 -right-28 bg-black/85 backdrop-blur-sm border text-white text-[8px] rounded px-1.5 py-1 whitespace-nowrap leading-tight space-y-0.5 shadow-md"
                    style={{ borderColor: stateColor }}
                  >
                    {renderPPEItem('Helmet', worker.ppe_status?.helmet)}
                    {renderPPEItem('Vest', worker.ppe_status?.safety_vest)}
                    {renderPPEItem('Gloves', worker.ppe_status?.gloves)}
                    {renderPPEItem('Shoes', worker.ppe_status?.safety_footwear)}
                    {display.detail && (
                      <div className="pt-0.5 font-bold" style={{ color: stateColor }}>
                        {display.detail}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

        {/* Dynamic Environmental Hazard HUD Overlays (Fire & Smoke) — Only confirmed/active hazards */}
        {isCameraOnline &&
          hazards
            .filter((h) => {
              const st = (h.state || '').toUpperCase();
              return st === 'CONFIRMED' || st === 'ACTIVE' || (!st && (h.confidence || 0) >= 0.35);
            })
            .map((hazard, idx) => {
            if (!hazard.bbox || hazard.bbox.length < 4) return null;
            const [x1, y1, x2, y2] = hazard.bbox;
            const nw = videoImgRef.current?.naturalWidth || 1280;
            const nh = videoImgRef.current?.naturalHeight || 720;

            let nx1 = hazard.normalized_bbox ? hazard.normalized_bbox[0] : (x1 > 1 ? x1 / nw : x1);
            let ny1 = hazard.normalized_bbox ? hazard.normalized_bbox[1] : (y1 > 1 ? y1 / nh : y1);
            let nx2 = hazard.normalized_bbox ? hazard.normalized_bbox[2] : (x2 > 1 ? x2 / nw : x2);
            let ny2 = hazard.normalized_bbox ? hazard.normalized_bbox[3] : (y2 > 1 ? y2 / nh : y2);

            nx1 = Math.max(0, Math.min(1, nx1));
            ny1 = Math.max(0, Math.min(1, ny1));
            nx2 = Math.max(nx1 + 0.02, Math.min(1, nx2));
            ny2 = Math.max(ny1 + 0.02, Math.min(1, ny2));

            const hasBounds = videoBounds.width > 0 && videoBounds.height > 0;
            const leftPx = hasBounds ? videoBounds.offsetX + nx1 * videoBounds.width : nx1 * 100;
            const topPx = hasBounds ? videoBounds.offsetY + ny1 * videoBounds.height : ny1 * 100;
            const widthPx = hasBounds ? (nx2 - nx1) * videoBounds.width : (nx2 - nx1) * 100;
            const heightPx = hasBounds ? (ny2 - ny1) * videoBounds.height : (ny2 - ny1) * 100;

            const isFire = hazard.hazard_type.toLowerCase() === 'fire';
            const borderColor = isFire ? 'border-red-500 shadow-[0_0_12px_rgba(239,68,68,0.5)]' : 'border-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.5)]';
            const badgeBg = isFire ? 'bg-red-600' : 'bg-amber-600';
            const confPct = Math.round((hazard.confidence || 0) * 100);

            return (
              <div
                key={hazard.event_id || hazard.hazard_id || `hazard-${idx}`}
                className="absolute pointer-events-none transition-all duration-150 animate-pulse"
                style={{
                  left: hasBounds ? `${leftPx}px` : `${leftPx}%`,
                  top: hasBounds ? `${topPx}px` : `${topPx}%`,
                  width: hasBounds ? `${widthPx}px` : `${widthPx}%`,
                  height: hasBounds ? `${heightPx}px` : `${heightPx}%`,
                }}
              >
                <div className={`w-full h-full border-2 ${borderColor} relative`}>
                  <div
                    className={`absolute -top-5 left-0 ${badgeBg} text-white text-[9px] font-extrabold px-1.5 py-0.5 rounded-t flex items-center gap-1 uppercase tracking-wider whitespace-nowrap shadow-md`}
                  >
                    <Flame className="w-3 h-3 inline animate-bounce" />
                    {isFire ? 'FIRE HAZARD' : 'SMOKE HAZARD'} ({confPct}%)
                  </div>
                </div>
              </div>
            );
          })}

        {/* Bottom Stream Telemetry Strip */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/85 via-black/50 to-transparent p-2.5 flex items-center justify-between text-white text-[10px]">
          <div className="flex items-center gap-3 font-mono-nums">
            <span>
              FPS:{' '}
              <strong className={activeCamera.metrics?.fps && activeCamera.metrics.fps > 0 ? 'text-slate-200' : 'text-slate-400'}>
                {activeCamera.metrics?.fps != null ? activeCamera.metrics.fps.toFixed(1) : '0.0'}
              </strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Inference:{' '}
              <strong className={activeCamera.metrics?.inference_latency_ms ? 'text-slate-200' : 'text-slate-400'}>
                {activeCamera.metrics?.inference_latency_ms != null && activeCamera.metrics.inference_latency_ms > 0
                  ? `${activeCamera.metrics.inference_latency_ms.toFixed(0)} ms`
                  : 'N/A'}
              </strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Resolution: <strong className="text-slate-200">{activeCamera.resolution || '1280 × 720'}</strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Workers:{' '}
              <strong className="text-emerald-400">
                {workers.length > 0 ? workers.length : activeCamera.metrics?.active_workers ?? 0}
              </strong>
            </span>
            {activeCamera.last_frame_age_ms != null && (
              <>
                <span className="text-slate-500">|</span>
                <span>
                  Age:{' '}
                  <strong className={activeCamera.last_frame_age_ms > 2000 ? 'text-amber-400' : 'text-slate-400'}>
                    {activeCamera.last_frame_age_ms}ms
                  </strong>
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-[9px]">
              Zone: <span className="text-sky-300 font-medium">{activeCamera.zone_id}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraFeedPlayer;
