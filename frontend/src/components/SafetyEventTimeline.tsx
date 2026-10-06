/**
 * SafetyEventTimeline.tsx — SafeSync Industrial SOC
 * Phase 10: Unified Real-Time Safety Event Timeline & Audit Log.
 *
 * Provides chronological tracing of authentic safety events:
 * - Worker safety transitions (SAFE, UNKNOWN, CONFIRMED VIOLATION)
 * - Decoupled combustion hazards (P0 Fire & Smoke)
 * - Transparent explainability rationale for each state transition
 */

import React, { useState, useMemo } from 'react';
import {
  Clock,
  ShieldCheck,
  AlertTriangle,
  Flame,
  HelpCircle,
  Filter,
  CheckCircle2,
  Tv,
} from 'lucide-react';
import { Alert, HazardEventDetail } from '../types';

export interface TimelineEventItem {
  id: string;
  timestamp: string;
  timeFormatted: string;
  source: string;
  cameraId: string;
  zoneId?: string;
  category: 'PPE_SAFE' | 'PPE_UNKNOWN' | 'PPE_VIOLATION' | 'FIRE_SMOKE' | 'SYSTEM';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  title: string;
  explanation: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'NOMINAL';
}

interface SafetyEventTimelineProps {
  alerts?: Alert[];
  hazards?: HazardEventDetail[];
  customEvents?: TimelineEventItem[];
  maxItems?: number;
  onNavigateCamera?: (cameraId: string) => void;
}

export const SafetyEventTimeline: React.FC<SafetyEventTimelineProps> = ({
  alerts = [],
  hazards = [],
  customEvents,
  maxItems = 25,
  onNavigateCamera,
}) => {
  const [filterPriority, setFilterPriority] = useState<string>('ALL');

  // Convert alerts and hazards into unified timeline entries
  const timelineEvents = useMemo(() => {
    if (customEvents && customEvents.length > 0) {
      return customEvents;
    }

    const items: TimelineEventItem[] = [];

    // Map Alerts
    alerts.forEach((alt) => {
      const isFireSmoke = alt.event_type.includes('FIRE') || alt.event_type.includes('SMOKE');
      const isPPE = alt.event_type.includes('HELMET') || alt.event_type.includes('VEST') || alt.event_type.includes('GLOVE') || alt.event_type.includes('FOOTWEAR');
      
      let category: TimelineEventItem['category'] = 'SYSTEM';
      let priority: TimelineEventItem['priority'] = 'P3';
      let explanation = alt.message || 'Safety event logged by SOC monitor.';

      if (isFireSmoke) {
        category = 'FIRE_SMOKE';
        priority = 'P0';
        explanation = 'Combustion or atmospheric plume confirmed by decoupled thermal pipeline.';
      } else if (alt.severity === 'CRITICAL') {
        category = 'PPE_VIOLATION';
        priority = 'P0';
        explanation = 'Critical safety threshold exceeded in high-risk perimeter.';
      } else if (alt.severity === 'HIGH') {
        category = 'PPE_VIOLATION';
        priority = 'P1';
        explanation = 'Severe compliance infraction requiring immediate intervention.';
      } else if (isPPE) {
        category = 'PPE_VIOLATION';
        priority = 'P2';
        explanation = 'Required zone PPE confirmed absent after 15-frame temporal tolerance (~0.5s).';
      }

      const tDate = alt.timestamp ? new Date(alt.timestamp) : new Date();
      const timeFormatted = tDate.toLocaleTimeString('en-GB', { hour12: false });

      items.push({
        id: alt.alert_id,
        timestamp: alt.timestamp,
        timeFormatted,
        source: alt.camera_id || 'System Core',
        cameraId: alt.camera_id || 'cam_01',
        zoneId: alt.zone_id,
        category,
        priority: (alt.priority as any) || priority,
        title: alt.title || alt.event_type.replace(/_/g, ' '),
        explanation,
        status: (alt.status as any) || 'ACTIVE',
      });
    });

    // Map Active Hazards if any
    hazards.forEach((haz) => {
      if (haz.state === 'CONFIRMED' || haz.state === 'ACTIVE') {
        items.push({
          id: `haz_${haz.hazard_id}`,
          timestamp: new Date().toISOString(),
          timeFormatted: new Date().toLocaleTimeString('en-GB', { hour12: false }),
          source: haz.camera_id || 'Thermal Core',
          cameraId: haz.camera_id || 'cam_01',
          zoneId: haz.zone_id,
          category: 'FIRE_SMOKE',
          priority: 'P0',
          title: `${haz.hazard_type.toUpperCase()} CONFIRMED EMERGENCY`,
          explanation: `Multi-frame thermal debounce verified active ${haz.hazard_type} with confidence ${(haz.confidence * 100).toFixed(0)}%.`,
          status: 'ACTIVE',
        });
      }
    });

    // Sort descending by timestamp
    items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    return items;
  }, [alerts, hazards, customEvents]);

  const filteredItems = useMemo(() => {
    if (filterPriority === 'ALL') return timelineEvents.slice(0, maxItems);
    return timelineEvents.filter((item) => item.priority === filterPriority).slice(0, maxItems);
  }, [timelineEvents, filterPriority, maxItems]);

  const getPriorityBadge = (priority: TimelineEventItem['priority']) => {
    switch (priority) {
      case 'P0':
        return 'bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse';
      case 'P1':
        return 'bg-orange-500/20 text-orange-400 border border-orange-500/40';
      case 'P2':
        return 'bg-amber-500/20 text-amber-400 border border-amber-500/40';
      default:
        return 'bg-sky-500/10 text-sky-400 border border-sky-500/20';
    }
  };

  const getCategoryIcon = (category: TimelineEventItem['category']) => {
    switch (category) {
      case 'FIRE_SMOKE':
        return <Flame className="w-3.5 h-3.5 text-rose-500" />;
      case 'PPE_VIOLATION':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
      case 'PPE_UNKNOWN':
        return <HelpCircle className="w-3.5 h-3.5 text-amber-400" />;
      case 'PPE_SAFE':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-sky-400" />;
    }
  };

  return (
    <div className="glass-card p-4 space-y-3.5 select-none text-slate-100">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-sky-400" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Safety Event Timeline &amp; Decision Trace
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-800 text-slate-400">
            {timelineEvents.length} Events Logged
          </span>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-1 self-start sm:self-auto text-xs">
          <Filter className="w-3 h-3 text-slate-500 mr-1" />
          {(['ALL', 'P0', 'P1', 'P2', 'P3'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setFilterPriority(p)}
              className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold transition cursor-pointer ${
                filterPriority === p
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {filteredItems.length > 0 ? (
        <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition flex items-start gap-3 text-xs"
            >
              <div className="p-2 rounded bg-slate-900 border border-slate-800 shrink-0 mt-0.5">
                {getCategoryIcon(item.category)}
              </div>

              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 truncate">
                    <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-black ${getPriorityBadge(item.priority)}`}>
                      {item.priority}
                    </span>
                    <span className="font-bold text-white truncate">{item.title}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 shrink-0">
                    {item.timeFormatted}
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 leading-snug">
                  {item.explanation}
                </p>

                <div className="flex items-center justify-between pt-1 border-t border-slate-900 text-[10px] font-mono text-slate-500">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 font-bold">{item.source}</span>
                    {item.zoneId && <span>• Zone: {item.zoneId}</span>}
                  </div>

                  {onNavigateCamera && (
                    <button
                      onClick={() => onNavigateCamera(item.cameraId)}
                      className="text-sky-400 hover:text-sky-300 flex items-center gap-1 cursor-pointer font-sans text-[10px] font-semibold"
                    >
                      <Tv className="w-3 h-3" /> Live Feed
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 rounded-lg bg-slate-900/30 border border-slate-800 text-center space-y-1">
          <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto" />
          <div className="text-xs font-bold text-slate-300">Zero incidents in selected filter</div>
          <p className="text-[10px] text-slate-500">
            No events matching priority {filterPriority} have been recorded in the current session.
          </p>
        </div>
      )}
    </div>
  );
};

export default SafetyEventTimeline;
