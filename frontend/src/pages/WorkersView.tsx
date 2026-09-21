/**
 * WorkersView.tsx — RAKSHYA VISION Phase 8
 * Real-Time Worker Tracking & PPE Compliance Evaluation.
 * Shows anonymous track states with strictly separated PRESENT, ABSENT, and UNKNOWN badges.
 */

import React, { useState } from 'react';
import {
  Users,
  ShieldAlert,
  Upload,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { WorkerTrack, ComplianceSummary } from '../types';
import { WorkerComplianceCard } from '../components/WorkerComplianceCard';
import { API_BASE_URL } from '../utils/constants';

interface WorkersViewProps {
  complianceConfig: any;
}

export const WorkersView: React.FC<WorkersViewProps> = ({ complianceConfig }) => {
  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  // Auto-poll live stream workers and PPE compliance from active camera worker
  React.useEffect(() => {
    let isMounted = true;
    const pollLiveWorkers = async () => {
      if (isAnalyzing) return;
      try {
        const response = await fetch(`${API_BASE_URL}/api/compliance/live`);
        if (response.ok && isMounted) {
          const data = await response.json();
          if (data && Array.isArray(data.workers)) {
            setWorkers(data.workers);
            if (data.summary) {
              setSummary(data.summary);
            }
            if (data.annotated_image_base64) {
              setAnnotatedImage(`data:image/jpeg;base64,${data.annotated_image_base64}`);
            }
          }
        }
      } catch {
        // Silently tolerate background polling dropouts
      }
    };

    pollLiveWorkers();
    const interval = setInterval(pollLiveWorkers, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [isAnalyzing]);

  const handleFrameUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAnalyzing(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('camera_id', 'CAM-01');
    formData.append('zone_id', 'FAB_BAY_01');

    try {
      const response = await fetch(`${API_BASE_URL}/api/compliance/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Inference returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setWorkers(data.workers || []);
      setSummary(data.summary || null);
      if (data.annotated_image_base64) {
        setAnnotatedImage(`data:image/jpeg;base64,${data.annotated_image_base64}`);
      }
    } catch (err: any) {
      setErrorMsg(`Analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredWorkers = workers.filter((w) => {
    if (filterStatus === 'COMPLIANT') return w.overall_compliant;
    if (filterStatus === 'VIOLATION') return !w.overall_compliant;
    if (filterStatus === 'UNKNOWN') {
      return Object.values(w.ppe_status).some((s) => s === 'UNKNOWN');
    }
    return true;
  });

  return (
    <div className="workers-view-container">
      {/* Title Bar */}
      <div className="view-title-bar">
        <div>
          <h2 className="view-heading">
            <Users size={22} /> Worker Tracking & PPE Compliance
          </h2>
          <p className="view-subheading">
            Multi-object ByteTrack tracking with Hungarian spatial PPE association and temporal validation
          </p>
        </div>

        {/* Upload Frame Analyzer */}
        <div>
          <label className="btn btn-primary file-upload-label">
            <Upload size={16} />
            <span>{isAnalyzing ? 'Running PPE Tracking...' : 'Test PPE Compliance on Image'}</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFrameUpload}
              disabled={isAnalyzing}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      {errorMsg && (
        <div className="banner-error mb-4">
          <ShieldAlert size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Compliance Stats Bar */}
      <div className="compliance-summary-grid">
        <div className="compliance-stat-card">
          <span className="stat-label">Total Workers</span>
          <span className="stat-val font-mono">{summary ? summary.total_workers : '0'}</span>
          <span className="stat-sub">
            {summary ? `${summary.total_workers} detected in current frame` : 'No active tracks'}
          </span>
        </div>

        <div className="compliance-stat-card">
          <span className="stat-label">Full Compliance</span>
          <span className="stat-val text-success font-mono">
            {summary ? summary.compliant_workers : '0'}
          </span>
          <span className="stat-sub">Wearing all required PPE</span>
        </div>

        <div className="compliance-stat-card">
          <span className="stat-label">Safety Violations</span>
          <span className="stat-val text-error font-mono">
            {summary ? summary.non_compliant_workers : '0'}
          </span>
          <span className="stat-sub">Confirmed absent mandatory items</span>
        </div>

        <div className="compliance-stat-card">
          <span className="stat-label">Compliance Rate</span>
          <span className="stat-val text-accent font-mono">
            {summary ? `${summary.compliance_rate_percent.toFixed(1)}%` : 'NO DATA'}
          </span>
          <span className="stat-sub">
            {summary ? 'Evaluated across verified tracks' : 'Awaiting worker detections'}
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="workers-toolbar">
        <div className="filter-item">
          <Filter size={14} />
          <select
            className="filter-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="ALL">All Workers ({workers.length})</option>
            <option value="COMPLIANT">Fully Compliant</option>
            <option value="VIOLATION">Safety Violations</option>
            <option value="UNKNOWN">Has Unknown / Occluded Items</option>
          </select>
        </div>

        <div className="ppe-policy-legend">
          <span className="legend-item text-success">
            ● CONFIRMED PRESENT (N ≥ {complianceConfig?.temporal?.confirmation_frames_needed ?? 3})
          </span>
          <span className="legend-item text-error">
            ● CONFIRMED ABSENT (N_missing &gt; {complianceConfig?.temporal?.missing_tolerance_before_absent ?? 5})
          </span>
          <span className="legend-item text-warning">
            ● UNKNOWN / OCCLUDED (Never triggers violation)
          </span>
        </div>
      </div>

      {/* Annotated Frame Preview (if inference run) */}
      {annotatedImage && (
        <div className="annotated-preview-box mb-6">
          <div className="annotated-preview-header">
            <span className="font-bold flex items-center gap-2">
              <CheckCircle2 size={16} className="text-success" />
              Live Frame Inference Annotation Output
            </span>
            <button className="btn-link" onClick={() => setAnnotatedImage(null)}>
              Dismiss Frame
            </button>
          </div>
          <img src={annotatedImage} alt="Annotated Workers" className="annotated-img" />
        </div>
      )}

      {/* Workers Grid or Empty State */}
      {filteredWorkers.length === 0 ? (
        <div className="workers-empty-card">
          <Users size={48} className="empty-icon" />
          <h3 className="empty-title">
            {workers.length === 0 ? 'NO ACTIVE WORKERS DETECTED' : 'NO WORKERS MATCH FILTER'}
          </h3>
          <p className="empty-subtitle">
            {workers.length === 0
              ? 'No workers are currently tracked in the active camera stream. Use "Test PPE Compliance on Image" above to test inference on a sample frame.'
              : 'Try changing the status filter to see other worker tracks.'}
          </p>
        </div>
      ) : (
        <div className="workers-cards-grid">
          {filteredWorkers.map((w) => (
            <WorkerComplianceCard key={w.track_id} worker={w} />
          ))}
        </div>
      )}
    </div>
  );
};
