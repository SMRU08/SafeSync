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
  const hasUnknown = Object.values(worker.ppe_status).some((s) => s === 'UNKNOWN');

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
        {renderPpeBadge('Hard Hat', <HardHat size={16} />, worker.ppe_status.helmet)}
        {renderPpeBadge('Safety Vest', <Shirt size={16} />, worker.ppe_status.safety_vest)}
        {renderPpeBadge('Safety Gloves', <Hand size={16} />, worker.ppe_status.gloves)}
        {renderPpeBadge('Safety Footwear', <Footprints size={16} />, worker.ppe_status.safety_footwear)}
      </div>

      {/* Bounding Box Info */}
      <div className="worker-card-footer">
        <span className="text-muted font-mono text-xs">
          BBOX: [{worker.bbox.map((v) => Math.round(v)).join(', ')}]
        </span>
      </div>
    </div>
  );
};
