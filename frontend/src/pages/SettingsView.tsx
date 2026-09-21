/**
 * SettingsView.tsx — RAKSHYA VISION Phase 8
 * Read-only inspection of active AI models, tracking heuristics, hazard thresholds, and alert policies.
 */

import React from 'react';
import { Sliders, Cpu, ShieldCheck, Flame, Bell } from 'lucide-react';

interface SettingsViewProps {
  complianceConfig: any;
  hazardConfig: any;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ complianceConfig, hazardConfig }) => {
  return (
    <div className="settings-view-container">
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Sliders size={22} /> System Configuration & AI Telemetry
          </h2>
          <p className="view-subheading">
            Active neural network hyperparameters, tracking heuristics, and deterministic risk policies
          </p>
        </div>
      </div>

      <div className="settings-cards-grid">
        {/* Model Architecture & Weights */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Cpu size={18} className="text-accent" />
            <h4 className="settings-card-title">AI Detection Engine (Phase 3.1 V2)</h4>
          </div>
          <div className="settings-props-list">
            <div className="prop-row">
              <span className="prop-name">Base Architecture:</span>
              <span className="prop-val font-mono">Ultralytics YOLOv8n</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Active Checkpoint:</span>
              <span className="prop-val font-mono text-xs">ppe_fire_smoke_v2/weights/best.pt</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Execution Device:</span>
              <span className="prop-val font-mono">CPU / Auto-selected</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Canonical Classes (0–6):</span>
              <span className="prop-val font-mono text-xs">
                person, helmet, safety_vest, gloves, safety_footwear, fire, smoke
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Inference Latency:</span>
              <span className="prop-val font-mono">~32.89 ms / frame</span>
            </div>
          </div>
        </div>

        {/* Worker Tracking & Spatial Association */}
        <div className="settings-card">
          <div className="settings-card-header">
            <ShieldCheck size={18} className="text-success" />
            <h4 className="settings-card-title">Worker Tracking & PPE Heuristics (Phase 5)</h4>
          </div>
          <div className="settings-props-list">
            <div className="prop-row">
              <span className="prop-name">Tracking Algorithm:</span>
              <span className="prop-val font-mono">ByteTrack (Kalman + Hungarian)</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">PPE Spatial Association:</span>
              <span className="prop-val font-mono">Anatomical Hungarian Matching</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Confirmation Frames (N_confirm):</span>
              <span className="prop-val font-mono">
                {complianceConfig?.temporal?.confirmation_frames_needed ?? 3} frames
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Missing Tolerance (N_missing):</span>
              <span className="prop-val font-mono">
                {complianceConfig?.temporal?.missing_tolerance_before_absent ?? 5} frames
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Occlusion Policy:</span>
              <span className="prop-val font-mono text-warning">
                UNKNOWN (Never triggers violation)
              </span>
            </div>
          </div>
        </div>

        {/* Fire & Smoke Hazard Analysis */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Flame size={18} className="text-fire" />
            <h4 className="settings-card-title">Fire & Smoke Analysis (Phase 6)</h4>
          </div>
          <div className="settings-props-list">
            <div className="prop-row">
              <span className="prop-name">Fire Detection Threshold:</span>
              <span className="prop-val font-mono">
                {hazardConfig?.thresholds?.fire_confidence_threshold ?? 0.35}
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Smoke Detection Threshold:</span>
              <span className="prop-val font-mono">
                {hazardConfig?.thresholds?.smoke_confidence_threshold ?? 0.30}
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Confirmation Temporal Frames:</span>
              <span className="prop-val font-mono">
                {hazardConfig?.thresholds?.temporal_confirmation_frames ?? 5} frames
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Clearing Frame Count:</span>
              <span className="prop-val font-mono">
                {hazardConfig?.thresholds?.temporal_clear_frames ?? 10} frames
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Spatial Geofencing:</span>
              <span className="prop-val font-mono">Point-in-Polygon Ray Casting</span>
            </div>
          </div>
        </div>

        {/* Risk & Smart Alert Policy */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Bell size={18} className="text-error" />
            <h4 className="settings-card-title">Risk Engine & Smart Alert Policy (Phase 7)</h4>
          </div>
          <div className="settings-props-list">
            <div className="prop-row">
              <span className="prop-name">Score Mapping:</span>
              <span className="prop-val font-mono text-xs">
                0-29: LOW, 30-59: MEDIUM, 60-84: HIGH, 85-100: CRITICAL
              </span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Helmet / Vest Cooldown:</span>
              <span className="prop-val font-mono">60 seconds</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Fire Alert Cooldown:</span>
              <span className="prop-val font-mono">30 seconds</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Smoke Alert Cooldown:</span>
              <span className="prop-val font-mono">45 seconds</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Severity Escalation Window:</span>
              <span className="prop-val font-mono">300 seconds (5 min)</span>
            </div>
            <div className="prop-row">
              <span className="prop-name">Event Dispatcher:</span>
              <span className="prop-val font-mono text-accent">In-Memory EventBroadcaster + WebSocket</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
