/**
 * AlertsTable.tsx — SafeSync Phase 8
 * Interactive alerts table with multi-criteria filtering, search, and instant action triggers.
 */

import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  Check,
  CheckCircle2,
  AlertOctagon,
  ChevronRight,
} from 'lucide-react';
import { Alert, RiskLevel, AlertStatus } from '../types';

interface AlertsTableProps {
  alerts: Alert[];
  onSelectAlert: (alert: Alert) => void;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  compact?: boolean;
}

export const AlertsTable: React.FC<AlertsTableProps> = ({
  alerts,
  onSelectAlert,
  onAcknowledge,
  onResolve,
  onDismiss,
  compact = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      // Search
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const matchTitle = a.title.toLowerCase().includes(term);
        const matchMsg = a.message.toLowerCase().includes(term);
        const matchCam = a.camera_id.toLowerCase().includes(term);
        const matchZone = a.zone_id.toLowerCase().includes(term);
        const matchId = a.alert_id.toLowerCase().includes(term);
        if (!matchTitle && !matchMsg && !matchCam && !matchZone && !matchId) {
          return false;
        }
      }
      // Severity
      if (severityFilter !== 'ALL' && a.severity !== severityFilter) {
        return false;
      }
      // Status
      if (statusFilter !== 'ALL' && a.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [alerts, searchTerm, severityFilter, statusFilter]);

  const handleAction = async (e: React.MouseEvent, action: 'ack' | 'resolve' | 'dismiss', alertId: string) => {
    e.stopPropagation();
    setActionLoadingId(`${action}-${alertId}`);
    try {
      if (action === 'ack') await onAcknowledge(alertId);
      if (action === 'resolve') await onResolve(alertId);
      if (action === 'dismiss') await onDismiss(alertId);
    } finally {
      setActionLoadingId(null);
    }
  };

  const getSeverityBadge = (severity: RiskLevel) => {
    return <span className={`badge severity-${severity.toLowerCase()}`}>{severity}</span>;
  };

  const getStatusBadge = (status: AlertStatus) => {
    return <span className={`badge status-${status.toLowerCase()}`}>{status}</span>;
  };

  return (
    <div className="alerts-table-container">
      {/* Controls / Filter Bar */}
      {!compact && (
        <div className="table-controls-bar">
          <div className="search-input-wrap">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by title, message, camera, or alert ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button className="clear-search-btn" onClick={() => setSearchTerm('')}>
                ×
              </button>
            )}
          </div>

          <div className="filter-selects-group">
            <div className="filter-item">
              <Filter size={14} className="filter-icon" />
              <select
                className="filter-select"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div className="filter-item">
              <select
                className="filter-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="RESOLVED">Resolved</option>
                <option value="DISMISSED">Dismissed</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Table / List */}
      {filteredAlerts.length === 0 ? (
        <div className="table-empty-state">
          <ShieldAlert size={36} className="empty-icon" />
          <h4 className="empty-title">
            {alerts.length === 0 ? 'NO DATA AVAILABLE' : 'NO MATCHING ALERTS'}
          </h4>
          <p className="empty-subtitle">
            {alerts.length === 0
              ? 'No safety alerts have been recorded in the database.'
              : 'No alerts match the selected search or filter criteria.'}
          </p>
        </div>
      ) : (
        <div className="responsive-table-wrap">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Alert Title & Description</th>
                <th>Location</th>
                <th>Status</th>
                <th>Time</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alt) => (
                <tr
                  key={alt.alert_id}
                  className={`soc-row row-${alt.severity.toLowerCase()} ${
                    alt.status === 'ACTIVE' && alt.severity === 'CRITICAL' ? 'row-pulse' : ''
                  }`}
                  onClick={() => onSelectAlert(alt)}
                >
                  <td className="cell-severity">{getSeverityBadge(alt.severity)}</td>
                  <td className="cell-content">
                    <div className="alert-row-title">{alt.title}</div>
                    <div className="alert-row-message">{alt.message}</div>
                    <div className="alert-row-sub">
                      <span className="font-mono text-muted">{alt.alert_id}</span>
                      <span className="dot-sep">•</span>
                      <span className="text-muted">Type: {alt.event_type}</span>
                    </div>
                  </td>
                  <td className="cell-location">
                    <div className="location-cam">{alt.camera_id}</div>
                    <div className="location-zone">{alt.zone_id}</div>
                  </td>
                  <td className="cell-status">{getStatusBadge(alt.status)}</td>
                  <td className="cell-time">
                    <div className="time-primary">
                      {new Date(alt.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="time-secondary">
                      {new Date(alt.timestamp).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="cell-actions text-right">
                    <div className="action-buttons-group">
                      {alt.status === 'ACTIVE' && (
                        <button
                          className="btn-icon btn-action-ack"
                          title="Acknowledge Alert"
                          disabled={actionLoadingId === `ack-${alt.alert_id}`}
                          onClick={(e) => handleAction(e, 'ack', alt.alert_id)}
                        >
                          <Check size={14} />
                        </button>
                      )}

                      {alt.status !== 'RESOLVED' && alt.status !== 'DISMISSED' && (
                        <>
                          <button
                            className="btn-icon btn-action-resolve"
                            title="Resolve Alert"
                            disabled={actionLoadingId === `resolve-${alt.alert_id}`}
                            onClick={(e) => handleAction(e, 'resolve', alt.alert_id)}
                          >
                            <CheckCircle2 size={14} />
                          </button>
                          <button
                            className="btn-icon btn-action-dismiss"
                            title="Dismiss Alert"
                            disabled={actionLoadingId === `dismiss-${alt.alert_id}`}
                            onClick={(e) => handleAction(e, 'dismiss', alt.alert_id)}
                          >
                            <AlertOctagon size={14} />
                          </button>
                        </>
                      )}

                      <button
                        className="btn-icon btn-action-detail"
                        title="View Full Details"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAlert(alt);
                        }}
                      >
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
