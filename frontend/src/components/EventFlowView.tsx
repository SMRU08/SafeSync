/**
 * EventFlowView.tsx — SafeSync Industrial SOC
 * Operational End-to-End Safety Event Flow Visualization (Phase 8, 13, 28).
 * Tracks causality from Camera Frame → AI Inference → Temporal Gate → Incident → Alert → Action.
 */

import React from 'react';
import {
  Camera,
  Cpu,
  Layers,
  ShieldAlert,
  Bell,
  CheckCircle2,
  Clock,
  ArrowRight,
  Flame,
  HardHat,
} from 'lucide-react';
import { Incident, Alert } from '../types';

interface EventFlowViewProps {
  incident?: Incident | null;
  alert?: Alert | null;
  className?: string;
}

export const EventFlowView: React.FC<EventFlowViewProps> = ({
  incident,
  alert,
  className = '',
}) => {
  const cameraId = incident?.camera_id || alert?.camera_id || 'CAM-01';
  const zoneId = incident?.zone_id || alert?.zone_id || 'production_floor';
  const eventType = (incident?.event_types?.[0] || alert?.event_type || 'PPE_VIOLATION').toUpperCase();
  const severity = incident?.risk_level || alert?.severity || 'MEDIUM';
  const status = alert?.status || incident?.status || 'OPEN';

  const isFireOrSmoke = eventType.includes('FIRE') || eventType.includes('SMOKE');
  const isHelmet = eventType.includes('HELMET');
  const isVest = eventType.includes('VEST');

  const getSeverityColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
      case 'HIGH':
        return 'text-orange-400 border-orange-500/40 bg-orange-500/10';
      case 'MEDIUM':
        return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
      default:
        return 'text-sky-400 border-sky-500/40 bg-sky-500/10';
    }
  };

  const steps = [
    {
      title: 'Camera Ingest',
      subtitle: `${cameraId.toUpperCase()} (${zoneId})`,
      icon: Camera,
      badge: 'Frame Captured',
      badgeColor: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
      desc: 'Raw video stream ingestion with RTSP/HTTP decoding',
    },
    {
      title: 'AI Detection',
      subtitle: isFireOrSmoke
        ? (eventType.includes('FIRE') ? 'Active Flame Detection' : 'Atmospheric Smoke Detection')
        : (isHelmet ? 'Worker Head ROI Analysis' : isVest ? 'Torso High-Vis Evaluation' : 'Worker PPE Inspection'),
      icon: isFireOrSmoke ? Flame : isHelmet ? HardHat : Cpu,
      badge: 'Single-Pass YOLO',
      badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      desc: 'Bounding box segmentation & class confidence scoring',
    },
    {
      title: 'Temporal Gate',
      subtitle: 'ByteTrack Multi-Frame Lock',
      icon: Layers,
      badge: 'Validated (>=2 frames)',
      badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      desc: 'False-positive rejection via temporal persistence gate',
    },
    {
      title: 'Incident Evaluation',
      subtitle: `Risk Level: ${severity}`,
      icon: ShieldAlert,
      badge: `Score: ${incident?.risk_score ?? 75}`,
      badgeColor: getSeverityColor(severity),
      desc: 'Risk matrix correlation & environmental weighting',
    },
    {
      title: 'Alert Dispatch',
      subtitle: isFireOrSmoke ? 'P0/P1 Emergency Alert' : 'P2 Visual Violation Alert',
      icon: Bell,
      badge: 'WebSocket & Audio',
      badgeColor: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      desc: 'Real-time broadcast to SOC consoles and on-site speaker',
    },
    {
      title: 'Operator Triage',
      subtitle: status === 'RESOLVED' ? 'Incident Resolved' : status === 'ACKNOWLEDGED' ? 'Operator Investigating' : 'Pending Action',
      icon: status === 'RESOLVED' ? CheckCircle2 : Clock,
      badge: status,
      badgeColor: status === 'RESOLVED' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30',
      desc: 'Audit trail logging with tamper-proof evidence link',
    },
  ];

  return (
    <div className={`p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-sky-400" />
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Operational Event Causality Flow
          </h4>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          Trace: {incident?.incident_id?.slice(0, 8) || alert?.alert_id?.slice(0, 8) || 'active-event'}
        </span>
      </div>

      {/* Responsive Horizontal / Vertical Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-2 pt-1">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div key={idx} className="relative flex flex-col justify-between p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700/80 transition-all">
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <div className="w-6 h-6 rounded-md bg-slate-800/90 flex items-center justify-center text-slate-300">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className={`text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded border ${step.badgeColor}`}>
                    {step.badge}
                  </span>
                </div>
                <h5 className="text-[11px] font-bold text-slate-200 leading-tight">{step.title}</h5>
                <p className="text-[10px] text-sky-400 font-medium truncate mt-0.5">{step.subtitle}</p>
                <p className="text-[9px] text-slate-400 leading-snug mt-1.5 line-clamp-2">{step.desc}</p>
              </div>

              {idx < steps.length - 1 && (
                <div className="hidden md:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-slate-600 pointer-events-none">
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EventFlowView;
