/**
 * HazardStatusPanel.tsx — SafeSync Phase 8
 * Real-time Fire & Smoke hazard monitoring panel for configured zones.
 */

import React from 'react';
import { Flame, CloudRain, ShieldCheck, MapPin } from 'lucide-react';
import { HazardEventDetail, HazardState } from '../types';

interface HazardStatusPanelProps {
  hazards: HazardEventDetail[];
  monitoredZones?: { zone_id: string; name: string }[];
}

export const HazardStatusPanel: React.FC<HazardStatusPanelProps> = ({
  hazards,
  monitoredZones = [
    { zone_id: 'FAB_BAY_01', name: 'Fabrication Bay' },
    { zone_id: 'PAINT_COAT_02', name: 'Paint & Coating Area' },
    { zone_id: 'CHEM_STORE_03', name: 'Chemical Storage' },
    { zone_id: 'ASSEMBLY_B_04', name: 'Assembly Line B' },
  ],
}) => {
  const getZoneHazard = (zoneId: string) => {
    return hazards.find((h) => h.zone_id === zoneId);
  };

  const getHazardStateBadge = (state: HazardState) => {
    switch (state) {
      case 'CONFIRMED':
        return <span className="badge badge-error">CONFIRMED HAZARD</span>;
      case 'ACTIVE':
        return <span className="badge badge-error">ACTIVE HAZARD</span>;
      case 'DETECTING':
        return <span className="badge badge-warning">DETECTING (CONFIRMING)</span>;
      case 'CANDIDATE':
        return <span className="badge badge-info">CANDIDATE (EVALUATING)</span>;
      case 'CLEARING':
        return <span className="badge badge-neutral">CLEARING</span>;
      case 'CLEARED':
        return <span className="badge badge-info">RECENTLY CLEARED</span>;
      case 'SUSPECTED':
        return <span className="badge badge-warning">SUSPECTED (VERIFYING)</span>;
      default:
        return <span className="badge badge-success">ZONE CLEAR</span>;
    }
  };

  return (
    <div className="hazard-panel-container">
      <div className="hazard-zone-grid">
        {monitoredZones.map((z) => {
          const hazard = getZoneHazard(z.zone_id);
          const state: HazardState = hazard ? hazard.state : 'NO_HAZARD';
          const isCritical = state === 'CONFIRMED' || state === 'ACTIVE';
          const isWarning = state === 'DETECTING' || state === 'SUSPECTED';
          const isCandidate = state === 'CANDIDATE';

          return (
            <div
              key={z.zone_id}
              className={`hazard-zone-card ${
                isCritical ? 'hazard-critical' : isWarning ? 'hazard-warning' : isCandidate ? 'hazard-evaluating' : 'hazard-clear'
              }`}
            >
              <div className="zone-card-header">
                <div className="zone-info">
                  <span className="zone-name">{z.name}</span>
                  <span className="zone-id">
                    <MapPin size={12} /> {z.zone_id}
                  </span>
                </div>
                <div className="zone-state-badge">{getHazardStateBadge(state)}</div>
              </div>

              <div className="zone-card-body">
                {hazard ? (
                  <div className="hazard-detail-row">
                    <div className="hazard-type-icon">
                      {hazard.hazard_type === 'fire' ? (
                        <Flame size={28} className="text-fire animate-pulse" />
                      ) : (
                        <CloudRain size={28} className="text-smoke" />
                      )}
                    </div>
                    <div className="hazard-stats">
                      <div className="hazard-type-label">
                        {hazard.hazard_type.toUpperCase()} DETECTED
                      </div>
                      <div className="hazard-conf">
                        Confidence: {(hazard.confidence * 100).toFixed(1)}%
                      </div>
                      {hazard.persistence_frames && (
                        <div className="hazard-frames">
                          Persistence: {hazard.persistence_frames} frames
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="hazard-clear-row">
                    <ShieldCheck size={26} className="text-success" />
                    <div>
                      <div className="clear-text">No Thermal / Smoke Signature</div>
                      <div className="clear-subtext">Continuous real-time optical scan</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
