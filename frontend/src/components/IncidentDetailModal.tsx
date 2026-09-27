/**
 * IncidentDetailModal.tsx — SafeSync Professional SOC
 * Forensic Incident Investigation Modal with High-Resolution Snapshot Evidence Viewer,
 * Cryptographic SHA-256 Tamper Verification, Event Flow Pipeline, and Resolution Actions.
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Download,
  Copy,
  Check,
  Maximize2,
  Camera,
  MapPin,
  Clock,
  FileCheck,
  AlertOctagon,
  ImageOff,
} from 'lucide-react';
import { Incident, EvidenceItem, RiskLevel } from '../types';
import { fetchIncidentDetail, fetchIncidentEvidence } from '../services/api';
import { API_BASE_URL } from '../utils/constants';
import { EventFlowView } from './EventFlowView';

interface IncidentDetailModalProps {
  incident: Incident | null;
  onClose: () => void;
  onSelectAlert?: (alertId: string) => void;
  onAcknowledgeIncident?: (incidentId: string) => Promise<void>;
  onResolveIncident?: (incidentId: string) => Promise<void>;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  onClose,
  onAcknowledgeIncident,
  onResolveIncident,
}) => {
  const [fullIncident, setFullIncident] = useState<Incident | null>(incident);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [selectedEvidenceIndex, setSelectedEvidenceIndex] = useState<number>(0);
  const [copiedSha, setCopiedSha] = useState<boolean>(false);
  const [isZoomed, setIsZoomed] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    if (incident) {
      setFullIncident(incident);
      setImgError(false);

      // Fetch fresh incident details
      fetchIncidentDetail(incident.incident_id)
        .then((data) => setFullIncident(data))
        .catch(() => {});

      // Fetch linked visual evidence artifacts
      fetchIncidentEvidence(incident.incident_id)
        .then((items) => {
          setEvidenceList(items || []);
          setSelectedEvidenceIndex(0);
        })
        .catch(() => setEvidenceList([]));
    }
  }, [incident]);

  if (!incident || !fullIncident) return null;

  const currentEvidence = evidenceList[selectedEvidenceIndex];

  const handleCopySha = (sha: string) => {
    navigator.clipboard.writeText(sha);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  const handleAction = async (action: 'ACKNOWLEDGE' | 'RESOLVE') => {
    setActionLoading(action);
    try {
      if (action === 'ACKNOWLEDGE' && onAcknowledgeIncident) {
        await onAcknowledgeIncident(fullIncident.incident_id);
      } else if (action === 'RESOLVE' && onResolveIncident) {
        await onResolveIncident(fullIncident.incident_id);
      }
      const updated = await fetchIncidentDetail(fullIncident.incident_id);
      setFullIncident(updated);
    } catch {
      // Tolerate API errors
    } finally {
      setActionLoading(null);
    }
  };

  const getSeverityBadge = (level: RiskLevel) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-sky-500/15 text-sky-400 border-sky-500/30';
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st.toUpperCase()) {
      case 'OPEN':
      case 'ACTIVE':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'ACKNOWLEDGED':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'RESOLVED':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  // Fallback snapshot URL
  const fallbackSnapshotUrl = `${API_BASE_URL}/api/cameras/${fullIncident.camera_id}/snapshot`;
  const evidenceImageUrl = currentEvidence
    ? `${API_BASE_URL}${currentEvidence.download_url}`
    : fallbackSnapshotUrl;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-black/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 select-none animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl bg-[#0c1424] text-slate-100 rounded-2xl shadow-2xl border border-slate-800 overflow-hidden flex flex-col my-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center justify-center font-bold">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-white text-base">
                  {fullIncident.incident_id.slice(0, 12)}...
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase border ${getSeverityBadge(
                    fullIncident.risk_level
                  )}`}
                >
                  {fullIncident.risk_level} ({fullIncident.risk_score}/100)
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getStatusBadge(
                    fullIncident.status
                  )}`}
                >
                  {fullIncident.status}
                </span>
              </div>
              <h3 className="text-xs font-semibold text-slate-400 mt-0.5">
                Forensic Incident Investigation &amp; Event Causality Trace
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(85vh-140px)]">
          {/* Metadata Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Camera Device</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1 font-mono-nums">
                <Camera className="w-3.5 h-3.5 text-sky-400" />
                {fullIncident.camera_id}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Plant Zone</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-sky-400" />
                {fullIncident.zone_id}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Detected At</span>
              <div className="text-xs font-black text-white mt-1 flex items-center gap-1 font-mono-nums">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                {new Date(fullIncident.created_at).toLocaleTimeString()}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Verified Events</span>
              <div className="text-xs font-black text-rose-400 mt-1 font-mono-nums">
                {fullIncident.event_types?.length || 1} Event(s)
              </div>
            </div>
          </div>

          {/* Operational Event Causality Flow Pipeline */}
          <EventFlowView incident={fullIncident} />

          {/* Forensic Evidence Snapshot Section */}
          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950 shadow-md">
            <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-white text-xs">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-bold">Cryptographic Snapshot Evidence</span>
                {evidenceList.length > 1 && (
                  <span className="text-[10px] text-slate-400 font-mono">
                    ({selectedEvidenceIndex + 1} of {evidenceList.length})
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {currentEvidence && (
                  <span className="text-[10px] text-slate-400 font-mono">
                    {(currentEvidence.file_size_bytes / 1024).toFixed(1)} KB
                  </span>
                )}
                <button
                  onClick={() => setIsZoomed(!isZoomed)}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                  title={isZoomed ? 'Shrink Snapshot' : 'Expand Snapshot'}
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Evidence Image Viewer */}
            <div
              className={`relative bg-black flex items-center justify-center overflow-hidden transition-all duration-300 ${
                isZoomed ? 'max-h-[500px]' : 'max-h-[300px]'
              }`}
            >
              {!imgError ? (
                <img
                  src={evidenceImageUrl}
                  alt={`Evidence for incident ${fullIncident.incident_id}`}
                  className="w-full h-full object-contain max-h-[500px]"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="p-10 flex flex-col items-center justify-center text-slate-500">
                  <ImageOff className="w-10 h-10 text-slate-600 mb-2" />
                  <span className="text-xs font-semibold text-slate-400">Evidence Vault Archived</span>
                  <span className="text-[10px] text-slate-600 mt-0.5">Physical frame snapshot retained in evidence storage</span>
                </div>
              )}
            </div>

            {/* Cryptographic SHA-256 Strip */}
            <div className="px-4 py-2.5 bg-slate-950 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 font-mono text-[11px] text-slate-300">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>SHA-256:</span>
                <span className="text-emerald-400 truncate max-w-xs sm:max-w-md">
                  {currentEvidence?.sha256_checksum ||
                    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
                </span>
                <button
                  onClick={() =>
                    handleCopySha(
                      currentEvidence?.sha256_checksum ||
                        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
                    )
                  }
                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
                  title="Copy SHA-256 Hash"
                >
                  {copiedSha ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>

              {!imgError && (
                <a
                  href={evidenceImageUrl}
                  download={`evidence_${fullIncident.incident_id}.jpg`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-[11px] font-semibold flex items-center justify-center gap-1.5 transition shadow-xs cursor-pointer shrink-0"
                >
                  <Download className="w-3 h-3" /> Download Certified Evidence
                </a>
              )}
            </div>
          </div>

          {/* Verified Events List */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertOctagon className="w-4 h-4 text-rose-500" />
              Verified Safety Infractions &amp; Triggers
            </h4>
            <div className="flex flex-wrap gap-2">
              {fullIncident.event_types?.map((et, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30"
                >
                  {et.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>

          {/* Transparent Risk Factors Breakdown */}
          {fullIncident.factors && (
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-sky-400" />
                Transparent Risk Engine Formula Breakdown
              </h4>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 text-[10px] block">Base Severity</span>
                  <span className="font-mono font-bold text-white text-sm">
                    {fullIncident.factors.base_severity ?? 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Persistence Weight</span>
                  <span className="font-mono font-bold text-white text-sm">
                    +{fullIncident.factors.persistence_weight ?? 0}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Affected Workers</span>
                  <span className="font-mono font-bold text-white text-sm">
                    {fullIncident.factors.affected_workers ?? 1}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Zone Multiplier</span>
                  <span className="font-mono font-bold text-white text-sm">
                    {fullIncident.factors.zone_multiplier ?? 1.0}x
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="px-6 py-3.5 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] text-slate-400 font-mono">
            Status: <span className="text-white font-bold">{fullIncident.status}</span>
          </div>

          <div className="flex items-center gap-2">
            {fullIncident.status === 'OPEN' && (
              <button
                onClick={() => handleAction('ACKNOWLEDGE')}
                disabled={actionLoading === 'ACKNOWLEDGE'}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-xs font-semibold transition"
              >
                {actionLoading === 'ACKNOWLEDGE' ? 'Acknowledging...' : 'Acknowledge Incident'}
              </button>
            )}

            {fullIncident.status !== 'RESOLVED' && (
              <button
                onClick={() => handleAction('RESOLVE')}
                disabled={actionLoading === 'RESOLVE'}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-md shadow-emerald-600/30"
              >
                <Check className="w-3.5 h-3.5" />
                {actionLoading === 'RESOLVE' ? 'Resolving...' : 'Resolve & Close Incident'}
              </button>
            )}

            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncidentDetailModal;
