/**
 * CameraFeedPlayer.tsx — RAKSHYA VISION Professional SOC
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
} from 'lucide-react';
import { CameraConfig, WorkerTrack, PPEPresence } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface CameraFeedPlayerProps {
  cameras: CameraConfig[];
  selectedCameraId?: string;
  onSelectCamera?: (cameraId: string) => void;
  workers?: WorkerTrack[];
  onRefresh?: () => void;
}

export const CameraFeedPlayer: React.FC<CameraFeedPlayerProps> = ({
  cameras,
  selectedCameraId,
  onSelectCamera,
  workers = [],
  onRefresh,
}) => {
  const [activeCamId, setActiveCamId] = useState<string>(
    selectedCameraId || (cameras[0]?.camera_id ?? 'camera_01')
  );
  const [isPaused, setIsPaused] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hasStreamError, setHasStreamError] = useState(false);
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
      state: 'ACTIVE',
      status: 'ACTIVE',
      metrics: {
        fps: 18.4,
        inference_latency_ms: 82,
        active_workers: workers.length,
      },
    };

  const isCameraOnline =
    activeCamera.state === 'CONNECTED' ||
    activeCamera.state === 'DEGRADED' ||
    activeCamera.status === 'ACTIVE';

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
      className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col"
    >
      {/* Feed Header */}
      <div className="px-4 py-2.5 border-b border-slate-200 flex items-center justify-between bg-white">
        <div className="flex items-center gap-3">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isCameraOnline ? 'bg-sky-500' : 'bg-rose-500'
            }`}
          />
          <span className="font-bold text-slate-800 text-xs tracking-tight">Live Camera Feed</span>

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
              className="text-xs bg-slate-50 border border-slate-200 rounded-md py-1 pl-2.5 pr-7 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
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
          {isCameraOnline ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500 text-white tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" /> LIVE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-500 text-white tracking-wide">
              STANDBY
            </span>
          )}

          {/* Pause / Resume */}
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100 transition"
            title={isPaused ? 'Resume Stream' : 'Pause Stream'}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
          </button>

          {/* Manual Snapshot Trigger */}
          <button
            onClick={() => setSnapshotTimestamp(Date.now())}
            className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100 transition"
            title="Refresh Frame"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100 transition"
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
        {hasStreamError || !isCameraOnline ? (
          <div className="flex flex-col items-center justify-center text-slate-400 p-6 text-center">
            <AlertTriangle className="w-10 h-10 text-amber-500 mb-2" />
            <h4 className="text-sm font-bold text-white mb-0.5">Camera Signal Standby</h4>
            <p className="text-xs text-slate-400 max-w-sm">
              {activeCamera.metrics?.last_error ||
                'Waiting for video frame data from hardware device. Ensure webcam or RTSP feed is operational.'}
            </p>
            <button
              onClick={() => {
                setHasStreamError(false);
                setStreamType(streamType === 'mjpeg' ? 'snapshot' : 'mjpeg');
                setSnapshotTimestamp(Date.now());
                onRefresh?.();
              }}
              className="mt-3 px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3 h-3" /> Retry Stream Connection
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

            const isCompliant = worker.overall_compliant;
            const borderColor = isCompliant ? 'border-emerald-500' : 'border-rose-500';
            const badgeBg = isCompliant ? 'bg-emerald-600' : 'bg-rose-600';

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
              >
                <div className={`w-full h-full border-2 ${borderColor} relative shadow-sm`}>
                  {/* Worker ID Tag */}
                  <div
                    className={`absolute -top-4 left-0 ${badgeBg} text-white text-[8px] font-bold px-1 rounded-t whitespace-nowrap`}
                  >
                    Worker #{worker.track_id}
                  </div>

                  {/* Itemized PPE Inspection Box */}
                  <div
                    className={`absolute top-0 -right-28 bg-black/85 backdrop-blur-sm border ${borderColor} text-white text-[8px] rounded px-1.5 py-1 whitespace-nowrap leading-tight space-y-0.5 shadow-md`}
                  >
                    {renderPPEItem('Helmet', worker.ppe_status?.helmet)}
                    {renderPPEItem('Vest', worker.ppe_status?.safety_vest)}
                    {renderPPEItem('Gloves', worker.ppe_status?.gloves)}
                    {renderPPEItem('Shoes', worker.ppe_status?.safety_footwear)}
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
              <strong className="text-slate-200">
                {activeCamera.metrics?.fps?.toFixed(1) ?? '18.4'}
              </strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Inference:{' '}
              <strong className="text-slate-200">
                {activeCamera.metrics?.inference_latency_ms?.toFixed(0) ?? '82'} ms
              </strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Resolution: <strong className="text-slate-200">1280 × 720</strong>
            </span>
            <span className="text-slate-500">|</span>
            <span>
              Workers:{' '}
              <strong className="text-emerald-400">
                {workers.length > 0 ? workers.length : activeCamera.metrics?.active_workers ?? 0}
              </strong>
            </span>
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
