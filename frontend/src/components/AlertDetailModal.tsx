/**
 * AlertDetailModal.tsx — RAKSHYA VISION Phase 8
 * Detailed audit view for a safety alert including lifecycle actions and history trail.
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  MapPin,
  Camera,
  History,
  Check,
  AlertOctagon,
  ShieldCheck,
  Download,
  Image as ImageIcon,
  Eye,
} from 'lucide-react';
import { Alert, EvidenceItem } from '../types';
import { fetchAlertDetail, fetchIncidentEvidence } from '../services/api';

interface AlertDetailModalProps {
  alert: Alert | null;
  onClose: () => void;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onSelectIncident?: (incidentId: string) => void;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
  onDismiss,
  onSelectIncident,
}) => {
  const [fullAlert, setFullAlert] = useState<Alert | null>(alert);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  useEffect(() => {
    if (alert) {
      setFullAlert(alert);
      setLoading(true);
      fetchAlertDetail(alert.alert_id)
        .then((data) => setFullAlert(data))
        .catch(() => {})
        .finally(() => setLoading(false));

      fetchIncidentEvidence(alert.incident_id)
        .then((items) => setEvidenceList(items || []))
        .catch(() => setEvidenceList([]));
    }
  }, [alert]);

  if (!alert || !fullAlert) return null;

  const handleAction = async (action: 'ack' | 'resolve' | 'dismiss') => {
    setActionInProgress(action);
    try {
      if (action === 'ack') await onAcknowledge(fullAlert.alert_id);
      if (action === 'resolve') await onResolve(fullAlert.alert_id);
      if (action === 'dismiss') await onDismiss(fullAlert.alert_id);
      // Re-fetch detail to refresh history
      const updated = await fetchAlertDetail(fullAlert.alert_id);
      setFullAlert(updated);
    } finally {
      setActionInProgress(null);
    }
  };

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'severity-critical';
      case 'HIGH':
        return 'severity-high';
      case 'MEDIUM':
        return 'severity-medium';
      default:
        return 'severity-low';
    }
  };

  const getStatusBadgeClass = (st: string) => {
    switch (st) {
      case 'ACTIVE':
        return 'status-active';
      case 'ACKNOWLEDGED':
        return 'status-ack';
      case 'RESOLVED':
        return 'status-resolved';
      case 'DISMISSED':
        return 'status-dismissed';
      default:
        return '';
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <ShieldAlert size={22} className="modal-title-icon" />
            <div>
              <div className="modal-id-row">
                <span className="modal-id">{fullAlert.alert_id}</span>
                <span className={`badge ${getSeverityBadgeClass(fullAlert.severity)}`}>
                  {fullAlert.severity}
                </span>
                <span className={`badge ${getStatusBadgeClass(fullAlert.status)}`}>
                  {fullAlert.status}
                </span>
              </div>
              <h3 className="modal-title">{fullAlert.title}</h3>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="modal-body">
          {/* Plain English Message Box */}
          <div className="alert-message-box">
            <p className="message-text">{fullAlert.message}</p>
          </div>

          {/* Metadata Grid */}
          <div className="modal-meta-grid">
            <div className="meta-item">
              <span className="meta-label">
                <Camera size={14} /> Camera
              </span>
              <span className="meta-value">{fullAlert.camera_id}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">
                <MapPin size={14} /> Monitored Zone
              </span>
              <span className="meta-value">{fullAlert.zone_id}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">
                <Clock size={14} /> Created At
              </span>
              <span className="meta-value">
                {new Date(fullAlert.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">
                <AlertTriangle size={14} /> Event Type
              </span>
              <span className="meta-value">{fullAlert.event_type}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Parent Incident</span>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                <span className="meta-value font-mono">{fullAlert.incident_id}</span>
                {onSelectIncident && fullAlert.incident_id && (
                  <button
                    onClick={() => {
                      onClose();
                      onSelectIncident(fullAlert.incident_id);
                    }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: '#fff',
                      backgroundColor: '#4f46e5',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    <Eye size={12} /> Inspect Evidence
                  </button>
                )}
              </div>
            </div>
            <div className="meta-item">
              <span className="meta-label">Resolution Time</span>
              <span className="meta-value">
                {fullAlert.resolved_at
                  ? new Date(fullAlert.resolved_at).toLocaleString()
                  : 'Pending'}
              </span>
            </div>
          </div>

          {/* Evidence Archival Section */}
          <div className="modal-section">
            <h4 className="section-subtitle">
              <ImageIcon size={16} /> Incident Visual Evidence & Tamper Verification
            </h4>

            {evidenceList && evidenceList.length > 0 ? (
              <div className="evidence-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '12px' }}>
                {evidenceList.map((ev) => (
                  <div
                    key={ev.evidence_id}
                    className="evidence-card"
                    style={{
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      background: 'rgba(15, 23, 42, 0.6)',
                    }}
                  >
                    <div style={{ position: 'relative', width: '100%', maxHeight: '200px', overflow: 'hidden', background: '#000' }}>
                      <img
                        src={ev.download_url}
                        alt="Incident Evidence"
                        style={{ width: '100%', height: 'auto', display: 'block', objectFit: 'contain' }}
                      />
                    </div>
                    <div style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                          Camera: <strong style={{ color: '#f1f5f9' }}>{ev.camera_id}</strong>
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {(ev.file_size_bytes / 1024).toFixed(1)} KB
                        </span>
                      </div>

                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '0.75rem',
                          background: 'rgba(16, 185, 129, 0.1)',
                          color: '#34d399',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          marginBottom: '10px',
                          fontFamily: 'monospace',
                        }}
                      >
                        <ShieldCheck size={14} />
                        <span>SHA-256: {ev.sha256_checksum.slice(0, 16)}...</span>
                      </div>

                      <a
                        href={ev.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-secondary"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '0.8rem',
                          padding: '6px 12px',
                          textDecoration: 'none',
                          color: '#e2e8f0',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          borderRadius: '6px',
                        }}
                      >
                        <Download size={14} /> Download Evidence
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text" style={{ fontSize: '0.85rem', color: '#94a3b8', fontStyle: 'italic', margin: '8px 0' }}>
                No visual snapshot archived for this incident (feed offline or inactive during detection).
              </p>
            )}
          </div>

          {/* Audit Trail / History */}
          <div className="modal-section">
            <h4 className="section-subtitle">
              <History size={16} /> Audit History & Escalation Trail
            </h4>

            {loading ? (
              <p className="loading-text">Loading audit trail...</p>
            ) : fullAlert.history && fullAlert.history.length > 0 ? (
              <div className="audit-timeline">
                {fullAlert.history.map((h, idx) => (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-dot" />
                    <div className="timeline-content">
                      <div className="timeline-header">
                        <span className="timeline-action">{h.action}</span>
                        {h.previous_level && h.new_level && (
                          <span className="timeline-escalation">
                            {h.previous_level} → {h.new_level}
                          </span>
                        )}
                        <span className="timeline-time">
                          {new Date(h.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {h.reason && <p className="timeline-reason">{h.reason}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-text">No additional lifecycle transitions logged.</p>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer">
          <div className="modal-action-buttons">
            {fullAlert.status === 'ACTIVE' && (
              <button
                className="btn btn-ack"
                disabled={actionInProgress !== null}
                onClick={() => handleAction('ack')}
              >
                <Check size={16} />
                {actionInProgress === 'ack' ? 'Acknowledging...' : 'Acknowledge Alert'}
              </button>
            )}

            {fullAlert.status !== 'RESOLVED' && fullAlert.status !== 'DISMISSED' && (
              <>
                <button
                  className="btn btn-resolve"
                  disabled={actionInProgress !== null}
                  onClick={() => handleAction('resolve')}
                >
                  <CheckCircle2 size={16} />
                  {actionInProgress === 'resolve' ? 'Resolving...' : 'Resolve Hazard'}
                </button>

                <button
                  className="btn btn-dismiss"
                  disabled={actionInProgress !== null}
                  onClick={() => handleAction('dismiss')}
                >
                  <AlertOctagon size={16} />
                  {actionInProgress === 'dismiss' ? 'Dismissing...' : 'Dismiss'}
                </button>
              </>
            )}
          </div>

          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
