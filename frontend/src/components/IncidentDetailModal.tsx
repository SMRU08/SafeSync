/**
 * IncidentDetailModal.tsx — RAKSHYA VISION Phase 8
 * Detailed view for parent safety incidents, showing factor breakdowns and linked alerts.
 */

import React, { useEffect, useState } from 'react';
import { X, ShieldAlert, AlertTriangle, Layers, Activity } from 'lucide-react';
import { Incident } from '../types';
import { fetchIncidentDetail } from '../services/api';

interface IncidentDetailModalProps {
  incident: Incident | null;
  onClose: () => void;
  onSelectAlert?: (alertId: string) => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  onClose,
  onSelectAlert,
}) => {
  const [fullIncident, setFullIncident] = useState<Incident | null>(incident);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (incident) {
      setFullIncident(incident);
      setLoading(true);
      fetchIncidentDetail(incident.incident_id)
        .then((data) => setFullIncident(data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [incident]);

  if (!incident || !fullIncident) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Layers size={22} className="modal-title-icon" />
            <div>
              <div className="modal-id-row">
                <span className="modal-id">{fullIncident.incident_id}</span>
                <span className={`badge severity-${fullIncident.risk_level.toLowerCase()}`}>
                  {fullIncident.risk_level} ({fullIncident.risk_score}/100)
                </span>
                <span className={`badge status-${fullIncident.status.toLowerCase()}`}>
                  {fullIncident.status}
                </span>
              </div>
              <h3 className="modal-title">Incident Analysis</h3>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Metadata */}
          <div className="modal-meta-grid">
            <div className="meta-item">
              <span className="meta-label">Camera</span>
              <span className="meta-value">{fullIncident.camera_id}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Zone</span>
              <span className="meta-value">{fullIncident.zone_id}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Created At</span>
              <span className="meta-value">
                {new Date(fullIncident.created_at).toLocaleString()}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Last Updated</span>
              <span className="meta-value">
                {new Date(fullIncident.updated_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Event Types */}
          <div className="modal-section">
            <h4 className="section-subtitle">
              <AlertTriangle size={16} /> Verified Safety Events
            </h4>
            <div className="event-badges-wrap">
              {fullIncident.event_types.map((et, i) => (
                <span key={i} className="event-badge">
                  {et}
                </span>
              ))}
            </div>
          </div>

          {/* Risk Factors Breakdown */}
          {fullIncident.factors && (
            <div className="modal-section">
              <h4 className="section-subtitle">
                <Activity size={16} /> Transparent Risk Factors Breakdown
              </h4>
              <div className="factors-card">
                <div className="factor-row">
                  <span>Base Severity:</span>
                  <span className="font-mono">{fullIncident.factors.base_severity ?? 'N/A'}</span>
                </div>
                <div className="factor-row">
                  <span>Persistence Weight:</span>
                  <span className="font-mono">+{fullIncident.factors.persistence_weight ?? 0}</span>
                </div>
                <div className="factor-row">
                  <span>Affected Workers:</span>
                  <span className="font-mono">{fullIncident.factors.affected_workers ?? 1}</span>
                </div>
                <div className="factor-row">
                  <span>Zone Multiplier:</span>
                  <span className="font-mono">{fullIncident.factors.zone_multiplier ?? 1.0}x</span>
                </div>
                <div className="factor-divider" />
                <div className="factor-row font-bold">
                  <span>Total Calculated Risk Score:</span>
                  <span className="font-mono text-accent">
                    {fullIncident.risk_score} / 100 ({fullIncident.risk_level})
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Linked Alerts */}
          <div className="modal-section">
            <h4 className="section-subtitle">
              <ShieldAlert size={16} /> Linked Alerts ({fullIncident.alerts?.length || 0})
            </h4>
            {loading ? (
              <p className="loading-text">Loading linked alerts...</p>
            ) : fullIncident.alerts && fullIncident.alerts.length > 0 ? (
              <div className="linked-alerts-list">
                {fullIncident.alerts.map((alt) => (
                  <div
                    key={alt.alert_id}
                    className="linked-alert-item"
                    onClick={() => {
                      if (onSelectAlert) onSelectAlert(alt.alert_id);
                    }}
                  >
                    <div className="linked-alert-left">
                      <span className={`badge severity-${alt.severity.toLowerCase()}`}>
                        {alt.severity}
                      </span>
                      <span className="linked-alert-title">{alt.title}</span>
                    </div>
                    <span className="linked-alert-time">
                      {new Date(alt.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No alerts currently linked to this incident.</p>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
