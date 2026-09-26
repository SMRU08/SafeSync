/**
 * AlertsTimeline.tsx — SafeSync Professional SOC
 * Enterprise real-time incident log with dark header, timeline styling,
 * severity badges, and direct operational action buttons (Acknowledge & Resolve).
 */

import React from 'react';
import { ShieldCheck, ArrowRight, Clock, Radio } from 'lucide-react';
import { Alert, RiskLevel } from '../types';

interface AlertsTimelineProps {
  alerts: Alert[];
  onAcknowledge?: (alertId: string) => Promise<void>;
  onResolve?: (alertId: string) => Promise<void>;
  onViewAll?: () => void;
  onSelectAlert?: (alert: Alert) => void;
}

export const AlertsTimeline: React.FC<AlertsTimelineProps> = ({
  alerts,
  onAcknowledge,
  onResolve,
  onViewAll,
  onSelectAlert,
}) => {
  const activeAlerts = alerts.filter((a) => a.status === 'ACTIVE' || a.status === 'ACKNOWLEDGED');

  const formatTimestamp = (ts?: string) => {
    if (!ts) return '--:--:--';
    try {
      const d = new Date(ts);
      return d.toTimeString().split(' ')[0];
    } catch {
      return '--:--:--';
    }
  };

  const getSeverityConfig = (sev: RiskLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-950/30',
          border: 'border-rose-500',
          borderLeft: 'border-l-rose-500',
          badge: 'bg-rose-600 text-white',
          dot: 'bg-rose-500 animate-pulse',
          text: 'text-rose-400',
        };
      case 'HIGH':
        return {
          bg: 'bg-rose-900/20',
          border: 'border-rose-700/60',
          borderLeft: 'border-l-rose-400',
          badge: 'bg-rose-500 text-white',
          dot: 'bg-rose-400',
          text: 'text-rose-300',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-900/20',
          border: 'border-amber-700/60',
          borderLeft: 'border-l-amber-400',
          badge: 'bg-amber-500 text-white',
          dot: 'bg-amber-400',
          text: 'text-amber-300',
        };
      default:
        return {
          bg: 'bg-sky-900/20',
          border: 'border-sky-700/60',
          borderLeft: 'border-l-sky-400',
          badge: 'bg-sky-500 text-white',
          dot: 'bg-sky-400',
          text: 'text-sky-300',
        };
    }
  };

  return (
    <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 shadow-xl overflow-hidden flex flex-col">
      {/* Dark Header */}
      <div className="px-4 py-3 bg-[#111f35] border-b border-slate-700/80 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
            <h3 className="font-bold text-xs text-white tracking-wide uppercase">
              Incident Log
            </h3>
          </div>
          {activeAlerts.length > 0 && (
            <span className="flex items-center gap-1 bg-rose-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
              {activeAlerts.length} Active
            </span>
          )}
        </div>
        {onViewAll && (
          <button
            onClick={onViewAll}
            className="text-[10px] font-semibold text-sky-400 hover:text-sky-200 flex items-center gap-1 transition"
          >
            View All <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Alerts Timeline List */}
      <div className="space-y-0 max-h-[380px] overflow-y-auto divide-y divide-slate-700/50">
        {activeAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <ShieldCheck className="w-10 h-10 text-emerald-500 mb-2" />
            <p className="text-xs font-bold text-emerald-400">All Zones Clear</p>
            <p className="text-[10px] text-slate-500 mt-0.5">No active incidents or PPE violations</p>
          </div>
        ) : (
          activeAlerts.slice(0, 6).map((alert) => {
            const config = getSeverityConfig(alert.severity);
            const timeStr = formatTimestamp(alert.timestamp);
            const isCritical = alert.severity === 'CRITICAL' || alert.severity === 'HIGH';

            return (
              <div
                key={alert.alert_id}
                className={`relative pl-3 pr-3 py-2.5 flex items-start gap-2.5 transition hover:bg-slate-800/40 border-l-2 ${config.borderLeft} ${
                  isCritical ? 'bg-rose-950/20' : 'bg-transparent'
                }`}
              >
                {/* Timeline dot */}
                <span className={`w-2 h-2 rounded-full ${config.dot} mt-1 flex-shrink-0`} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Time */}
                    <div className="flex items-center gap-1 text-[9px] text-slate-400 font-mono-nums">
                      <Clock className="w-2.5 h-2.5" />
                      <span>{timeStr}</span>
                    </div>
                    {/* Severity badge */}
                    <span className={`${config.badge} font-bold text-[8px] px-1.5 py-0.5 rounded tracking-widest uppercase`}>
                      {alert.severity}
                    </span>
                    {/* Status chip */}
                    <span className={`text-[8px] font-semibold uppercase tracking-wider ${
                      alert.status === 'ACTIVE' ? 'text-rose-400' : 'text-amber-400'
                    }`}>
                      {alert.status}
                    </span>
                  </div>

                  {/* Alert title */}
                  <div
                    onClick={() => onSelectAlert?.(alert)}
                    className="font-bold text-white text-[11px] mt-1 truncate cursor-pointer hover:text-sky-300 transition"
                    title={alert.title}
                  >
                    {alert.title || alert.event_type.replace(/_/g, ' ')}
                  </div>

                  {/* Alert message */}
                  <p className="text-[10px] text-slate-400 leading-snug line-clamp-1 mt-0.5">
                    {alert.message || 'Safety anomaly flagged by edge AI engine.'}
                  </p>

                  {/* Footer: camera + zone + actions */}
                  <div className="flex items-center justify-between mt-1.5">
                    <p className="text-[9px] text-slate-500 font-mono-nums truncate max-w-[130px]">
                      {alert.camera_id} • {alert.zone_id}
                    </p>

                    {/* Operational Action Buttons */}
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {alert.status === 'ACTIVE' && onAcknowledge && (
                        <button
                          onClick={() => onAcknowledge(alert.alert_id)}
                          className="px-2 py-0.5 bg-amber-500 hover:bg-amber-400 text-white text-[9px] font-bold rounded shadow-sm transition cursor-pointer"
                        >
                          Ack
                        </button>
                      )}
                      {alert.status !== 'RESOLVED' && onResolve && (
                        <button
                          onClick={() => onResolve(alert.alert_id)}
                          className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white text-[9px] font-bold rounded shadow-sm transition cursor-pointer"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AlertsTimeline;
