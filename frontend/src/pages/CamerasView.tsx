/**
 * CamerasView.tsx — RAKSHYA VISION Phase 8
 * Live Camera & Optical Feeds Management with real-time zone boundary inspection and test analyzer.
 */

import React, { useState } from 'react';
import {
  Video,
  Camera,
  MapPin,
  Activity,
  Upload,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface CamerasViewProps {
  cameras: CameraConfig[];
  hazardConfig: any;
}

export const CamerasView: React.FC<CamerasViewProps> = ({ cameras, hazardConfig }) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    cameras[0]?.camera_id || 'CAM-01'
  );
  const [testResultImage, setTestResultImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisSummary, setAnalysisSummary] = useState<string | null>(null);

  const defaultCameras: CameraConfig[] = [
    { camera_id: 'CAM-01', name: 'Fabrication Bay', zone_id: 'FAB_BAY_01', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
    { camera_id: 'CAM-02', name: 'Paint & Coating Area', zone_id: 'PAINT_COAT_02', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
    { camera_id: 'CAM-03', name: 'Chemical Storage', zone_id: 'CHEM_STORE_03', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
    { camera_id: 'CAM-04', name: 'Assembly Line B', zone_id: 'ASSEMBLY_B_04', status: 'ACTIVE', resolution: '1280x720', fps: 30 },
  ];

  const activeCameras = cameras.length > 0 ? cameras : defaultCameras;
  const currentCamera = activeCameras.find((c) => c.camera_id === selectedCameraId) || activeCameras[0];

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

  return (
    <div className="cameras-view-container">
      {/* Camera Grid Header */}
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Video size={22} /> Optical Surveillance & Stream Feeds
          </h2>
          <p className="view-subheading">
            Continuous 24/7 AI-supervised computer vision feeds across industrial zones
          </p>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="cameras-layout-grid">
        {/* Left: Camera List & Feeds */}
        <div className="camera-list-column">
          <div className="camera-cards-grid">
            {activeCameras.map((cam) => {
              const isSelected = cam.camera_id === currentCamera.camera_id;
              return (
                <div
                  key={cam.camera_id}
                  className={`camera-feed-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedCameraId(cam.camera_id)}
                >
                  <div className="feed-header">
                    <div className="feed-title-row">
                      <span className="font-mono font-bold">{cam.camera_id}</span>
                      <span className="badge badge-success text-xs">ACTIVE</span>
                    </div>
                    <span className="feed-name">{cam.name}</span>
                  </div>

                  <div className="feed-screen">
                    <div className="feed-crosshair">
                      <Camera size={32} className="text-accent" />
                      <span className="feed-resolution">{cam.resolution} @ {cam.fps} FPS</span>
                    </div>
                    <div className="feed-zone-pill">
                      <MapPin size={12} /> {cam.zone_id}
                    </div>
                  </div>

                  <div className="feed-footer">
                    <span className="feed-stream-type">RTSP Stream (Direct H.264)</span>
                    <button className="btn-select-cam">
                      {isSelected ? 'Inspecting' : 'Select'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Camera Inspector & Live Frame Analyzer */}
        <div className="camera-inspector-column">
          <div className="inspector-card">
            <div className="inspector-header">
              <div className="inspector-title-group">
                <Layers size={18} />
                <h3 className="inspector-title">Feed Inspector: {currentCamera.camera_id}</h3>
              </div>
              <span className="badge badge-info">{currentCamera.zone_id}</span>
            </div>

            {/* Live / Annotated Screen */}
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
              ) : (
                <div className="screen-placeholder">
                  <Video size={48} className="text-muted" />
                  <h4>Stream Standby</h4>
                  <p>Awaiting video frame packet or image test upload.</p>
                </div>
              )}
            </div>

            {/* Analysis Summary */}
            {analysisSummary && (
              <div className="analysis-summary-banner">
                <Activity size={16} />
                <span>{analysisSummary}</span>
              </div>
            )}

            {/* Test Frame Upload Controls */}
            <div className="inspector-controls">
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

              {testResultImage && (
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setTestResultImage(null);
                    setAnalysisSummary(null);
                  }}
                >
                  Reset Stream
                </button>
              )}
            </div>

            {/* Zone Telemetry */}
            <div className="inspector-meta-section">
              <h4 className="meta-heading">Zone Configuration</h4>
              <div className="meta-props-table">
                <div className="meta-prop-row">
                  <span>Camera Identifier:</span>
                  <span className="font-mono">{currentCamera.camera_id}</span>
                </div>
                <div className="meta-prop-row">
                  <span>Assigned Zone:</span>
                  <span className="font-mono">{currentCamera.zone_id}</span>
                </div>
                <div className="meta-prop-row">
                  <span>Stream Protocol:</span>
                  <span className="font-mono">RTSP / TCP</span>
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
