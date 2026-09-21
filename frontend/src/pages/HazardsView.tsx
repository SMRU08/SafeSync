/**
 * HazardsView.tsx — RAKSHYA VISION Phase 8
 * Fire & Smoke Hazard Analysis view with zone monitoring, spatial relationships, and frame testing.
 */

import React, { useState } from 'react';
import {
  Flame,
  ShieldCheck,
  ShieldAlert,
  Upload,
  Activity,
  CheckCircle2,
  Clock,
  MapPin,
} from 'lucide-react';
import { HazardEventDetail } from '../types';
import { HazardStatusPanel } from '../components/HazardStatusPanel';
import { API_BASE_URL } from '../utils/constants';

interface HazardsViewProps {
  hazards: HazardEventDetail[];
  hazardConfig?: any;
}

export const HazardsView: React.FC<HazardsViewProps> = ({ hazards, hazardConfig: _hazardConfig }) => {
  const [analyzedHazards, setAnalyzedHazards] = useState<HazardEventDetail[]>(hazards);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [sceneState, setSceneState] = useState<string | null>(null);
  const [relationship, setRelationship] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleHazardFrameUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAnalyzing(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('camera_id', 'CAM-01');
    formData.append('zone_id', 'FAB_BAY_01');

    try {
      const response = await fetch(`${API_BASE_URL}/api/hazards/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Inference returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setSceneState(data.scene_hazard_state);
      setRelationship(data.relationship);
      setAnalyzedHazards(data.hazards || []);
      if (data.annotated_image_base64) {
        setAnnotatedImage(`data:image/jpeg;base64,${data.annotated_image_base64}`);
      }
    } catch (err: any) {
      setErrorMsg(`Hazard analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const activeHazardsList = analyzedHazards.length > 0 ? analyzedHazards : hazards;

  return (
    <div className="hazards-view-container">
      {/* Title Bar */}
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Flame size={22} /> Fire & Smoke Hazard Analysis
          </h2>
          <p className="view-subheading">
            Decoupled thermal and smoke signature tracking with spatial ROI validation and multi-frame temporal confirmation
          </p>
        </div>

        <div>
          <label className="btn btn-primary file-upload-label">
            <Upload size={16} />
            <span>{isAnalyzing ? 'Analyzing Thermal/Smoke...' : 'Test Hazard Inference on Frame'}</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleHazardFrameUpload}
              disabled={isAnalyzing}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      {errorMsg && (
        <div className="banner-error mb-4">
          <ShieldAlert size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Real-Time Spatial Relationship Banner */}
      {relationship && (
        <div className="hazard-relation-banner mb-6">
          <div className="relation-tag">
            <Activity size={18} />
            <span>Scene Status: <strong>{sceneState}</strong></span>
          </div>
          <div className="relation-tag">
            <span>Spatial Interaction: <strong>{relationship}</strong></span>
          </div>
        </div>
      )}

      {/* Monitored Zones Grid */}
      <div className="mb-6">
        <h3 className="section-heading mb-3">
          <MapPin size={18} /> Continuous Zone Threat Level
        </h3>
        <HazardStatusPanel hazards={activeHazardsList} />
      </div>

      {/* Annotated Result */}
      {annotatedImage && (
        <div className="annotated-preview-box mb-6">
          <div className="annotated-preview-header">
            <span className="font-bold flex items-center gap-2">
              <CheckCircle2 size={16} className="text-success" />
              Thermal & Smoke Optical Annotation
            </span>
            <button className="btn-link" onClick={() => setAnnotatedImage(null)}>
              Dismiss Frame
            </button>
          </div>
          <img src={annotatedImage} alt="Annotated Hazards" className="annotated-img" />
        </div>
      )}

      {/* Hazard Tracker Events History Table */}
      <div className="soc-section">
        <h3 className="section-heading mb-3">
          <Clock size={18} /> Active Hazard Events
        </h3>

        {activeHazardsList.length === 0 ? (
          <div className="table-empty-state">
            <ShieldCheck size={36} className="empty-icon text-success" />
            <h4 className="empty-title">NO ACTIVE HAZARDS DETECTED</h4>
            <p className="empty-subtitle">
              All monitored industrial zones are verified clear of fire, heat, and smoke signatures.
            </p>
          </div>
        ) : (
          <div className="responsive-table-wrap">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Hazard ID</th>
                  <th>Type</th>
                  <th>Zone & Camera</th>
                  <th>Confirmation State</th>
                  <th>Confidence</th>
                  <th>Persistence</th>
                </tr>
              </thead>
              <tbody>
                {activeHazardsList.map((h, i) => (
                  <tr key={h.hazard_id || i} className="soc-row">
                    <td className="font-mono text-accent">{h.hazard_id}</td>
                    <td>
                      <span className={`badge ${h.hazard_type === 'fire' ? 'badge-error' : 'badge-warning'}`}>
                        {h.hazard_type.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div>{h.zone_id}</div>
                      <div className="text-xs text-muted">{h.camera_id}</div>
                    </td>
                    <td>
                      <span className={`badge ${h.state === 'CONFIRMED' ? 'badge-error' : 'badge-warning'}`}>
                        {h.state}
                      </span>
                    </td>
                    <td className="font-mono">{(h.confidence * 100).toFixed(1)}%</td>
                    <td className="font-mono">{h.persistence_frames || 1} frames</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
