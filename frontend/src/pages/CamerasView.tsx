/**
 * CamerasView.tsx — RAKSHYA VISION Phase 10 Step 6
 * Real Multi-Camera Management Dashboard with live operational metrics,
 * explicit camera worker lifecycle states, dynamic start/stop controls,
 * and live snapshot inspector.
 */

import React, { useState, useEffect } from 'react';
import {
  Video,
  Camera,
  MapPin,
  Activity,
  Upload,
  CheckCircle2,
  Layers,
  Play,
  Square,
  RefreshCw,
  Radio,
  AlertTriangle,
  Smartphone,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { API_BASE_URL } from '../utils/constants';
import { startCamera, stopCamera, fetchCameras } from '../services/api';

interface CamerasViewProps {
  cameras: CameraConfig[];
  hazardConfig: any;
  onRefreshCameras?: () => void;
}

export const CamerasView: React.FC<CamerasViewProps> = ({ cameras, hazardConfig, onRefreshCameras }) => {
  const [activeCameraList, setActiveCameraList] = useState<CameraConfig[]>(cameras);
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    cameras[0]?.camera_id || 'camera_01'
  );
  const [testResultImage, setTestResultImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisSummary, setAnalysisSummary] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState<boolean>(false);
  const [liveSnapshotUrl, setLiveSnapshotUrl] = useState<string | null>(null);

  // Synchronize when parent cameras update
  useEffect(() => {
    if (cameras.length > 0) {
      setActiveCameraList(cameras);
      if (!selectedCameraId || !cameras.some((c) => c.camera_id === selectedCameraId)) {
        setSelectedCameraId(cameras[0].camera_id);
      }
    }
  }, [cameras]);

  const currentCamera =
    activeCameraList.find((c) => c.camera_id === selectedCameraId) ||
    activeCameraList[0] || {
      camera_id: 'camera_01',
      name: 'Default Camera',
      zone_id: 'UNKNOWN',
      status: 'ACTIVE' as const,
      resolution: '1280x720',
      fps: 0,
    };

  // Poll live snapshot for selected camera if CONNECTED
  useEffect(() => {
    let interval: any = null;
    const fetchSnapshot = () => {
      if (currentCamera.state === 'CONNECTED' || currentCamera.status === 'ACTIVE') {
        setLiveSnapshotUrl(`${API_BASE_URL}/api/cameras/${currentCamera.camera_id}/snapshot?t=${Date.now()}`);
      } else {
        setLiveSnapshotUrl(null);
      }
    };

    fetchSnapshot();
    interval = setInterval(fetchSnapshot, 500);
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentCamera.camera_id, currentCamera.state, currentCamera.status]);

  const handleStart = async (camId: string) => {
    setActionInProgress(true);
    try {
      await startCamera(camId);
      const updated = await fetchCameras();
      if (Array.isArray(updated)) {
        setActiveCameraList(
          updated.map((c: any) => ({
            camera_id: c.camera_id,
            name: c.name,
            zone_id: c.zone_id,
            status: c.state === 'CONNECTED' ? 'ACTIVE' : c.state === 'DISABLED' ? 'STANDBY' : 'OFFLINE',
            state: c.state,
            source_type: c.source_type,
            enabled: c.enabled,
            resolution: '1280x720',
            fps: c.metrics?.fps || 0,
            safe_source: c.safe_source,
            metrics: c.metrics,
          }))
        );
      }
      if (onRefreshCameras) onRefreshCameras();
    } catch (err: any) {
      console.error('Failed to start camera:', err);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleStop = async (camId: string) => {
    setActionInProgress(true);
    try {
      await stopCamera(camId);
      const updated = await fetchCameras();
      if (Array.isArray(updated)) {
        setActiveCameraList(
          updated.map((c: any) => ({
            camera_id: c.camera_id,
            name: c.name,
            zone_id: c.zone_id,
            status: c.state === 'CONNECTED' ? 'ACTIVE' : c.state === 'DISABLED' ? 'STANDBY' : 'OFFLINE',
            state: c.state,
            source_type: c.source_type,
            enabled: c.enabled,
            resolution: '1280x720',
            fps: c.metrics?.fps || 0,
            safe_source: c.safe_source,
            metrics: c.metrics,
          }))
        );
      }
      if (onRefreshCameras) onRefreshCameras();
    } catch (err: any) {
      console.error('Failed to stop camera:', err);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAnalyzing(true);
    setAnalysisSummary(null);
    setTestResultImage(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('camera_id', currentCamera.camera_id);
    formData.append('zone_id', currentCamera.zone_id);

    try {
      const response = await fetch(`${API_BASE_URL}/api/compliance/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Inference returned HTTP ${response.status}`);
      }

      const data = await response.json();
      if (data.annotated_image_base64) {
        setTestResultImage(`data:image/jpeg;base64,${data.annotated_image_base64}`);
      }
      setAnalysisSummary(
        `Tracked ${data.summary?.total_workers || 0} worker(s). Compliant: ${
          data.summary?.compliant_workers || 0
        }, Non-Compliant: ${data.summary?.non_compliant_workers || 0}`
      );
    } catch (err: any) {
      setAnalysisSummary(`Analysis error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getBadgeClass = (state?: string) => {
    switch (state) {
      case 'CONNECTED':
        return 'badge-success';
      case 'CONNECTING':
      case 'RECONNECTING':
        return 'badge-warning';
      case 'ERROR':
        return 'badge-danger';
      case 'DISABLED':
      case 'DISCONNECTED':
      default:
        return 'badge-secondary';
    }
  };

  return (
    <div className="cameras-view-container">
      {/* Camera Grid Header */}
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Video size={22} /> Production Multi-Camera Surveillance Hub
          </h2>
          <p className="view-subheading">
            Real-time optical feeds with isolated worker threads, reconnect policies, and live telemetry
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn btn-secondary text-xs flex items-center gap-1"
            onClick={async () => {
              if (onRefreshCameras) onRefreshCameras();
              const updated = await fetchCameras();
              if (Array.isArray(updated)) {
                setActiveCameraList(
                  updated.map((c: any) => ({
                    camera_id: c.camera_id,
                    name: c.name,
                    zone_id: c.zone_id,
                    status: c.state === 'CONNECTED' ? 'ACTIVE' : c.state === 'DISABLED' ? 'STANDBY' : 'OFFLINE',
                    state: c.state,
                    source_type: c.source_type,
                    enabled: c.enabled,
                    resolution: '1280x720',
                    fps: c.metrics?.fps || 0,
                    safe_source: c.safe_source,
                    metrics: c.metrics,
                  }))
                );
              }
            }}
          >
            <RefreshCw size={14} /> Refresh Feeds
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="cameras-layout-grid">
        {/* Left: Real Multi-Camera Cards */}
        <div className="camera-list-column">
          <div className="camera-cards-grid">
            {activeCameraList.map((cam) => {
              const isSelected = cam.camera_id === currentCamera.camera_id;
              const displayState = cam.state || (cam.status === 'ACTIVE' ? 'CONNECTED' : 'DISCONNECTED');
              const isConnected = displayState === 'CONNECTED';

              return (
                <div
                  key={cam.camera_id}
                  className={`camera-feed-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedCameraId(cam.camera_id)}
                >
                  <div className="feed-header">
                    <div className="feed-title-row">
                      <span className="font-mono font-bold">{cam.camera_id}</span>
                      <span className={`badge ${getBadgeClass(displayState)} text-xs uppercase font-mono`}>
                        {displayState}
                      </span>
                    </div>
                    <span className="feed-name">{cam.name}</span>
                  </div>

                  <div className="feed-screen">
                    <div className="feed-crosshair">
                      <Camera size={28} className={isConnected ? 'text-success' : 'text-accent'} />
                      <span className="feed-resolution font-mono">
                        {cam.metrics?.fps ? `${cam.metrics.fps} FPS` : `${cam.fps} FPS Target`}
                      </span>
                    </div>
                    <div className="feed-zone-pill">
                      <MapPin size={12} /> {cam.zone_id}
                    </div>
                  </div>

                  <div className="feed-footer">
                    <div className="flex flex-col text-xs text-muted truncate max-w-[180px]">
                      <span className="font-mono">{cam.source_type?.toUpperCase() || 'RTSP'}</span>
                      <span className="truncate">{cam.safe_source || 'Managed Worker'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {displayState === 'CONNECTED' ? (
                        <button
                          className="btn btn-danger btn-xs"
                          title="Stop Camera Stream"
                          disabled={actionInProgress}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStop(cam.camera_id);
                          }}
                        >
                          <Square size={12} />
                        </button>
                      ) : (
                        <button
                          className="btn btn-primary btn-xs"
                          title="Start Camera Stream"
                          disabled={actionInProgress}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStart(cam.camera_id);
                          }}
                        >
                          <Play size={12} />
                        </button>
                      )}
                      <button className="btn-select-cam">
                        {isSelected ? 'Inspecting' : 'Select'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Camera Inspector & Live Telemetry */}
        <div className="camera-inspector-column">
          <div className="inspector-card">
            <div className="inspector-header">
              <div className="inspector-title-group">
                <Layers size={18} />
                <h3 className="inspector-title">Inspector: {currentCamera.camera_id}</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge ${getBadgeClass(currentCamera.state)} font-mono text-xs uppercase`}>
                  {currentCamera.state || currentCamera.status}
                </span>
                <span className="badge badge-info font-mono text-xs">{currentCamera.zone_id}</span>
              </div>
            </div>

            {/* Live Snapshot or Upload Screen */}
            <div className="inspector-display-screen">
              {testResultImage ? (
                <div className="annotated-image-wrap">
                  <img
                    src={testResultImage}
                    alt="Inference Detection Output"
                    className="annotated-result-img"
                  />
                  <div className="annotation-overlay-tag">
                    <CheckCircle2 size={14} className="text-success" /> Live Inference Completed
                  </div>
                </div>
              ) : liveSnapshotUrl && (currentCamera.state === 'CONNECTED' || currentCamera.status === 'ACTIVE') ? (
                <div className="annotated-image-wrap">
                  <img
                    src={liveSnapshotUrl}
                    alt={`Live feed from ${currentCamera.camera_id}`}
                    className="annotated-result-img"
                    onError={() => setLiveSnapshotUrl(null)}
                  />
                  <div className="annotation-overlay-tag">
                    <Radio size={14} className="text-success animate-pulse" /> Live Stream Worker Active
                  </div>
                </div>
              ) : (
                <div className="screen-placeholder">
                  <Video size={48} className="text-muted" />
                  <h4>Stream Inactive</h4>
                  <p className="text-xs text-muted">
                    {currentCamera.state === 'ERROR'
                      ? `Error: ${currentCamera.metrics?.last_error || 'Stream offline'}`
                      : 'Camera is disconnected or standby. Click Start or upload a test frame.'}
                  </p>
                </div>
              )}
            </div>

            {/* Camera Diagnostics Warning Banner */}
            {currentCamera.metrics?.last_error && (
              <div className="bg-amber-950/70 border border-amber-500/50 text-amber-200 text-xs p-3 rounded mt-2 flex items-start gap-2">
                <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <strong>Hardware / Stream Advisory:</strong> {currentCamera.metrics.last_error}
                </div>
              </div>
            )}

            {/* Analysis Summary */}
            {analysisSummary && (
              <div className="analysis-summary-banner">
                <Activity size={16} />
                <span>{analysisSummary}</span>
              </div>
            )}

            {/* Frame Controls & Diagnostics */}
            <div className="inspector-controls flex items-center justify-between">
              <label className="btn btn-primary file-upload-label">
                <Upload size={16} />
                <span>{isAnalyzing ? 'Running AI Inference...' : 'Upload Frame for AI Analysis'}</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileUpload}
                  disabled={isAnalyzing}
                  style={{ display: 'none' }}
                />
              </label>

              <div className="flex items-center gap-2">
                {currentCamera.state === 'CONNECTED' ? (
                  <button
                    className="btn btn-danger text-xs flex items-center gap-1"
                    disabled={actionInProgress}
                    onClick={() => handleStop(currentCamera.camera_id)}
                  >
                    <Square size={14} /> Stop Worker
                  </button>
                ) : (
                  <button
                    className="btn btn-success text-xs flex items-center gap-1"
                    disabled={actionInProgress}
                    onClick={() => handleStart(currentCamera.camera_id)}
                  >
                    <Play size={14} /> Start Worker
                  </button>
                )}

                {testResultImage && (
                  <button
                    className="btn btn-secondary text-xs"
                    onClick={() => {
                      setTestResultImage(null);
                      setAnalysisSummary(null);
                    }}
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>

            {/* Real Operational Telemetry Metrics */}
            <div className="inspector-meta-section">
              <h4 className="meta-heading">Operational Telemetry (Verified Backend Metrics)</h4>
              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div className="bg-[#1e222d] p-2 rounded border border-border flex justify-between items-center">
                  <span className="text-muted">Actual FPS:</span>
                  <span className="font-mono font-bold text-accent">
                    {currentCamera.metrics?.fps ?? 0} fps
                  </span>
                </div>
                <div className="bg-[#1e222d] p-2 rounded border border-border flex justify-between items-center">
                  <span className="text-muted">Total Frames:</span>
                  <span className="font-mono font-bold text-success">
                    {currentCamera.metrics?.frame_count ?? 0}
                  </span>
                </div>
                <div className="bg-[#1e222d] p-2 rounded border border-border flex justify-between items-center">
                  <span className="text-muted">Dropped Frames:</span>
                  <span className="font-mono font-bold text-warning">
                    {currentCamera.metrics?.dropped_frames ?? 0}
                  </span>
                </div>
                <div className="bg-[#1e222d] p-2 rounded border border-border flex justify-between items-center">
                  <span className="text-muted">Reconnect Count:</span>
                  <span className="font-mono font-bold text-info">
                    {currentCamera.metrics?.reconnect_count ?? 0}
                  </span>
                </div>
              </div>

              <h4 className="meta-heading">Configuration & Security</h4>
              <div className="meta-props-table">
                <div className="meta-prop-row">
                  <span>Camera ID:</span>
                  <span className="font-mono">{currentCamera.camera_id}</span>
                </div>
                <div className="meta-prop-row">
                  <span>Source URL (Masked):</span>
                  <span className="font-mono text-muted text-xs truncate max-w-[260px]">
                    {currentCamera.safe_source || 'Managed Locally'}
                  </span>
                </div>
                <div className="meta-prop-row">
                  <span>Assigned Zone:</span>
                  <span className="font-mono">{currentCamera.zone_id}</span>
                </div>
                <div className="meta-prop-row">
                  <span>Stream Protocol:</span>
                  <span className="font-mono uppercase">{currentCamera.source_type || 'RTSP'}</span>
                </div>
                <div className="meta-prop-row">
                  <span>Spatial ROI Polygon:</span>
                  <span className="font-mono text-xs text-muted">
                    {hazardConfig?.zones?.[currentCamera.zone_id]?.polygon
                      ? `[${hazardConfig.zones[currentCamera.zone_id].polygon.length} vertices]`
                      : 'Full Frame [0, 0, 1280, 720]'}
                  </span>
                </div>
              </div>

              {/* Android & External Camera Integration Guide */}
              <div className="mt-4 p-3 bg-[#171b26] rounded border border-border">
                <div className="flex items-center gap-2 mb-2 text-xs font-bold text-accent">
                  <Smartphone size={15} /> Android &amp; External Camera Setup Guide
                </div>
                <div className="text-xs text-muted space-y-1">
                  <p>
                    <strong className="text-foreground">Option 1 — Wi-Fi Network Stream (Recommended):</strong> Install <em>IP Webcam</em> or <em>DroidCam</em> on Android, start the server, and configure in <code>configs/cameras.yaml</code>:
                  </p>
                  <code className="block bg-black/40 p-1.5 rounded font-mono text-[11px] text-info">
                    source: "http://&lt;phone_ip&gt;:8080/video" | source_type: "http"
                  </code>
                  <p className="mt-2">
                    <strong className="text-foreground">Option 2 — USB Connection:</strong> Connect phone via USB and select <em>"Webcam" mode</em> (Android 14+) or use <em>DroidCam PC client</em> to expose DirectShow device index (e.g., <code>source: "1", source_type: "usb"</code>).
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
