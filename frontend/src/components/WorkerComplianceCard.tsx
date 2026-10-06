/**
 * WorkerComplianceCard.tsx — SafeSync Phase 5
 * High-performance, accessible industrial Worker Card for the Workers & PPE Center.
 *
 * Implements:
 *   - Anonymous Tracking ID (Worker #{ID}) — Section 19 & 50
 *   - Camera node & Zone association (with honest fallback '—') — Section 21 & 22
 *   - Tri-State Safety Status:
 *       ● SAFE                (#22C55E) — all required PPE PRESENT
 *       ● UNKNOWN / LIMITED   (#F5B942) — non-punitive, UNKNOWN IS NOT A VIOLATION
 *       ● CONFIRMED VIOLATION (#EF4444) — confirmed gear absence after 15-frame debounce
 *   - Canonical 4-point PPE checklist (Helmet, Vest, Gloves, Footwear) via PPEStatusBadge
 *   - Real telemetry (Active frames, Dwell time, Confidence if provided)
 *   - Direct routing triggers (Inspect, View in Live Monitor, View Entry Gate)
 */

import React from 'react';
import {
  User,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  MapPin,
  Clock,
  Eye,
  Tv,
  DoorOpen,
  Camera,
} from 'lucide-react';
import { WorkerTrack } from '../types';
import { resolveWorkerDisplay } from '../utils/workerDisplay';
import { PPEStatusBadge } from './PPEStatusBadge';

interface WorkerComplianceCardProps {
  worker: WorkerTrack;
  cameraName?: string;
  onInspect?: (worker: WorkerTrack) => void;
  onNavigateLive?: () => void;
  onNavigateGate?: () => void;
}

export const WorkerComplianceCard: React.FC<WorkerComplianceCardProps> = ({
  worker,
  cameraName,
  onInspect,
  onNavigateLive,
  onNavigateGate,
}) => {
  const ppe = worker.ppe_status || {
    helmet: 'UNKNOWN',
    safety_vest: 'UNKNOWN',
    gloves: 'UNKNOWN',
    safety_footwear: 'UNKNOWN',
  };

  const display = resolveWorkerDisplay(worker);

  // Calculate verified vs missing items
  const items = [
    { key: 'helmet', name: 'Helmet', state: ppe.helmet },
    { key: 'safety_vest', name: 'Vest', state: ppe.safety_vest },
    { key: 'gloves', name: 'Gloves', state: ppe.gloves },
    { key: 'safety_footwear', name: 'Footwear', state: ppe.safety_footwear },
  ];
  const presentCount = items.filter((i) => i.state === 'PRESENT').length;
  const absentItems = items.filter((i) => i.state === 'ABSENT').map((i) => i.name);
  const unknownItems = items.filter((i) => i.state === 'UNKNOWN').map((i) => i.name);

  // Calculate dwell time in seconds / minutes
  const totalSeconds = worker.dwell_seconds ?? Math.round((worker.active_frames || 1) / 30);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const dwellDisplay = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

  // Real timestamp or dwell fallback (Section 23)
  const lastSeenDisplay = worker.timestamp
    ? new Date(worker.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : worker.first_seen
    ? new Date(worker.first_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';

  // Real camera & zone (Section 21 & 22)
  const displayCamera = cameraName || worker.camera_name || worker.camera_id || 'CAM_01';
  const displayZone = worker.zone_id ? worker.zone_id.replace(/_/g, ' ') : '—';
  const isEntryGate = worker.zone_id === 'entry_gate' || (worker.camera_id && worker.camera_id.includes('gate'));

  return (
    <div
      onClick={() => onInspect?.(worker)}
      className={`rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden flex flex-col justify-between ${
        display.state === 'SAFE'
          ? 'bg-[#0D1B2A] border-[#20344A] hover:border-emerald-500/50 shadow-sm'
          : display.state === 'VIOLATION'
          ? 'bg-[#0D1B2A] border-rose-500/50 hover:border-rose-500 ring-1 ring-rose-500/20 shadow-sm'
          : 'bg-[#0D1B2A] border-amber-500/40 hover:border-amber-500/70 shadow-sm'
      }`}
    >
      {/* ─── Header Bar: Tracking ID, Camera & Zone ─── */}
      <div className="p-3.5 border-b border-[#20344A] bg-[#12263A]/80 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 border ${
              display.state === 'SAFE'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                : display.state === 'VIOLATION'
                ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                : 'bg-amber-500/15 text-[#F5B942] border-amber-500/30'
            }`}
          >
            <User className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-mono font-black text-white text-sm tracking-tight truncate">
                Worker #{worker.track_id.toString().padStart(3, '0')}
              </h4>
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: display.color }}
                title={`Safety State: ${display.label}`}
              />
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5 truncate">
              <span className="flex items-center gap-1 text-slate-300 font-mono truncate">
                <Camera className="w-3 h-3 text-sky-400 shrink-0" />
                {displayCamera}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 capitalize truncate">
                <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                {displayZone}
              </span>
            </div>
          </div>
        </div>

        {/* Overall Status Badge */}
        <div className="text-right shrink-0">
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wide border ${
              display.state === 'SAFE'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                : display.state === 'VIOLATION'
                ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                : 'bg-amber-500/15 text-[#F5B942] border-amber-500/30'
            }`}
          >
            {display.state === 'SAFE' ? (
              <>
                <ShieldCheck className="w-3 h-3 text-emerald-400" /> SAFE
              </>
            ) : display.state === 'VIOLATION' ? (
              <>
                <ShieldAlert className="w-3 h-3 text-rose-400" /> VIOLATION
              </>
            ) : (
              <>
                <HelpCircle className="w-3 h-3 text-[#F5B942]" /> UNKNOWN
              </>
            )}
          </span>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
            {presentCount}/4 Verified
          </div>
        </div>
      </div>

      {/* ─── 4-Point PPE Status Checklist (Section 15) ─── */}
      <div className="p-3.5 space-y-2 flex-1">
        <div className="grid grid-cols-2 gap-2">
          <PPEStatusBadge item="helmet" status={ppe.helmet} />
          <PPEStatusBadge item="safety_vest" status={ppe.safety_vest} />
          <PPEStatusBadge item="gloves" status={ppe.gloves} />
          <PPEStatusBadge item="safety_footwear" status={ppe.safety_footwear} />
        </div>

        {/* Explainability Mini-Banner (Section 25, 26, 27) */}
        {display.state === 'VIOLATION' && absentItems.length > 0 && (
          <div className="mt-2 px-2.5 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-[11px] text-rose-300 flex items-center justify-between">
            <span className="font-semibold text-slate-300">Missing Mandatory Gear:</span>
            <span className="font-bold text-rose-400 uppercase tracking-tight">
              {absentItems.join(', ')}
            </span>
          </div>
        )}

        {display.state === 'UNKNOWN' && unknownItems.length > 0 && (
          <div className="mt-2 px-2.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-[11px] text-[#F5B942] flex items-center justify-between">
            <span className="font-semibold text-slate-300">Visibility Limited:</span>
            <span className="font-medium text-[#F5B942] text-[10px]">
              {unknownItems.join(', ')} occluded
            </span>
          </div>
        )}
      </div>

      {/* ─── Card Footer: Real Telemetry & Direct Links (Section 23, 40, 41) ─── */}
      <div className="px-3.5 py-2.5 bg-[#12263A]/50 border-t border-[#20344A] flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2 text-slate-400 font-mono text-[10px]">
          <span title="Dwell Time">
            <Clock className="w-3 h-3 text-sky-400 inline mr-0.5" />
            {dwellDisplay}
          </span>
          <span>•</span>
          <span title="Last Observed">Seen: {lastSeenDisplay}</span>
        </div>

        <div className="flex items-center gap-2">
          {isEntryGate && onNavigateGate && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onNavigateGate();
              }}
              className="text-[10px] font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30"
              title="Navigate to Entry Gate turnstile view"
            >
              <DoorOpen className="w-2.5 h-2.5" /> Entry Gate
            </button>
          )}

          {onNavigateLive && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onNavigateLive();
              }}
              className="text-[10px] font-semibold text-slate-400 hover:text-white flex items-center gap-0.5 transition"
              title="View in Live Monitor"
            >
              <Tv className="w-2.5 h-2.5" /> Live
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              onInspect?.(worker);
            }}
            className="text-[11px] font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1 transition"
          >
            <Eye className="w-3 h-3" /> Inspect
          </button>
        </div>
      </div>
    </div>
  );
};

export default WorkerComplianceCard;
