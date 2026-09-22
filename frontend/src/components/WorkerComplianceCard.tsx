/**
 * WorkerComplianceCard.tsx — RAKSHYA VISION Phase 8
 * Displays anonymous worker tracking state, PPE confirmation checklist, and compliance status.
 * Strictly maintains visual distinction between PRESENT, ABSENT, and UNKNOWN (occluded).
 */

import React from 'react';
import {
  User,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  HardHat,
  Shirt,
  Hand,
  Footprints,
  MapPin,
  Clock,
} from 'lucide-react';
import { WorkerTrack, PPEPresence } from '../types';

interface WorkerComplianceCardProps {
  worker: WorkerTrack;
}

export const WorkerComplianceCard: React.FC<WorkerComplianceCardProps> = ({ worker }) => {
  const renderPpeBadge = (label: string, icon: React.ReactNode, status: PPEPresence) => {
    let badgeClass = 'ppe-unknown';
    let text = 'UNKNOWN';
    let tooltip = 'Occluded or insufficient evidence to confirm presence/absence';

    if (status === 'PRESENT') {
      badgeClass = 'ppe-present';
      text = 'CONFIRMED PRESENT';
      tooltip = 'Confirmed worn across required temporal frames';
    } else if (status === 'ABSENT') {
      badgeClass = 'ppe-absent';
      text = 'CONFIRMED ABSENT';
      tooltip = 'Confirmed missing — safety violation logged';
    }

    return (
      <div className={`ppe-item-badge ${badgeClass}`} title={tooltip}>
        <div className="ppe-item-icon">{icon}</div>
        <div className="ppe-item-info">
          <span className="ppe-item-name">{label}</span>
          <span className="ppe-item-status">{text}</span>
        </div>
      </div>
    );
  };

  const isCompliant = worker.overall_compliant;
  const ppe = worker.ppe_status || { helmet: 'UNKNOWN', safety_vest: 'UNKNOWN', gloves: 'UNKNOWN', safety_footwear: 'UNKNOWN' };
  const hasUnknown = Object.values(ppe).some((s) => s === 'UNKNOWN');

  const bboxDisplay = Array.isArray(worker.bbox)
    ? worker.bbox.map((v) => Math.round(Number(v) || 0)).join(', ')
    : typeof worker.bbox === 'object' && worker.bbox !== null
    ? `${Math.round((worker.bbox as any).x1 || 0)}, ${Math.round((worker.bbox as any).y1 || 0)}, ${Math.round((worker.bbox as any).x2 || 0)}, ${Math.round((worker.bbox as any).y2 || 0)}`
    : 'N/A';

  return (
    <div className={`worker-card ${isCompliant ? 'card-compliant' : 'card-non-compliant'}`}>
      {/* Header */}
      <div className="worker-card-header">
        <div className="worker-id-group">
          <div className="worker-avatar">
            <User size={18} />
          </div>
          <div>
            <h4 className="worker-id-title">Worker #{worker.track_id}</h4>
            <div className="worker-meta-row">
              {worker.zone_id && (
                <span className="worker-zone">
                  <MapPin size={12} /> {worker.zone_id}
                </span>
              )}
              <span className="worker-persistence">
                <Clock size={12} /> {worker.active_frames} frames
              </span>
            </div>
          </div>
        </div>

        {/* Overall Status Badge */}
        <div>
          {isCompliant ? (
            <span className="badge badge-success">
              <ShieldCheck size={14} /> COMPLIANT
            </span>
          ) : (
            <span className="badge badge-error">
              <ShieldAlert size={14} /> VIOLATION
            </span>
          )}
          {hasUnknown && (
            <span
              className="badge badge-neutral ml-1"
              title="Contains occluded/unknown PPE items"
            >
              <HelpCircle size={12} /> UNKNOWN ITEMS
            </span>
          )}
        </div>
      </div>

      {/* PPE Checklist Grid */}
      <div className="ppe-grid">
        {renderPpeBadge('Hard Hat', <HardHat size={16} />, ppe.helmet || 'UNKNOWN')}
        {renderPpeBadge('Safety Vest', <Shirt size={16} />, ppe.safety_vest || 'UNKNOWN')}
        {renderPpeBadge('Safety Gloves', <Hand size={16} />, ppe.gloves || 'UNKNOWN')}
        {renderPpeBadge('Safety Footwear', <Footprints size={16} />, ppe.safety_footwear || 'UNKNOWN')}
      </div>

      {/* Bounding Box Info */}
      <div className="worker-card-footer">
        <span className="text-muted font-mono text-xs">
          BBOX: [{bboxDisplay}]
        </span>
      </div>
    </div>
  );
};
