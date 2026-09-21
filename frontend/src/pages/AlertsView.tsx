/**
 * AlertsView.tsx — RAKSHYA VISION Phase 8
 * Centralized Operations Management for Safety Alerts & Verified Incidents.
 */

import React, { useState } from 'react';
import {
  Bell,
  Layers,
  Search,
  Filter,
  ChevronRight,
} from 'lucide-react';
import { Alert, Incident, RiskSummary } from '../types';
import { AlertsTable } from '../components/AlertsTable';
import { AlertDetailModal } from '../components/AlertDetailModal';
import { IncidentDetailModal } from '../components/IncidentDetailModal';

interface AlertsViewProps {
  alerts: Alert[];
  incidents: Incident[];
  summary: RiskSummary | null;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
}

export const AlertsView: React.FC<AlertsViewProps> = ({
  alerts,
  incidents,
  summary,
  onAcknowledge,
  onResolve,
  onDismiss,
}) => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'incidents'>('alerts');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [incidentSearch, setIncidentSearch] = useState<string>('');
  const [incidentStatusFilter, setIncidentStatusFilter] = useState<string>('ALL');

  const filteredIncidents = incidents.filter((inc) => {
    if (incidentStatusFilter !== 'ALL' && inc.status !== incidentStatusFilter) return false;
    if (incidentSearch.trim()) {
      const q = incidentSearch.toLowerCase();
      return (
        inc.incident_id.toLowerCase().includes(q) ||
        inc.camera_id.toLowerCase().includes(q) ||
        inc.zone_id.toLowerCase().includes(q) ||
        inc.event_types.some((t) => t.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="alerts-view-container">
      {/* Title Bar */}
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Bell size={22} /> Alerts & Incidents Operations Center
          </h2>
          <p className="view-subheading">
            Deduplicated, prioritized safety alerts with escalation tracking and human-in-the-loop acknowledgement
          </p>
        </div>

        {/* View Toggle Tabs */}
        <div className="view-tab-toggle">
          <button
            className={`toggle-btn ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            <Bell size={14} />
            <span>Alerts ({alerts.length})</span>
          </button>
          <button
            className={`toggle-btn ${activeTab === 'incidents' ? 'active' : ''}`}
            onClick={() => setActiveTab('incidents')}
          >
            <Layers size={14} />
            <span>Incidents ({incidents.length})</span>
          </button>
        </div>
      </div>

      {/* Quick Severity Distribution Bar */}
      <div className="alerts-summary-strip">
        <div className="summary-strip-item strip-critical">
          <span className="strip-count font-mono">{summary?.critical ?? 0}</span>
          <span className="strip-label">CRITICAL</span>
        </div>
        <div className="summary-strip-item strip-high">
          <span className="strip-count font-mono">{summary?.high ?? 0}</span>
          <span className="strip-label">HIGH</span>
        </div>
        <div className="summary-strip-item strip-medium">
          <span className="strip-count font-mono">{summary?.medium ?? 0}</span>
          <span className="strip-label">MEDIUM</span>
        </div>
        <div className="summary-strip-item strip-low">
          <span className="strip-count font-mono">{summary?.low ?? 0}</span>
          <span className="strip-label">LOW</span>
        </div>
        <div className="summary-strip-item strip-open">
          <span className="strip-count font-mono">{summary?.open_incidents ?? 0}</span>
          <span className="strip-label">OPEN INCIDENTS</span>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'alerts' ? (
        <AlertsTable
          alerts={alerts}
          onSelectAlert={(alt) => setSelectedAlert(alt)}
          onAcknowledge={onAcknowledge}
          onResolve={onResolve}
          onDismiss={onDismiss}
        />
      ) : (
        <div className="incidents-section">
          {/* Incident Filter Controls */}
          <div className="table-controls-bar">
            <div className="search-input-wrap">
              <Search size={16} className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Search incidents by ID, camera, zone, or event..."
                value={incidentSearch}
                onChange={(e) => setIncidentSearch(e.target.value)}
              />
            </div>
            <div className="filter-selects-group">
              <div className="filter-item">
                <Filter size={14} />
                <select
                  className="filter-select"
                  value={incidentStatusFilter}
                  onChange={(e) => setIncidentStatusFilter(e.target.value)}
                >
                  <option value="ALL">All Statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="ACKNOWLEDGED">Acknowledged</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="DISMISSED">Dismissed</option>
                </select>
              </div>
            </div>
          </div>

          {/* Incidents Table */}
          {filteredIncidents.length === 0 ? (
            <div className="table-empty-state">
              <Layers size={36} className="empty-icon" />
              <h4 className="empty-title">
                {incidents.length === 0 ? 'NO DATA AVAILABLE' : 'NO MATCHING INCIDENTS'}
              </h4>
              <p className="empty-subtitle">
                {incidents.length === 0
                  ? 'No safety incidents have been recorded in the database.'
                  : 'Try changing your filter settings.'}
              </p>
            </div>
          ) : (
            <div className="responsive-table-wrap">
              <table className="soc-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Risk Score & Level</th>
                    <th>Events</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Created Time</th>
                    <th className="text-right">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.map((inc) => (
                    <tr
                      key={inc.incident_id}
                      className="soc-row"
                      onClick={() => setSelectedIncident(inc)}
                    >
                      <td className="font-mono text-accent">{inc.incident_id}</td>
                      <td>
                        <span className={`badge severity-${inc.risk_level.toLowerCase()}`}>
                          {inc.risk_level} ({inc.risk_score}/100)
                        </span>
                      </td>
                      <td>
                        <div className="incident-events-list">
                          {inc.event_types.map((e, idx) => (
                            <span key={idx} className="event-pill">
                              {e}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div>{inc.camera_id}</div>
                        <div className="text-xs text-muted">{inc.zone_id}</div>
                      </td>
                      <td>
                        <span className={`badge status-${inc.status.toLowerCase()}`}>
                          {inc.status}
                        </span>
                      </td>
                      <td className="text-muted text-xs">
                        {new Date(inc.created_at).toLocaleString()}
                      </td>
                      <td className="text-right">
                        <button
                          className="btn-icon btn-action-detail"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedIncident(inc);
                          }}
                        >
                          <ChevronRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <AlertDetailModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={onAcknowledge}
        onResolve={onResolve}
        onDismiss={onDismiss}
      />

      <IncidentDetailModal
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
        onSelectAlert={(altId) => {
          setSelectedIncident(null);
          const found = alerts.find((a) => a.alert_id === altId);
          if (found) setSelectedAlert(found);
        }}
      />
    </div>
  );
};
