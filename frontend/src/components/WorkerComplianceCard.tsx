/**
 * WorkerComplianceCard.tsx — RAKSHYA VISION Professional SOC
 * Enhanced Worker Profile Card with Itemized PPE Status, Dwell Time,
 * Compliance Health Score, and Detailed Inspection Trigger.
 */

import React from 'react';
import {
  User,
  ShieldCheck,
  ShieldAlert,
  HardHat,
  Shirt,
  Hand,
  Footprints,
  MapPin,
  Clock,
  Eye,
  Check,
  X,
  Minus,
} from 'lucide-react';
import { WorkerTrack, PPEPresence } from '../types';

interface WorkerComplianceCardProps {
  worker: WorkerTrack;
  onInspect?: (worker: WorkerTrack) => void;
}

export const WorkerComplianceCard: React.FC<WorkerComplianceCardProps> = ({ worker, onInspect }) => {
  const ppe = worker.ppe_status || {
    helmet: 'UNKNOWN',
    safety_vest: 'UNKNOWN',
    gloves: 'UNKNOWN',
    safety_footwear: 'UNKNOWN',
  };

  // Calculate compliance score based on verified PPE items
  const items = [ppe.helmet, ppe.safety_vest, ppe.gloves, ppe.safety_footwear];
  const presentCount = items.filter((s) => s === 'PRESENT').length;
  const absentCount = items.filter((s) => s === 'ABSENT').length;
  const complianceScore = Math.round((presentCount / items.length) * 100);
  const isCompliant = worker.overall_compliant;

  // Calculate dwell time in seconds / minutes
  const totalSeconds = worker.dwell_seconds ?? Math.round((worker.active_frames || 1) / 30);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const dwellDisplay = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

  const renderBadge = (label: string, icon: React.ReactNode, status?: PPEPresence) => {
    let bg = 'bg-slate-50 border-slate-200 text-slate-500';
    let iconColor = 'text-slate-400';
    let badge = <Minus className="w-2.5 h-2.5" />;
    let text = 'Unknown';

    if (status === 'PRESENT') {
      bg = 'bg-emerald-50 border-emerald-200 text-emerald-800';
      iconColor = 'text-emerald-600';
      badge = <Check className="w-2.5 h-2.5" />;
      text = 'Present';
    } else if (status === 'ABSENT') {
      bg = 'bg-rose-50 border-rose-200 text-rose-800';
      iconColor = 'text-rose-600';
      badge = <X className="w-2.5 h-2.5" />;
      text = 'Absent';
    }

    return (
      <div className={`p-2 rounded-lg border ${bg} flex items-center justify-between transition`}>
        <div className="flex items-center gap-2">
          <span className={iconColor}>{icon}</span>
          <span className="text-xs font-medium text-slate-700">{label}</span>
        </div>
        <span className="inline-flex items-center gap-1 text-[10px] font-bold tracking-tight">
          {badge}
          {text}
        </span>
      </div>
    );
  };

  return (
    <div
      onClick={() => onInspect?.(worker)}
      className={`bg-white rounded-xl border transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer overflow-hidden flex flex-col justify-between ${
        isCompliant
          ? 'border-slate-200 hover:border-emerald-300'
          : 'border-rose-200 hover:border-rose-400 ring-1 ring-rose-100'
      }`}
    >
      {/* Header Bar */}
      <div className="p-3.5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs ${
              isCompliant ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
            }`}
          >
            <User className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-extrabold text-slate-900 text-sm tracking-tight">
                Worker #{worker.track_id.toString().padStart(3, '0')}
              </h4>
              <span
                className={`w-2 h-2 rounded-full ${
                  isCompliant ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500 animate-bounce'
                }`}
              />
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
              <span className="flex items-center gap-0.5">
                <MapPin className="w-3 h-3 text-slate-400" />
                {worker.zone_id || 'Production Floor'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-0.5 font-mono-nums">
                <Clock className="w-3 h-3 text-slate-400" />
                {dwellDisplay}
              </span>
            </div>
          </div>
        </div>

        {/* Overall Status Badge */}
        <div className="text-right">
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wide uppercase ${
              isCompliant
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-rose-100 text-rose-800 border border-rose-300'
            }`}
          >
            {isCompliant ? (
              <>
                <ShieldCheck className="w-3 h-3 text-emerald-600" /> COMPLIANT
              </>
            ) : (
              <>
                <ShieldAlert className="w-3 h-3 text-rose-600" /> VIOLATION
              </>
            )}
          </span>
          <div className="text-[10px] text-slate-400 font-mono-nums mt-0.5">
            {complianceScore}% Verified ({presentCount}/4)
          </div>
        </div>
      </div>

      {/* PPE Grid Checklist */}
      <div className="p-3.5 space-y-1.5 flex-1">
        <div className="grid grid-cols-2 gap-1.5">
          {renderBadge('Helmet', <HardHat className="w-3.5 h-3.5" />, ppe.helmet)}
          {renderBadge('Vest', <Shirt className="w-3.5 h-3.5" />, ppe.safety_vest)}
          {renderBadge('Gloves', <Hand className="w-3.5 h-3.5" />, ppe.gloves)}
          {renderBadge('Shoes', <Footprints className="w-3.5 h-3.5" />, ppe.safety_footwear)}
        </div>

        {/* Missing Items Warning if any */}
        {absentCount > 0 && (
          <div className="mt-2.5 px-2.5 py-1.5 rounded-md bg-rose-50/80 border border-rose-200 text-[11px] text-rose-800 flex items-center justify-between">
            <span className="font-semibold">Missing Equipment:</span>
            <span className="font-bold text-rose-600">
              {[
                ppe.helmet === 'ABSENT' && 'Helmet',
                ppe.safety_vest === 'ABSENT' && 'Vest',
                ppe.gloves === 'ABSENT' && 'Gloves',
                ppe.safety_footwear === 'ABSENT' && 'Shoes',
              ]
                .filter(Boolean)
                .join(', ')}
            </span>
          </div>
        )}
      </div>

      {/* Card Footer */}
      <div className="px-3.5 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-400">
          Frames: <strong className="text-slate-600">{worker.active_frames || 1}</strong>
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onInspect?.(worker);
          }}
          className="text-[11px] font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 transition"
        >
          <Eye className="w-3 h-3" /> Inspect History
        </button>
      </div>
    </div>
  );
};

export default WorkerComplianceCard;
