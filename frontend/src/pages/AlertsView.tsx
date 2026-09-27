/**
 * AlertsView.tsx — SafeSync Professional SOC
 * Centralized Operations Management for Safety Alerts & Verified Incidents (Phase 14 & 15).
 * Features Priority tiers (P0 Critical, P1 High, P2 Medium, P3 Low),
 * lifecycle status filtering (ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED),
 * operator triage actions, and linked forensic evidence navigation.
 */

import React, { useState } from 'react';
import {
  AlertTriangle,
  Search,
  CheckCircle2,
  RefreshCw,
  Check,
  ExternalLink,
} from 'lucide-react';
import { Alert, Incident, RiskSummary, AlertStatus } from '../types';
import { EmptyState } from '../components/ui/EmptyState';

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
  onDismiss: _onDismiss,
  onRefresh,
  onSelectAlert,
  onSelectIncident,
}) => {
  const [activeTab, setActiveTab] = useState<AlertStatus>('ACTIVE');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  // Filter alerts by tab, priority, and search query
  const filteredAlerts = alerts.filter((alert) => {
    if (alert.status !== activeTab) return false;
    if (priorityFilter !== 'ALL') {
      const p = alert.priority || (alert.severity === 'CRITICAL' ? 'P0' : alert.severity === 'HIGH' ? 'P1' : 'P2');
      if (p !== priorityFilter) return false;
    }
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

  const getPriorityBadgeClass = (priority?: string, sev?: string) => {
    const p = priority || (sev === 'CRITICAL' ? 'P0' : sev === 'HIGH' ? 'P1' : 'P2');
    switch (p) {
      case 'P0':
        return 'text-rose-400 bg-rose-500/15 border-rose-500/30';
      case 'P1':
        return 'text-orange-400 bg-orange-500/15 border-orange-500/30';
      case 'P2':
        return 'text-amber-400 bg-amber-500/15 border-amber-500/30';
      default:
        return 'text-sky-400 bg-sky-500/15 border-sky-500/30';
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
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#070b14] text-slate-100 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
                Alerts &amp; Incident Operations
                <span className="text-[11px] font-mono px-2 py-0.2 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 font-medium">
                  {counts.ACTIVE} Active Alerts
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Priority-tiered alarm queue with operator acknowledgement, cooldown suppression, and resolution ledger
              </p>
            </div>
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="self-start sm:self-auto px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-sky-400" />
            <span>Refresh Ledger</span>
          </button>
        )}
      </div>

      {/* Main Ledger Card */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden flex flex-col">
        {/* Status Tab Navigation & Search Filters */}
        <div className="p-4 bg-slate-900/80 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            {(['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === tab
                    ? 'bg-sky-600 text-white shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80'
                }`}
              >
                <span>{tab}</span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    activeTab === tab ? 'bg-sky-800 text-white' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {counts[tab]}
                </span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            {/* Priority Filter */}
            <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-950 border border-slate-800 text-xs">
              {(['ALL', 'P0', 'P1', 'P2'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPriorityFilter(p)}
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                    priorityFilter === p
                      ? 'bg-slate-800 text-white font-bold'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {p === 'ALL' ? 'All' : p}
                </button>
              ))}
            </div>

            {/* Search Box */}
            <div className="relative w-48 sm:w-60">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search alerts, cameras..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>
        </div>

        {/* Alerts Table */}
        {filteredAlerts.length === 0 ? (
          <EmptyState
            icon={CheckCircle2}
            title={`No ${activeTab} Alerts`}
            description={`There are currently no alerts in ${activeTab.toLowerCase()} status matching the filters.`}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase tracking-wider">
                  <th className="py-3 px-4">Priority / Severity</th>
                  <th className="py-3 px-4">Event Description</th>
                  <th className="py-3 px-4">Camera &amp; Zone</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredAlerts.map((alert) => {
                  const isActing = actionInProgress === alert.alert_id;
                  const priority = alert.priority || (alert.severity === 'CRITICAL' ? 'P0' : alert.severity === 'HIGH' ? 'P1' : 'P2');

                  return (
                    <tr
                      key={alert.alert_id}
                      onClick={() => onSelectAlert?.(alert)}
                      className="hover:bg-slate-900/60 transition cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getPriorityBadgeClass(alert.priority, alert.severity)}`}>
                            {priority} • {alert.severity}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div>
                          <div className="font-bold text-white text-xs leading-tight">
                            {alert.title}
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5 max-w-md line-clamp-1">
                            {alert.message}
                          </p>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="text-[11px] text-slate-300 font-mono">
                          {alert.camera_id}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {alert.zone_id || 'production_floor'}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-mono text-[11px] text-slate-400">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          {alert.status === 'ACTIVE' && (
                            <button
                              onClick={() => handleAction(alert.alert_id, onAcknowledge)}
                              disabled={isActing}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition"
                            >
                              Ack
                            </button>
                          )}

                          {alert.status !== 'RESOLVED' && (
                            <button
                              onClick={() => handleAction(alert.alert_id, onResolve)}
                              disabled={isActing}
                              className="px-2.5 py-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 text-[11px] font-semibold transition flex items-center gap-1"
                            >
                              <Check className="w-3 h-3" /> Resolve
                            </button>
                          )}

                          {alert.incident_id && onSelectIncident && (
                            <button
                              onClick={() => onSelectIncident(alert.incident_id)}
                              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
                              title="Open Incident File"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsView;
