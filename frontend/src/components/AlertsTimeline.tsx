/**
 * AlertsTimeline.tsx — RAKSHYA VISION Professional SOC
 * Real-time alert feed panel with timeline styling, severity badges,
 * and direct operational action buttons (Acknowledge & Resolve).
 */

import React from 'react';
import { AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';
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
          bg: 'bg-rose-50/80',
          border: 'border-rose-200',
          badge: 'bg-rose-600 text-white',
          dot: 'bg-rose-600',
        };
      case 'HIGH':
        return {
          bg: 'bg-rose-50/50',
          border: 'border-rose-100',
          badge: 'bg-rose-500 text-white',
          dot: 'bg-rose-500',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-50/50',
          border: 'border-amber-100',
          badge: 'bg-amber-500 text-white',
          dot: 'bg-amber-500',
        };
      default:
        return {
          bg: 'bg-sky-50/50',
          border: 'border-sky-100',
          badge: 'bg-sky-500 text-white',
          dot: 'bg-sky-500',
        };
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500" />
          <h3 className="font-bold text-xs text-slate-800 tracking-tight">
            Recent Alerts &amp; Incidents
          </h3>
        </div>
        {onViewAll && (
          <button
            onClick={onViewAll}
            className="text-[11px] font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 transition"
          >
            View All <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Alerts Timeline List */}
      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-0.5">
        {activeAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-6 text-center text-slate-400">
            <ShieldCheck className="w-8 h-8 text-emerald-500 mb-1.5" />
            <p className="text-xs font-semibold text-slate-700">All Zones Clear</p>
            <p className="text-[10px] text-slate-400">No active incidents or PPE violations</p>
          </div>
        ) : (
          activeAlerts.slice(0, 5).map((alert) => {
            const config = getSeverityConfig(alert.severity);
            const timeStr = formatTimestamp(alert.timestamp);

            return (
              <div
                key={alert.alert_id}
                className={`p-2.5 rounded-lg border ${config.border} ${config.bg} flex items-start gap-2.5 transition hover:shadow-sm`}
              >
                <span className={`w-2 h-2 rounded-full ${config.dot} mt-1 flex-shrink-0`} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono-nums text-[10px] text-slate-500">{timeStr}</span>
                    <span
                      className={`${config.badge} font-bold text-[8px] px-1.5 py-0.5 rounded tracking-wide`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-[9px] font-medium text-slate-400 ml-auto">
                      {alert.status}
                    </span>
                  </div>

                  <div
                    onClick={() => onSelectAlert?.(alert)}
                    className="font-bold text-slate-800 text-[11px] mt-0.5 truncate cursor-pointer hover:text-sky-600 transition"
                    title={alert.title}
                  >
                    {alert.title || alert.event_type.replace(/_/g, ' ')}
                  </div>

                  <p className="text-[10px] text-slate-500 leading-snug line-clamp-2 mt-0.5">
                    {alert.message || 'Safety anomaly flagged by edge AI engine.'}
                  </p>

                  <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-200/60">
                    <p className="text-[9px] text-slate-400 font-mono-nums truncate max-w-[130px]">
                      {alert.camera_id} • {alert.zone_id}
                    </p>

                    {/* Operational Action Buttons */}
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {alert.status === 'ACTIVE' && onAcknowledge && (
                        <button
                          onClick={() => onAcknowledge(alert.alert_id)}
                          className="px-2 py-0.5 bg-amber-500 hover:bg-amber-600 text-white text-[9px] font-semibold rounded shadow-xs transition cursor-pointer"
                        >
                          Ack
                        </button>
                      )}
                      {alert.status !== 'RESOLVED' && onResolve && (
                        <button
                          onClick={() => onResolve(alert.alert_id)}
                          className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[9px] font-semibold rounded shadow-xs transition cursor-pointer"
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
