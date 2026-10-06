/**
 * demoScenarios.ts — SafeSync Industrial SOC
 * Phase 10: Canonical Pre-Recorded Validation Scenarios.
 *
 * Implements the 5 canonical demonstration flows:
 *   1. Fully Equipped Worker (Green / Safe)
 *   2. Unknown State / Limited Visibility (Yellow / Unknown — Zero Penalty)
 *   3. Confirmed PPE Violation (Red / Violation after 15-frame tolerance)
 *   4. Multi-Worker Concurrent Independence (3 workers simultaneously)
 *   5. Decoupled Combustion Emergency (P0 Fire & Smoke)
 *
 * Safety rules:
 * - Purely client-side demo state
 * - Zero database writes
 * - Zero neural network weight or threshold modifications
 * - Clearly marked as DEMO MODE across the UI
 */

import { WorkerTrack, HazardEventDetail, Alert } from '../types';

export interface DemoScenarioData {
  id: string;
  name: string;
  title: string;
  subtitle: string;
  shortTitle: string;
  description: string;
  expectedSafetyState: string;
  toleranceFrames: number;
  highlightNote: string;
  workers: WorkerTrack[];
  hazards: HazardEventDetail[];
  alerts: Alert[];
  fireStatus: 'CLEAR' | 'DETECTED';
  smokeStatus: 'CLEAR' | 'DETECTED';
  explanation: string;
}

export const DEMO_SCENARIOS: Record<string, DemoScenarioData> = {
  safe_worker: {
    id: 'safe_worker',
    name: 'Scenario 1: Fully Equipped Worker (Compliant)',
    title: 'Fully Equipped Worker',
    subtitle: '100% Compliant — No Alarm',
    shortTitle: 'Fully Equipped Worker',
    description: 'Worker observed with Safety Helmet, High-Vis Vest, Gloves, and Safety Footwear verified on body zones.',
    expectedSafetyState: 'SAFE (Green)',
    toleranceFrames: 15,
    highlightNote: 'Continuous tracking with all 4 required PPE present',
    explanation: 'All required PPE is currently observed. Zero alerts created. Worker is safe to proceed.',
    fireStatus: 'CLEAR',
    smokeStatus: 'CLEAR',
    alerts: [],
    hazards: [],
    workers: [
      {
        track_id: 14,
        bbox: [180, 100, 360, 480],
        normalized_bbox: [0.28, 0.2, 0.56, 0.9],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'PRESENT',
          gloves: 'PRESENT',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: true,
        overall_status: 'COMPLIANT',
        active_frames: 180,
        dwell_seconds: 6.0,
        confidence: 0.94,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: [],
        is_partially_occluded: false,
      },
    ],
  },

  unknown_worker: {
    id: 'unknown_worker',
    name: 'Scenario 2: Unknown State / Limited Visibility',
    title: 'Unknown / Limited Visibility',
    subtitle: 'Neutral Evaluation — Zero Penalty',
    shortTitle: 'Unknown / Limited Visibility',
    description: 'Worker hand extremities occluded by industrial machinery. Neutral evaluation with zero false penalty.',
    expectedSafetyState: 'UNKNOWN (Yellow)',
    toleranceFrames: 15,
    highlightNote: 'Non-punitive handling: Occluded limbs do not trigger false alarms',
    explanation: 'Required PPE (Gloves) could not be conclusively evaluated because visibility is limited. UNKNOWN != VIOLATION.',
    fireStatus: 'CLEAR',
    smokeStatus: 'CLEAR',
    alerts: [],
    hazards: [],
    workers: [
      {
        track_id: 19,
        bbox: [210, 110, 390, 490],
        normalized_bbox: [0.32, 0.22, 0.6, 0.92],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'PRESENT',
          gloves: 'UNKNOWN',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: false,
        overall_status: 'UNKNOWN',
        active_frames: 90,
        dwell_seconds: 3.0,
        confidence: 0.89,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: [],
        is_partially_occluded: true,
      },
    ],
  },

  confirmed_violation: {
    id: 'confirmed_violation',
    name: 'Scenario 3: Confirmed PPE Violation (15-Frame Debounced)',
    title: 'Confirmed PPE Violation',
    subtitle: '15-Frame Debounced Tolerance',
    shortTitle: 'Confirmed PPE Violation',
    description: 'Worker cranial region clearly visible without head protection across 15 consecutive frames (~0.5s tolerance).',
    expectedSafetyState: 'CONFIRMED VIOLATION (Red)',
    toleranceFrames: 15,
    highlightNote: 'Only triggers after 15 consecutive absent frames (~0.5s)',
    explanation: 'Helmet absence confirmed after the 15-frame temporal debouncing period. P2 Alert generated.',
    fireStatus: 'CLEAR',
    smokeStatus: 'CLEAR',
    hazards: [],
    alerts: [
      {
        alert_id: 'demo_alt_v3_01',
        incident_id: 'demo_inc_v3_01',
        severity: 'HIGH',
        priority: 'P2',
        title: 'Confirmed Missing Hard Hat',
        message: 'Worker T-023 confirmed missing safety helmet in Production Floor after 15 consecutive frames.',
        camera_id: 'camera_01',
        zone_id: 'zone_production',
        event_type: 'MISSING_HELMET',
        status: 'ACTIVE',
        timestamp: new Date().toISOString(),
      },
    ],
    workers: [
      {
        track_id: 23,
        bbox: [170, 95, 350, 470],
        normalized_bbox: [0.26, 0.19, 0.54, 0.88],
        ppe_status: {
          helmet: 'ABSENT',
          safety_vest: 'PRESENT',
          gloves: 'PRESENT',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: false,
        overall_status: 'NON_COMPLIANT',
        active_frames: 220,
        dwell_seconds: 7.3,
        confidence: 0.91,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: ['helmet'],
        is_partially_occluded: false,
      },
    ],
  },

  multi_worker: {
    id: 'multi_worker',
    name: 'Scenario 4: Multi-Worker Concurrent Independence',
    title: 'Multi-Worker Concurrent Independence',
    subtitle: 'Zero Cross-Worker Contamination',
    shortTitle: 'Multi-Worker Independence',
    description: 'Three workers (Safe, Unknown, Violation) tracked concurrently. Zero cross-worker gear contamination.',
    expectedSafetyState: 'Worker A Safe, Worker B Unknown, Worker C Violation',
    toleranceFrames: 15,
    highlightNote: 'Hungarian bipartite matching isolates tracks simultaneously',
    explanation: 'Independent Hungarian bipartite association maintains 1-to-1 worker gear assignments without spatial leakage.',
    fireStatus: 'CLEAR',
    smokeStatus: 'CLEAR',
    hazards: [],
    alerts: [
      {
        alert_id: 'demo_alt_v3_02',
        incident_id: 'demo_inc_v3_02',
        severity: 'HIGH',
        priority: 'P2',
        title: 'Confirmed Missing Safety Vest',
        message: 'Worker T-023 confirmed missing high-vis vest in Production Floor after 15 frames.',
        camera_id: 'camera_01',
        zone_id: 'zone_production',
        event_type: 'MISSING_SAFETY_VEST',
        status: 'ACTIVE',
        timestamp: new Date().toISOString(),
      },
    ],
    workers: [
      {
        track_id: 14,
        bbox: [80, 110, 220, 460],
        normalized_bbox: [0.12, 0.22, 0.34, 0.88],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'PRESENT',
          gloves: 'PRESENT',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: true,
        overall_status: 'COMPLIANT',
        active_frames: 180,
        dwell_seconds: 6.0,
        confidence: 0.94,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: [],
      },
      {
        track_id: 19,
        bbox: [240, 120, 390, 470],
        normalized_bbox: [0.38, 0.24, 0.62, 0.9],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'PRESENT',
          gloves: 'UNKNOWN',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: false,
        overall_status: 'UNKNOWN',
        active_frames: 110,
        dwell_seconds: 3.6,
        confidence: 0.88,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: [],
        is_partially_occluded: true,
      },
      {
        track_id: 23,
        bbox: [410, 100, 560, 460],
        normalized_bbox: [0.65, 0.2, 0.88, 0.88],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'ABSENT',
          gloves: 'PRESENT',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: false,
        overall_status: 'NON_COMPLIANT',
        active_frames: 150,
        dwell_seconds: 5.0,
        confidence: 0.92,
        zone_id: 'zone_production',
        camera_id: 'camera_01',
        camera_name: 'CAM-01 • Production Floor Primary',
        missing_items: ['safety_vest'],
      },
    ],
  },

  fire_smoke: {
    id: 'fire_smoke',
    name: 'Scenario 5: Decoupled Combustion Emergency (Fire & Smoke)',
    title: 'Decoupled Combustion Emergency',
    subtitle: 'P0 Immediate Halt & Evacuation',
    shortTitle: 'Fire & Smoke Emergency',
    description: 'Open combustion flame and atmospheric smoke plume detected. Bypasses worker tracking to trigger P0 Emergency halt.',
    expectedSafetyState: 'P0 EMERGENCY (Fire & Smoke Confirmed)',
    toleranceFrames: 15,
    highlightNote: 'Decoupled thermal branch operates independently from worker tracker',
    explanation: 'Combustion detection event received from decoupled thermal pipeline. Evacuation siren dispatched.',
    fireStatus: 'DETECTED',
    smokeStatus: 'DETECTED',
    hazards: [
      {
        hazard_id: 'demo_haz_f01',
        hazard_type: 'fire',
        state: 'CONFIRMED',
        confidence: 0.93,
        zone_id: 'zone_hazard',
        camera_id: 'camera_03',
        active_frames: 16,
        bbox: [120, 200, 280, 360],
        normalized_bbox: [0.18, 0.38, 0.44, 0.7],
      },
      {
        hazard_id: 'demo_haz_s01',
        hazard_type: 'smoke',
        state: 'CONFIRMED',
        confidence: 0.86,
        zone_id: 'zone_hazard',
        camera_id: 'camera_03',
        active_frames: 22,
        bbox: [80, 80, 340, 240],
        normalized_bbox: [0.12, 0.15, 0.52, 0.46],
      },
    ],
    alerts: [
      {
        alert_id: 'demo_alt_p0_01',
        incident_id: 'demo_inc_p0_01',
        severity: 'CRITICAL',
        priority: 'P0',
        title: 'P0 CRITICAL: Active Combustion & Smoke Plume',
        message: 'Decoupled thermal pipeline confirmed active flame and smoke in Hazard Zone / Electrical Room (CAM-03).',
        camera_id: 'camera_03',
        zone_id: 'zone_hazard',
        event_type: 'FIRE_AND_SMOKE',
        status: 'ACTIVE',
        timestamp: new Date().toISOString(),
      },
    ],
    workers: [
      {
        track_id: 14,
        bbox: [380, 110, 520, 460],
        normalized_bbox: [0.6, 0.22, 0.82, 0.88],
        ppe_status: {
          helmet: 'PRESENT',
          safety_vest: 'PRESENT',
          gloves: 'PRESENT',
          safety_footwear: 'PRESENT',
        },
        overall_compliant: true,
        overall_status: 'COMPLIANT',
        active_frames: 180,
        dwell_seconds: 6.0,
        confidence: 0.94,
        zone_id: 'zone_hazard',
        camera_id: 'camera_03',
        camera_name: 'CAM-03 • Hazard Zone',
        missing_items: [],
      },
    ],
  },
};
