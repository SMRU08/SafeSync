/**
 * workerDisplay.ts — SafeSync worker bounding-box safety colors (visualization only).
 *
 * Maps the FINAL, temporally-validated worker compliance state produced by the backend
 * pipeline (YOLO → ByteTrack → Hungarian association → temporal validation) to a
 * display color/label. It never re-derives compliance from raw detections.
 *
 * Priority (UNKNOWN ≠ ABSENT ≠ VIOLATION):
 *   NON_COMPLIANT (confirmed ABSENT) → RED    "CONFIRMED VIOLATION"
 *   UNKNOWN                          → AMBER  "UNKNOWN"
 *   COMPLIANT (all PRESENT)          → GREEN  "SAFE"
 * UNKNOWN is never shown as RED.
 */
import type { WorkerTrack } from '../types';

export type WorkerDisplayState = 'SAFE' | 'UNKNOWN' | 'VIOLATION';

export const WORKER_STATE_COLORS: Record<WorkerDisplayState, string> = {
  SAFE: '#22C55E',
  UNKNOWN: '#F59E0B',
  VIOLATION: '#EF4444',
};

const PPE_LABELS: Array<[keyof WorkerTrack['ppe_status'], string]> = [
  ['helmet', 'Helmet'],
  ['safety_vest', 'Vest'],
  ['gloves', 'Gloves'],
  ['safety_footwear', 'Footwear'],
];

export interface WorkerDisplay {
  state: WorkerDisplayState;
  color: string;
  label: string;
  detail: string;
  missingItems: string[];
  unknownItems: string[];
}

export function resolveWorkerDisplay(
  worker: Pick<WorkerTrack, 'overall_compliant' | 'overall_status' | 'ppe_status'>,
): WorkerDisplay {
  const ppe = worker.ppe_status || ({} as WorkerTrack['ppe_status']);
  const absent = PPE_LABELS.filter(([k]) => ppe[k] === 'ABSENT').map(([, l]) => l);
  const unknown = PPE_LABELS.filter(([k]) => !ppe[k] || ppe[k] === 'UNKNOWN').map(([, l]) => l);

  // Authoritative: validated tri-state from the backend. Fallback for legacy payloads
  // without overall_status: only a confirmed ABSENT item may produce a violation.
  const status =
    worker.overall_status ??
    (absent.length > 0 ? 'NON_COMPLIANT' : worker.overall_compliant ? 'COMPLIANT' : 'UNKNOWN');

  if (status === 'NON_COMPLIANT') {
    return {
      state: 'VIOLATION',
      color: WORKER_STATE_COLORS.VIOLATION,
      label: 'CONFIRMED VIOLATION',
      detail: absent.length ? `Missing: ${absent.join(', ')}` : '',
      missingItems: absent,
      unknownItems: unknown,
    };
  }
  if (status === 'COMPLIANT') {
    return {
      state: 'SAFE',
      color: WORKER_STATE_COLORS.SAFE,
      label: 'SAFE',
      detail: '',
      missingItems: [],
      unknownItems: [],
    };
  }
  return {
    state: 'UNKNOWN',
    color: WORKER_STATE_COLORS.UNKNOWN,
    label: 'UNKNOWN',
    detail: unknown.length ? `${unknown.join(', ')} visibility limited` : 'Visibility limited',
    missingItems: [],
    unknownItems: unknown,
  };
}
