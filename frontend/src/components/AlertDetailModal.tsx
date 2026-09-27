/**
 * AlertDetailModal.tsx — SafeSync Phase 8 & Master Redesign
 * Detailed audit view for a safety alert including EventFlowView causality pipeline,
 * audit history trail, and operator triage actions.
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  AlertTriangle,
  Clock,
  MapPin,
  Camera,
  History,
  Check,
} from 'lucide-react';
import { Alert } from '../types';
import { fetchAlertDetail } from '../services/api';
import { EventFlowView } from './EventFlowView';

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
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  useEffect(() => {
    if (alert) {
      setFullAlert(alert);
      fetchAlertDetail(alert.alert_id)
        .then((data) => setFullAlert(data))
        .catch(() => {});
    }
  }, [alert]);

  if (!alert || !fullAlert) return null;

  const handleAction = async (action: 'ack' | 'resolve' | 'dismiss') => {
    setActionInProgress(action);
    try {
      if (action === 'ack') await onAcknowledge(fullAlert.alert_id);
      if (action === 'resolve') await onResolve(fullAlert.alert_id);
      if (action === 'dismiss') await onDismiss(fullAlert.alert_id);
      const updated = await fetchAlertDetail(fullAlert.alert_id);
      setFullAlert(updated);
    } finally {
      setActionInProgress(null);
    }
  };

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/15 border-rose-500/30';
      case 'HIGH':
        return 'text-orange-400 bg-orange-500/15 border-orange-500/30';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-500/15 border-amber-500/30';
      default:
        return 'text-sky-400 bg-sky-500/15 border-sky-500/30';
    }
  };

  const getStatusBadgeClass = (st: string) => {
    switch (st) {
      case 'ACTIVE':
        return 'text-rose-400 bg-rose-500/15 border-rose-500/30';
      case 'ACKNOWLEDGED':
        return 'text-amber-400 bg-amber-500/15 border-amber-500/30';
      case 'RESOLVED':
        return 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 select-none animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl bg-[#0c1424] text-slate-100 rounded-2xl shadow-2xl border border-slate-800 overflow-hidden flex flex-col my-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-white text-base">
                  {fullAlert.alert_id.slice(0, 12)}...
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase border ${getSeverityBadgeClass(
                    fullAlert.severity
                  )}`}
                >
                  {fullAlert.severity}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getStatusBadgeClass(
                    fullAlert.status
                  )}`}
                >
                  {fullAlert.status}
                </span>
              </div>
              <h3 className="text-xs font-semibold text-slate-400 mt-0.5">
                {fullAlert.title}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[calc(85vh-140px)]">
          {/* Metadata Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Camera</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1 font-mono-nums">
                <Camera className="w-3.5 h-3.5 text-sky-400" />
                {fullAlert.camera_id}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Plant Zone</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-sky-400" />
                {fullAlert.zone_id || 'production_floor'}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Timestamp</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1 font-mono-nums">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                {new Date(fullAlert.timestamp).toLocaleTimeString()}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Linked Incident</span>
              <button
                onClick={() => {
                  if (onSelectIncident) {
                    onSelectIncident(fullAlert.incident_id);
                    onClose();
                  }
                }}
                className="text-xs font-bold text-sky-400 hover:text-sky-300 mt-1 flex items-center gap-1 font-mono underline"
              >
                {fullAlert.incident_id.slice(0, 8)}...
              </button>
            </div>
          </div>

          {/* Event Causality Flow Component */}
          <EventFlowView alert={fullAlert} />

          {/* Alert Message */}
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Operator Alert Message
            </span>
            <p className="text-slate-200 leading-relaxed font-medium">
              {fullAlert.message}
            </p>
          </div>

          {/* Audit History Timeline */}
          {fullAlert.history && fullAlert.history.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <History className="w-4 h-4 text-sky-400" />
                Audit Trail &amp; Operator Actions
              </h4>
              <div className="space-y-2">
                {fullAlert.history.map((h, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/80 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-200">{h.action}</span>
                      {h.reason && <span className="text-slate-400 text-[11px]">— {h.reason}</span>}
                    </div>
                    <span className="font-mono text-[10px] text-slate-500">
                      {new Date(h.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="px-6 py-3.5 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] text-slate-400 font-mono">
            Priority: <span className="text-white font-bold">{fullAlert.priority || 'P2'}</span>
          </div>

          <div className="flex items-center gap-2">
            {fullAlert.status === 'ACTIVE' && (
              <button
                onClick={() => handleAction('ack')}
                disabled={actionInProgress === 'ack'}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-xs font-semibold transition"
              >
                {actionInProgress === 'ack' ? 'Acknowledging...' : 'Acknowledge Alert'}
              </button>
            )}

            {fullAlert.status !== 'RESOLVED' && (
              <button
                onClick={() => handleAction('resolve')}
                disabled={actionInProgress === 'resolve'}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-md shadow-emerald-600/30"
              >
                <Check className="w-3.5 h-3.5" />
                {actionInProgress === 'resolve' ? 'Resolving...' : 'Resolve Alert'}
              </button>
            )}

            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertDetailModal;
