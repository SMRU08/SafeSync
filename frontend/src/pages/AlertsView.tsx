/**
 * AlertsView.tsx — RAKSHYA VISION Professional SOC
 * Centralized Operations Management for Safety Alerts & Verified Incidents.
 * Features tabs for ACTIVE, ACKNOWLEDGED, RESOLVED, and DISMISSED alerts with
 * full operational lifecycle action buttons (Acknowledge, Resolve, Dismiss).
 */

import React, { useState } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  RefreshCw,
  Eye,
} from 'lucide-react';
import { Alert, Incident, RiskSummary, RiskLevel, AlertStatus } from '../types';

interface AlertsViewProps {
  alerts: Alert[];
  incidents?: Incident[];
  summary?: RiskSummary | null;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onRefresh?: () => void;
  onSelectAlert?: (alert: Alert) => void;
  onSelectIncident?: (incidentId: string) => void;
}

export const AlertsView: React.FC<AlertsViewProps> = ({
  alerts,
  incidents: _incidents,
  onAcknowledge,
  onResolve,
  onDismiss,
  onRefresh,
  onSelectAlert,
  onSelectIncident,
}) => {
  const [activeTab, setActiveTab] = useState<AlertStatus>('ACTIVE');
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  // Filter alerts by tab, severity, and search query
  const filteredAlerts = alerts.filter((alert) => {
    if (alert.status !== activeTab) return false;
    if (severityFilter !== 'ALL' && alert.severity !== severityFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        alert.alert_id.toLowerCase().includes(q) ||
        alert.camera_id.toLowerCase().includes(q) ||
        alert.zone_id.toLowerCase().includes(q) ||
        alert.event_type.toLowerCase().includes(q) ||
        (alert.message && alert.message.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getSeverityBadge = (sev: RiskLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-600 text-white';
      case 'HIGH':
        return 'bg-rose-500 text-white';
      case 'MEDIUM':
        return 'bg-amber-500 text-white';
      case 'LOW':
        return 'bg-sky-500 text-white';
      default:
        return 'bg-slate-500 text-white';
    }
  };

  const counts = {
    ACTIVE: alerts.filter((a) => a.status === 'ACTIVE').length,
    ACKNOWLEDGED: alerts.filter((a) => a.status === 'ACKNOWLEDGED').length,
    RESOLVED: alerts.filter((a) => a.status === 'RESOLVED').length,
    DISMISSED: alerts.filter((a) => a.status === 'DISMISSED').length,
  };

  const handleAction = async (id: string, actionFn: (id: string) => Promise<void>) => {
    setActionInProgress(id);
    try {
      await actionFn(id);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-500" />
            Alerts &amp; Incident Lifecycle Triage
          </h2>
          <p className="text-xs text-slate-500">
            Real-time incident dispatch, human-in-the-loop acknowledgment, and compliance remediation
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="self-start sm:self-auto px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-xs flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-sky-600" />
            <span>Refresh Ledger</span>
          </button>
        )}
      </div>

      {/* Main Ledger Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        {/* Tabs Row */}
        <div className="flex items-center gap-2 px-4 pt-3 border-b border-slate-200 bg-white">
          {(['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'] as AlertStatus[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2.5 px-3 text-xs font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
                activeTab === tab
                  ? 'border-sky-600 text-sky-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <span>{tab}</span>
              <span
                className={`text-[9px] px-1.5 py-0.2 rounded-full font-mono ${
                  activeTab === tab
                    ? 'bg-sky-100 text-sky-800'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {counts[tab]}
              </span>
            </button>
          ))}
        </div>

        {/* Filter Toolbar */}
        <div className="p-3 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white">
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search alerts, zones, cameras..."
                className="w-full bg-slate-50 border border-slate-200 text-xs rounded-md pl-8 pr-3 py-1.5 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-50 border border-slate-200 text-xs rounded-md py-1 px-2.5 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>

          <span className="text-[11px] text-slate-400 font-mono-nums">
            Showing {filteredAlerts.length} entries
          </span>
        </div>

        {/* Ledger Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[10px] uppercase">
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Incident ID</th>
                <th className="py-2.5 px-3">Hazard Event</th>
                <th className="py-2.5 px-3">Camera Node</th>
                <th className="py-2.5 px-3">Plant Zone</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-400">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-1.5" />
                    <p className="text-xs font-semibold text-slate-700">No {activeTab} Alerts</p>
                    <p className="text-[10px] text-slate-400">Ledger is clear for this state.</p>
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((a) => {
                  const isBusy = actionInProgress === a.alert_id;

                  return (
                    <tr key={a.alert_id} className="hover:bg-slate-50 transition">
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[8px] font-bold px-2 py-0.5 rounded tracking-wide ${getSeverityBadge(
                            a.severity
                          )}`}
                        >
                          {a.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">
                        {onSelectAlert ? (
                          <button
                            onClick={() => onSelectAlert(a)}
                            className="hover:text-indigo-600 hover:underline text-left cursor-pointer"
                            title="Click to view alert details"
                          >
                            {a.alert_id}
                          </button>
                        ) : (
                          a.alert_id
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <div
                          className={`font-semibold text-slate-800 ${onSelectAlert ? 'cursor-pointer hover:text-indigo-600' : ''}`}
                          onClick={() => onSelectAlert && onSelectAlert(a)}
                        >
                          {a.title || a.event_type.replace(/_/g, ' ')}
                        </div>
                        <p className="text-[10px] text-slate-500 truncate max-w-xs">{a.message}</p>
                      </td>
                      <td className="py-2.5 px-3 font-mono-nums text-slate-600">{a.camera_id}</td>
                      <td className="py-2.5 px-3 text-slate-600">{a.zone_id}</td>
                      <td className="py-2.5 px-3 font-mono-nums text-slate-500 text-[11px]">
                        {new Date(a.timestamp).toLocaleString('en-GB')}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-[10px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                          {a.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {(onSelectIncident || onSelectAlert) && (
                            <button
                              onClick={() => {
                                if (onSelectIncident && a.incident_id) {
                                  onSelectIncident(a.incident_id);
                                } else if (onSelectAlert) {
                                  onSelectAlert(a);
                                }
                              }}
                              className="px-2 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded text-[10px] font-semibold transition cursor-pointer flex items-center gap-1 shadow-xs"
                              title="Forensic Snapshot & Incident Evidence"
                            >
                              <Eye className="w-3 h-3" />
                              <span>Inspect</span>
                            </button>
                          )}
                          {a.status === 'ACTIVE' && (
                            <button
                              disabled={isBusy}
                              onClick={() => handleAction(a.alert_id, onAcknowledge)}
                              className="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-[10px] font-semibold transition cursor-pointer shadow-xs disabled:opacity-50"
                            >
                              Ack
                            </button>
                          )}
                          {a.status !== 'RESOLVED' && (
                            <button
                              disabled={isBusy}
                              onClick={() => handleAction(a.alert_id, onResolve)}
                              className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-semibold transition cursor-pointer shadow-xs disabled:opacity-50"
                            >
                              Resolve
                            </button>
                          )}
                          {a.status !== 'DISMISSED' && a.status !== 'RESOLVED' && (
                            <button
                              disabled={isBusy}
                              onClick={() => handleAction(a.alert_id, onDismiss)}
                              className="px-2 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-[10px] font-semibold transition cursor-pointer disabled:opacity-50"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AlertsView;
