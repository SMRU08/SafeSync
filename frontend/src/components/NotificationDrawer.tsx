/**
 * NotificationDrawer.tsx — SafeSync Industrial SOC
 * Real-Time Notification Center Drawer (Phase 20).
 * Slides in from the right with tabbed filtering by severity, immediate triage actions, and incident linkage.
 */

import React, { useState } from 'react';
import {
  X,
  Bell,
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  Clock,
  Check,
} from 'lucide-react';
import { Alert } from '../types';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: Alert[];
  onSelectAlert?: (alert: Alert) => void;
  onAcknowledgeAlert?: (alertId: string) => Promise<void>;
  onResolveAlert?: (alertId: string) => Promise<void>;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  alerts,
  onSelectAlert,
  onAcknowledgeAlert,
  onResolveAlert,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'WARNING' | 'INFO'>('ALL');
  const [actingId, setActingId] = useState<string | null>(null);

  if (!isOpen) return null;

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'CRITICAL') return alert.severity === 'CRITICAL' || alert.severity === 'HIGH';
    if (filter === 'WARNING') return alert.severity === 'MEDIUM';
    if (filter === 'INFO') return alert.severity === 'LOW';
    return true;
  });

  const handleAction = async (e: React.MouseEvent, alertId: string, type: 'ack' | 'resolve') => {
    e.stopPropagation();
    setActingId(alertId);
    try {
      if (type === 'ack' && onAcknowledgeAlert) {
        await onAcknowledgeAlert(alertId);
      } else if (type === 'resolve' && onResolveAlert) {
        await onResolveAlert(alertId);
      }
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden select-none">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-[#0c1424] border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform duration-300 ease-out">
          {/* Drawer Header */}
          <div className="px-4 py-4 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                  SOC Notification Center
                  <span className="text-[10px] font-mono px-2 py-0.2 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    {alerts.filter((a) => a.status === 'ACTIVE').length} Active
                  </span>
                </h3>
                <p className="text-[10px] text-slate-400">Real-time hazard alerts &amp; infraction audit log</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1 px-4 py-2 bg-slate-950/60 border-b border-slate-800/80 text-xs">
            {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition ${
                  filter === tab
                    ? 'bg-sky-600 text-white shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                {tab === 'ALL' ? 'All Alerts' : tab === 'CRITICAL' ? 'P0/P1 Critical' : tab === 'WARNING' ? 'P2 Warning' : 'P3 Info'}
              </button>
            ))}
          </div>

          {/* Notification List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/40 p-2 space-y-1">
            {filteredAlerts.length === 0 ? (
              <div className="py-16 text-center text-slate-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-300">All Alerts Cleared</p>
                <p className="text-[11px] text-slate-500 mt-1">No alerts match the selected priority filter.</p>
              </div>
            ) : (
              filteredAlerts.map((alert) => {
                const isCritical = alert.severity === 'CRITICAL' || alert.severity === 'HIGH';
                const isMedium = alert.severity === 'MEDIUM';

                return (
                  <div
                    key={alert.alert_id}
                    onClick={() => {
                      if (onSelectAlert) onSelectAlert(alert);
                      onClose();
                    }}
                    className="p-3 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800/70 hover:border-slate-700 transition cursor-pointer flex flex-col justify-between gap-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2.5">
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                            isCritical
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              : isMedium
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                              : 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                          }`}
                        >
                          {isCritical ? (
                            <AlertOctagon className="w-4 h-4" />
                          ) : isMedium ? (
                            <AlertTriangle className="w-4 h-4" />
                          ) : (
                            <Info className="w-4 h-4" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-200 leading-tight">
                              {alert.title}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                            {alert.message}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                          isCritical
                            ? 'text-rose-400 bg-rose-500/15 border-rose-500/30'
                            : isMedium
                            ? 'text-amber-400 bg-amber-500/15 border-amber-500/30'
                            : 'text-sky-400 bg-sky-500/15 border-sky-500/30'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>

                    {/* Metadata & Actions */}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/50 text-[10px] text-slate-400">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-400">{alert.camera_id}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {alert.status === 'ACTIVE' && onAcknowledgeAlert && (
                          <button
                            onClick={(e) => handleAction(e, alert.alert_id, 'ack')}
                            disabled={actingId === alert.alert_id}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition text-[10px] font-semibold"
                          >
                            Ack
                          </button>
                        )}
                        {alert.status !== 'RESOLVED' && onResolveAlert && (
                          <button
                            onClick={(e) => handleAction(e, alert.alert_id, 'resolve')}
                            disabled={actingId === alert.alert_id}
                            className="px-2 py-0.5 rounded bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 transition text-[10px] font-semibold flex items-center gap-1"
                          >
                            <Check className="w-3 h-3" />
                            Resolve
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDrawer;
