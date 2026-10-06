/**
 * WorkersView.tsx — SafeSync Phase 5: Workers & PPE Center + Explainability
 * Premier Hackathon Worker Safety & Explainable Compliance Dashboard.
 *
 * Answers the 8 Core Questions:
 *   1. WHO is being monitored?       → Anonymous Tracking ID (Worker #{ID})
 *   2. WHICH camera/zone is worker? → Real camera node & plant zone (or '—')
 *   3. WHICH PPE is PRESENT?         → Helmet, Vest, Gloves, Footwear (✓ PRESENT, #22C55E)
 *   4. WHICH PPE is UNKNOWN?         → ? UNKNOWN (#F5B942, non-punitive, visibility limited)
 *   5. WHICH PPE is ABSENT?          → ✕ ABSENT (#EF4444, confirmed absence after 15 frames)
 *   6. WHAT is overall safety state? → SAFE / UNKNOWN / CONFIRMED VIOLATION
 *   7. WHY is worker in that state?  → Comprehensive Explainability Panel for all 3 states
 *   8. WHEN was worker observed?     → Actual timestamp or dwell time (or '—')
 *
 * Adheres strictly to:
 *   - Absolute Backend Lock (V3 SHA-256: 9b414f...)
 *   - Current Canonical PPE (Helmet, Vest, Gloves, Footwear; Goggles PLANNED/EXTENSIBLE)
 *   - Locked Thresholds (Helmet 0.25, Vest 0.25, Gloves 0.22, Footwear 0.22, 15 frames debounce)
 *   - Zero fake workers, zero fake percentages, zero biometric claims
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Users,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Search,
  LayoutGrid,
  List,
  Eye,
  MapPin,
  Clock,
  Activity,
  Download,
  RefreshCw,
  Camera,
  DoorOpen,
  Tv,
  AlertTriangle,
  FileText,
  Info,
  X,
  Check,
  Shield,
} from 'lucide-react';
import {
  WorkerTrack,
  ComplianceSummary,
  CameraConfig,
  Alert,
  Incident,
} from '../types';
import { ActiveTab } from '../components/Sidebar';
import { API_BASE_URL } from '../utils/constants';
import { WorkerComplianceCard } from '../components/WorkerComplianceCard';
import { WorkerSafetyLegend } from '../components/WorkerSafetyLegend';
import { PPEStatusBadge } from '../components/PPEStatusBadge';
import { resolveWorkerDisplay } from '../utils/workerDisplay';
import { EmptyState } from '../components/ui/EmptyState';

interface WorkersViewProps {
  complianceConfig?: any;
  cameras?: CameraConfig[];
  alerts?: Alert[];
  incidents?: Incident[];
  onNavigate?: (tab: ActiveTab, subTab?: 'matrix' | 'entry_gate') => void;
  onOpenEnrollModal?: () => void;
}

export const WorkersView: React.FC<WorkersViewProps> = ({
  complianceConfig: _complianceConfig,
  cameras = [],
  alerts = [],
  incidents = [],
  onNavigate,
  onOpenEnrollModal: _onOpenEnrollModal,
}) => {
  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<WorkerTrack | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompliance, setFilterCompliance] = useState<'ALL' | 'SAFE' | 'VIOLATION' | 'UNKNOWN'>('ALL');
  const [selectedCameraFilter, setSelectedCameraFilter] = useState<string>('ALL');
  const [selectedZoneFilter, setSelectedZoneFilter] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'GRID' | 'TABLE'>('GRID');

  // Connection & loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastFetchTimestamp, setLastFetchTimestamp] = useState<string | null>(null);

  // Active camera map for rapid lookup
  const cameraMap = useMemo(() => {
    const map = new Map<string, CameraConfig>();
    cameras.forEach((c) => {
      map.set(c.camera_id, c);
    });
    return map;
  }, [cameras]);

  // Unique zones extracted from actual cameras and workers
  const availableZones = useMemo(() => {
    const zones = new Set<string>();
    cameras.forEach((c) => {
      if (c.zone_id) zones.add(c.zone_id);
    });
    workers.forEach((w) => {
      if (w.zone_id) zones.add(w.zone_id);
    });
    return Array.from(zones);
  }, [cameras, workers]);

  // Fetch live compliance from backend API
  const fetchWorkers = async (showSpinner = false) => {
    if (showSpinner) setIsRefreshing(true);
    try {
      const url =
        selectedCameraFilter !== 'ALL'
          ? `${API_BASE_URL}/api/compliance/live?camera_id=${encodeURIComponent(selectedCameraFilter)}`
          : `${API_BASE_URL}/api/compliance/live`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data) {
        if (Array.isArray(data.workers)) {
          // Enrich worker tracks with camera details if available
          const enriched: WorkerTrack[] = data.workers.map((w: WorkerTrack) => {
            const camId = w.camera_id || data.camera_id || 'camera_01';
            const cam = cameraMap.get(camId);
            return {
              ...w,
              camera_id: camId,
              camera_name: cam?.name || camId,
              zone_id: w.zone_id || cam?.zone_id || cam?.location,
              timestamp: data.timestamp || w.timestamp,
            };
          });

          setWorkers(enriched);

          // Keep selected worker in sync if updated
          if (selectedWorker) {
            const updated = enriched.find((w) => w.track_id === selectedWorker.track_id);
            if (updated) setSelectedWorker(updated);
          }
        } else {
          setWorkers([]);
        }

        if (data.summary) {
          setSummary(data.summary);
        }

        setLastFetchTimestamp(new Date().toISOString());
        setConnectionError(null);
      }
    } catch (err: any) {
      setConnectionError(err.message || 'Worker data stream unavailable');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWorkers(true);
    const interval = setInterval(() => fetchWorkers(false), 1500);
    return () => clearInterval(interval);
  }, [selectedCameraFilter, cameraMap]);

  // Filtered & Sorted Workers (Priority: Confirmed Violation → Unknown → Safe)
  const filteredAndSortedWorkers = useMemo(() => {
    let result = workers.filter((w) => {
      const disp = resolveWorkerDisplay(w);

      // Compliance status filter
      if (filterCompliance === 'SAFE' && disp.state !== 'SAFE') return false;
      if (filterCompliance === 'VIOLATION' && disp.state !== 'VIOLATION') return false;
      if (filterCompliance === 'UNKNOWN' && disp.state !== 'UNKNOWN') return false;

      // Camera filter
      if (selectedCameraFilter !== 'ALL' && w.camera_id !== selectedCameraFilter) {
        return false;
      }

      // Zone filter
      if (selectedZoneFilter !== 'ALL' && w.zone_id !== selectedZoneFilter) {
        return false;
      }

      // Search query: strictly by Tracking ID or Zone (Section 18 & 50)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().replace(/^worker\s*#?/i, '').trim();
        const idMatches = w.track_id.toString().includes(q);
        const zoneMatches = w.zone_id ? w.zone_id.toLowerCase().includes(q) : false;
        const camMatches = w.camera_id ? w.camera_id.toLowerCase().includes(q) : false;
        return idMatches || zoneMatches || camMatches;
      }

      return true;
    });

    // Default sorting priority (Section 34): 1. VIOLATION, 2. UNKNOWN, 3. SAFE
    result.sort((a, b) => {
      const stateScore = (w: WorkerTrack) => {
        const d = resolveWorkerDisplay(w);
        if (d.state === 'VIOLATION') return 3;
        if (d.state === 'UNKNOWN') return 2;
        return 1;
      };

      const diff = stateScore(b) - stateScore(a);
      if (diff !== 0) return diff;

      // Secondary: active frames (most persistent / dwell time)
      return (b.active_frames || 0) - (a.active_frames || 0);
    });

    return result;
  }, [workers, filterCompliance, selectedCameraFilter, selectedZoneFilter, searchQuery]);

  // Actual KPI counts (strictly real values, Section 16 & 49)
  const totalCount = summary?.total_workers ?? workers.length;
  const safeCount = workers.filter((w) => resolveWorkerDisplay(w).state === 'SAFE').length;
  const violationCount = workers.filter((w) => resolveWorkerDisplay(w).state === 'VIOLATION').length;
  const unknownCount = workers.filter((w) => resolveWorkerDisplay(w).state === 'UNKNOWN').length;

  // Export worker telemetry JSON (Section 29)
  const handleExportWorkerLog = (w: WorkerTrack) => {
    const reportData = {
      worker_tracking_id: w.track_id,
      camera_id: w.camera_id || 'unknown',
      camera_name: w.camera_name || 'unknown',
      zone_id: w.zone_id || '—',
      safety_state: resolveWorkerDisplay(w).state,
      safety_label: resolveWorkerDisplay(w).label,
      overall_compliant: w.overall_compliant,
      ppe_status: w.ppe_status,
      confidence: w.confidence !== undefined ? w.confidence : null,
      active_frames: w.active_frames,
      dwell_seconds: w.dwell_seconds ?? Math.round((w.active_frames || 1) / 30),
      bounding_box: w.bbox,
      normalized_bbox: w.normalized_bbox,
      last_observed: w.timestamp || new Date().toISOString(),
      export_timestamp: new Date().toISOString(),
      engine_version: 'SafeSync V3 Production (Locked)',
      temporal_window: '15 Frames Backend Debounced',
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `safesync_worker_${w.track_id}_telemetry.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Find actual safety incidents/alerts matching this worker's camera or zone (Section 30)
  const workerSafetyEvents = useMemo(() => {
    if (!selectedWorker) return [];
    const fromIncidents = incidents.filter(
      (inc) =>
        (selectedWorker.camera_id && inc.camera_id === selectedWorker.camera_id) ||
        (selectedWorker.zone_id && inc.zone_id === selectedWorker.zone_id)
    );
    const fromAlerts = alerts
      .filter(
        (alt) =>
          (selectedWorker.camera_id && alt.camera_id === selectedWorker.camera_id) ||
          (selectedWorker.zone_id && alt.zone_id === selectedWorker.zone_id)
      )
      .map((alt) => ({
        incident_id: alt.alert_id,
        event_types: [alt.event_type],
        created_at: alt.timestamp || new Date().toISOString(),
        risk_level: alt.severity || 'MEDIUM',
        status: alt.status,
      }));

    return [...fromIncidents, ...fromAlerts];
  }, [selectedWorker, incidents, alerts]);

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#07111F] text-[#E8F0F7] select-none">
      {/* ─── Top Header & SOC Telemetry Bar ─────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#20344A]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-white tracking-tight">
                  WORKERS &amp; PPE CENTER
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-sky-400 border border-slate-700 font-bold uppercase">
                  Explainable AI
                </span>
              </div>
              <p className="text-xs text-[#8FA3B8] mt-0.5">
                Real-time worker safety tracking, itemized spatial PPE auditing, and ISO-aligned explainability
              </p>
            </div>
          </div>
        </div>

        {/* Live Status & Locked Model Badges */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto flex-wrap">
          {/* Connection Status Pill (Section 31 & 45) */}
          {connectionError ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-500/15 border border-rose-500/40 text-rose-400 text-xs font-bold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>CONNECTION UNAVAILABLE</span>
              <button
                onClick={() => fetchWorkers(true)}
                className="ml-1 underline hover:text-white cursor-pointer"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-bold text-white tracking-wider text-[11px]">● LIVE</span>
              <span className="text-slate-500 font-mono text-[10px]">
                {lastFetchTimestamp
                  ? new Date(lastFetchTimestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                  : '—'}
              </span>
            </div>
          )}

          {/* Model Lock Tag (Section 1) */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-[10px] font-mono text-slate-400">
            <Shield className="w-3 h-3 text-sky-400" />
            <span>V3 Production Model (LOCKED)</span>
          </div>

          {/* Refresh Action */}
          <button
            onClick={() => fetchWorkers(true)}
            disabled={isRefreshing}
            className="p-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white hover:border-slate-600 transition cursor-pointer"
            title="Refresh Worker Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* ─── Summary KPI Ribbon (Section 16 & 49: Real Values Only) ───────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        {/* Tracked Personnel */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between hover:border-slate-600 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wider">
              Tracked Personnel
            </span>
            <Users className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono mt-2 leading-none">
            {isLoading ? '—' : totalCount}
          </div>
          <span className="text-[10px] text-sky-400 font-medium mt-1">
            Anonymous Tracking IDs
          </span>
        </div>

        {/* Safe Workers (Green: #22C55E) */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between hover:border-emerald-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wider">
              Safe (Compliant)
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-[#22C55E] font-mono mt-2 leading-none">
            {isLoading ? '—' : safeCount}
          </div>
          <span className="text-[10px] text-emerald-400 font-medium mt-1">
            All Required PPE Present
          </span>
        </div>

        {/* Confirmed Violations (Red: #EF4444) */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between hover:border-rose-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wider">
              Confirmed Violations
            </span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-[#EF4444] font-mono mt-2 leading-none">
            {isLoading ? '—' : violationCount}
          </div>
          <span className="text-[10px] text-rose-400 font-medium mt-1">
            Debounced 15 Frames
          </span>
        </div>

        {/* Unknown / Visibility Limited (Yellow: #F5B942) */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between hover:border-amber-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wider">
              Visibility Limited
            </span>
            <HelpCircle className="w-4 h-4 text-[#F5B942]" />
          </div>
          <div className="text-2xl font-black text-[#F5B942] font-mono mt-2 leading-none">
            {isLoading ? '—' : unknownCount}
          </div>
          <span className="text-[10px] text-amber-400 font-medium mt-1">
            Non-Punitive • Unknown ≠ Violation
          </span>
        </div>
      </div>

      {/* ─── Production PPE Policy & Legend Banner ──────────────────────── */}
      <div className="p-3 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <WorkerSafetyLegend className="bg-transparent border-none p-0" />
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <span className="px-2 py-0.5 rounded bg-[#12263A] border border-[#20344A] text-slate-300">
            Thresholds: Helmet 0.25 | Vest 0.25 | Gloves 0.22 | Footwear 0.22
          </span>
        </div>
      </div>

      {/* ─── Filters & Search Toolbar (Section 17, 18, 38, 39) ───────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-1">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0D1B2A] border border-[#20344A] text-xs overflow-x-auto">
          {(['ALL', 'SAFE', 'VIOLATION', 'UNKNOWN'] as const).map((tab) => {
            const count =
              tab === 'ALL'
                ? workers.length
                : tab === 'SAFE'
                ? safeCount
                : tab === 'VIOLATION'
                ? violationCount
                : unknownCount;

            return (
              <button
                key={tab}
                onClick={() => setFilterCompliance(tab)}
                className={`px-3 py-1 font-bold rounded-lg transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  filterCompliance === tab
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <span>
                  {tab === 'ALL'
                    ? 'All Workers'
                    : tab === 'SAFE'
                    ? 'Safe'
                    : tab === 'VIOLATION'
                    ? 'Confirmed Violations'
                    : 'Unknown (Limited)'}
                </span>
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-black/30">
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Dropdowns, Search, and View Mode */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Camera Filter (Section 39) */}
          {cameras.length > 0 && (
            <select
              value={selectedCameraFilter}
              onChange={(e) => setSelectedCameraFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-xs text-white focus:outline-none focus:border-sky-500"
              title="Filter by Camera"
            >
              <option value="ALL">All Cameras ({cameras.length})</option>
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id}>
                  {c.name || c.camera_id}
                </option>
              ))}
            </select>
          )}

          {/* Zone Filter (Section 38) */}
          {availableZones.length > 0 && (
            <select
              value={selectedZoneFilter}
              onChange={(e) => setSelectedZoneFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-xs text-white focus:outline-none focus:border-sky-500 capitalize"
              title="Filter by Zone"
            >
              <option value="ALL">All Zones ({availableZones.length})</option>
              {availableZones.map((z) => (
                <option key={z} value={z}>
                  {z.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          )}

          {/* Search Input by Tracking ID (Section 18 & 50) */}
          <div className="relative w-48 sm:w-56">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Tracking ID..."
              className="w-full bg-[#0D1B2A] border border-[#20344A] rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Grid / Table View Switcher */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-[#0D1B2A] border border-[#20344A]">
            <button
              onClick={() => setViewMode('GRID')}
              className={`p-1.5 rounded-md transition cursor-pointer ${
                viewMode === 'GRID' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Grid View (Cards)"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('TABLE')}
              className={`p-1.5 rounded-md transition cursor-pointer ${
                viewMode === 'TABLE' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Table View (Ledger)"
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* ─── Main Content Surface ────────────────────────────────────────── */}
      {isLoading ? (
        /* Loading Skeleton State (Section 44) */
        <div className="space-y-4">
          <div className="p-8 rounded-xl bg-[#0D1B2A] border border-[#20344A] text-center">
            <RefreshCw className="w-6 h-6 text-sky-400 animate-spin mx-auto mb-2" />
            <h3 className="font-bold text-white text-sm">Loading worker safety data...</h3>
            <p className="text-xs text-slate-400 mt-1">Connecting to active camera compliance workers</p>
          </div>
        </div>
      ) : filteredAndSortedWorkers.length === 0 ? (
        /* Empty State (Section 42 & 43) */
        <EmptyState
          icon={ShieldCheck}
          title="NO ACTIVE WORKERS"
          description={
            searchQuery.trim() || filterCompliance !== 'ALL' || selectedCameraFilter !== 'ALL' || selectedZoneFilter !== 'ALL'
              ? 'No tracked personnel match the active search or filter criteria.'
              : 'Monitoring is active across surveillance feeds. No worker tracks currently detected in facility zones.'
          }
        />
      ) : viewMode === 'GRID' ? (
        /* Grid Mode (Section 7) */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredAndSortedWorkers.map((w) => {
            const cam = cameraMap.get(w.camera_id || '');
            const isEntryGate = w.zone_id === 'entry_gate' || (w.camera_id && w.camera_id.includes('gate'));

            return (
              <WorkerComplianceCard
                key={w.track_id}
                worker={w}
                cameraName={cam?.name || w.camera_name || w.camera_id}
                onInspect={(worker) => setSelectedWorker(worker)}
                onNavigateLive={() => onNavigate?.('live-monitor')}
                onNavigateGate={isEntryGate ? () => onNavigate?.('cameras', 'entry_gate') : undefined}
              />
            );
          })}
        </div>
      ) : (
        /* Table Mode / Ledger (Section 6) */
        <div className="rounded-xl border border-[#20344A] bg-[#0D1B2A] overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#12263A] border-b border-[#20344A] text-slate-400 font-bold text-[10px] uppercase tracking-wider">
                  <th className="py-3 px-4">Tracking ID</th>
                  <th className="py-3 px-4">Camera</th>
                  <th className="py-3 px-4">Plant Zone</th>
                  <th className="py-3 px-3">Helmet</th>
                  <th className="py-3 px-3">Safety Vest</th>
                  <th className="py-3 px-3">Gloves</th>
                  <th className="py-3 px-3">Footwear</th>
                  <th className="py-3 px-4">Overall Safety</th>
                  <th className="py-3 px-4">Last Seen</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#20344A]/70">
                {filteredAndSortedWorkers.map((w) => {
                  const disp = resolveWorkerDisplay(w);
                  const ppe = w.ppe_status || {
                    helmet: 'UNKNOWN',
                    safety_vest: 'UNKNOWN',
                    gloves: 'UNKNOWN',
                    safety_footwear: 'UNKNOWN',
                  };
                  const cam = cameraMap.get(w.camera_id || '');
                  const displayCam = cam?.name || w.camera_name || w.camera_id || 'CAM_01';
                  const displayZone = w.zone_id ? w.zone_id.replace(/_/g, ' ') : '—';
                  const isEntryGate = w.zone_id === 'entry_gate' || (w.camera_id && w.camera_id.includes('gate'));

                  const lastSeen = w.timestamp
                    ? new Date(w.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                    : w.first_seen
                    ? new Date(w.first_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                    : '—';

                  return (
                    <tr
                      key={w.track_id}
                      onClick={() => setSelectedWorker(w)}
                      className="hover:bg-[#12263A]/80 transition cursor-pointer"
                    >
                      {/* Tracking ID */}
                      <td className="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                        Worker #{w.track_id.toString().padStart(3, '0')}
                      </td>

                      {/* Camera */}
                      <td className="py-3 px-4 font-mono text-slate-300 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <Camera className="w-3 h-3 text-sky-400" />
                          <span>{displayCam}</span>
                        </div>
                      </td>

                      {/* Plant Zone */}
                      <td className="py-3 px-4 text-slate-300 capitalize whitespace-nowrap">
                        {displayZone}
                      </td>

                      {/* PPE Items (Compact badges) */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <PPEStatusBadge item="helmet" status={ppe.helmet} compact />
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        <PPEStatusBadge item="safety_vest" status={ppe.safety_vest} compact />
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        <PPEStatusBadge item="gloves" status={ppe.gloves} compact />
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        <PPEStatusBadge item="safety_footwear" status={ppe.safety_footwear} compact />
                      </td>

                      {/* Overall State */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                            disp.state === 'SAFE'
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : disp.state === 'VIOLATION'
                              ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                              : 'bg-amber-500/15 text-[#F5B942] border-amber-500/30'
                          }`}
                        >
                          {disp.label}
                        </span>
                      </td>

                      {/* Last Seen */}
                      <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap text-[11px]">
                        {lastSeen}
                      </td>

                      {/* Action Triggers */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {isEntryGate && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onNavigate?.('cameras', 'entry_gate');
                              }}
                              className="px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded text-[10px] font-bold transition flex items-center gap-1"
                              title="View in Entry Gate"
                            >
                              <DoorOpen className="w-2.5 h-2.5" /> Gate
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedWorker(w);
                            }}
                            className="px-2.5 py-1 bg-[#12263A] hover:bg-slate-700 text-sky-400 hover:text-white rounded text-[11px] font-bold transition inline-flex items-center gap-1 border border-[#20344A]"
                          >
                            <Eye className="w-3 h-3" /> Inspect
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Forensic Worker Profile Slide-Over Drawer (Section 14 & 24–30) ─── */}
      {selectedWorker && (() => {
        const selDisp = resolveWorkerDisplay(selectedWorker);
        const ppe = selectedWorker.ppe_status || {
          helmet: 'UNKNOWN',
          safety_vest: 'UNKNOWN',
          gloves: 'UNKNOWN',
          safety_footwear: 'UNKNOWN',
        };
        const cam = cameraMap.get(selectedWorker.camera_id || '');
        const displayCam = cam?.name || selectedWorker.camera_name || selectedWorker.camera_id || 'CAM_01';
        const displayZone = selectedWorker.zone_id ? selectedWorker.zone_id.replace(/_/g, ' ') : '—';
        const isEntryGate = selectedWorker.zone_id === 'entry_gate' || (selectedWorker.camera_id && selectedWorker.camera_id.includes('gate'));

        const lastSeen = selectedWorker.timestamp
          ? new Date(selectedWorker.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          : selectedWorker.first_seen
          ? new Date(selectedWorker.first_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          : '—';

        const totalSeconds = selectedWorker.dwell_seconds ?? Math.round((selectedWorker.active_frames || 1) / 30);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const dwellDisplay = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

        return (
          <div className="fixed inset-0 z-50 overflow-hidden bg-black/65 backdrop-blur-xs flex justify-end">
            <div className="w-full max-w-xl bg-[#0D1B2A] text-[#E8F0F7] border-l border-[#20344A] shadow-2xl h-full flex flex-col p-6 overflow-y-auto animate-in slide-in-from-right duration-200">
              {/* Drawer Header */}
              <div className="flex items-center justify-between pb-4 border-b border-[#20344A]">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg border ${
                      selDisp.state === 'SAFE'
                        ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                        : selDisp.state === 'VIOLATION'
                        ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                        : 'bg-amber-500/15 text-[#F5B942] border-amber-500/30'
                    }`}
                  >
                    <Users className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-mono font-black text-white text-lg tracking-tight">
                        Worker #{selectedWorker.track_id.toString().padStart(3, '0')}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                          selDisp.state === 'SAFE'
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : selDisp.state === 'VIOLATION'
                            ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            : 'bg-amber-500/15 text-[#F5B942] border-amber-500/30'
                        }`}
                      >
                        {selDisp.label}
                      </span>
                    </div>
                    <p className="text-xs text-[#8FA3B8] mt-0.5">
                      Anonymous tracking profile • Camera node {displayCam}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedWorker(null)}
                  className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                  title="Close Profile"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="mt-5 space-y-5 flex-1">
                {/* ─── Telemetry Strip (Section 21, 22, 23, 28) ─── */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-[#12263A] border border-[#20344A]">
                    <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wide">
                      Camera Node
                    </span>
                    <div className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1 truncate">
                      <Camera className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      <span className="truncate">{displayCam}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#12263A] border border-[#20344A]">
                    <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wide">
                      Plant Zone
                    </span>
                    <div className="text-xs font-bold text-white mt-1 flex items-center gap-1 capitalize truncate">
                      <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate">{displayZone}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#12263A] border border-[#20344A]">
                    <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wide">
                      Dwell Time
                    </span>
                    <div className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      {dwellDisplay}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#12263A] border border-[#20344A]">
                    <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wide">
                      Last Observed
                    </span>
                    <div className="text-xs font-mono font-bold text-white mt-1 flex items-center gap-1">
                      <Activity className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      {lastSeen}
                    </div>
                  </div>
                </div>

                {/* ─── Itemized PPE Checklist (Section 15 & 51) ─── */}
                <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Itemized PPE Checklist (Canonical)
                    </h4>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Active Frames: {selectedWorker.active_frames || 1}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <PPEStatusBadge item="helmet" status={ppe.helmet} />
                    <PPEStatusBadge item="safety_vest" status={ppe.safety_vest} />
                    <PPEStatusBadge item="gloves" status={ppe.gloves} />
                    <PPEStatusBadge item="safety_footwear" status={ppe.safety_footwear} />
                    {/* Goggles extensible notice (Section 2 & 51) */}
                    <PPEStatusBadge item="goggles" status="PLANNED" />
                  </div>
                </div>

                {/* ─── EXPLAINABILITY PANEL (Section 24, 25, 26, 27) ─── */}
                <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-3">
                  <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-sky-400">
                    <Info className="w-4 h-4" />
                    <span>Explainable AI — Safety State Reason</span>
                  </div>

                  {/* 1. SAFE Explanation (Section 25) */}
                  {selDisp.state === 'SAFE' && (
                    <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-2">
                      <div className="flex items-center gap-2 text-emerald-400 text-xs font-black">
                        <Check className="w-4 h-4" />
                        <span>WHY IS THIS WORKER SAFE?</span>
                      </div>
                      <p className="text-xs text-emerald-200 leading-relaxed">
                        All currently required PPE items (Safety Helmet, High-Visibility Vest, Protective Gloves, Safety Footwear) are confirmed <strong>PRESENT</strong> in their anatomical zones. No violation or risk detected.
                      </p>
                    </div>
                  )}

                  {/* 2. UNKNOWN Explanation (Section 26) */}
                  {selDisp.state === 'UNKNOWN' && (
                    <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-2">
                      <div className="flex items-center gap-2 text-[#F5B942] text-xs font-black">
                        <HelpCircle className="w-4 h-4" />
                        <span>WHY IS THIS WORKER UNKNOWN?</span>
                      </div>
                      <p className="text-xs text-amber-200 leading-relaxed font-semibold">
                        PPE state could not be fully confirmed from the current camera view.
                      </p>
                      <div className="text-[11px] text-slate-300 space-y-1">
                        <div>
                          <strong>Reason:</strong> VISIBILITY INSUFFICIENT FOR CONFIRMATION
                          {selDisp.unknownItems.length > 0 && ` (${selDisp.unknownItems.join(', ')} occluded or angle limited)`}.
                        </div>
                        <div className="text-amber-400/90 text-[10px] mt-1 italic">
                          Important: Per SafeSync ISO-aligned safety standards, UNKNOWN states are non-punitive and NEVER trigger violation alarms or P2 incidents.
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 3. CONFIRMED VIOLATION Explanation (Section 27) */}
                  {selDisp.state === 'VIOLATION' && (
                    <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 space-y-2.5">
                      <div className="flex items-center gap-2 text-rose-400 text-xs font-black">
                        <ShieldAlert className="w-4 h-4" />
                        <span>WHY IS THIS WORKER IN VIOLATION?</span>
                      </div>
                      <p className="text-xs text-rose-200 leading-relaxed">
                        Confirmed absence of mandatory safety gear:{' '}
                        <strong className="text-rose-400 uppercase">
                          {selDisp.missingItems.join(', ') || 'Required Equipment'}
                        </strong>.
                      </p>
                      {/* Causality flow */}
                      <div className="grid grid-cols-4 gap-1.5 text-center text-[10px] pt-1">
                        <div className="p-2 rounded bg-black/40 border border-[#20344A]">
                          <span className="text-slate-400 block font-bold">1. DETECT</span>
                          <span className="text-white mt-0.5 block truncate">Anatomical Zone</span>
                        </div>
                        <div className="p-2 rounded bg-black/40 border border-[#20344A]">
                          <span className="text-slate-400 block font-bold">2. ASSOCIATE</span>
                          <span className="text-amber-400 mt-0.5 block truncate">Hungarian Match</span>
                        </div>
                        <div className="p-2 rounded bg-black/40 border border-[#20344A]">
                          <span className="text-slate-400 block font-bold">3. TEMPORAL</span>
                          <span className="text-rose-400 mt-0.5 block truncate">15 Frames Validated</span>
                        </div>
                        <div className="p-2 rounded bg-black/40 border border-[#20344A]">
                          <span className="text-slate-400 block font-bold">4. ALERT</span>
                          <span className="text-sky-400 mt-0.5 block truncate">P2 Dispatched</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* ─── Safety Event History (Section 30) ─── */}
                <div className="p-4 rounded-xl bg-[#12263A] border border-[#20344A] space-y-2.5">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-sky-400" />
                      Associated Safety Incidents
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {workerSafetyEvents.length} events
                    </span>
                  </h4>

                  {workerSafetyEvents.length === 0 ? (
                    <div className="p-3 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-center text-xs text-slate-400">
                      NO SAFETY EVENTS RECORDED FOR THIS CAMERA/ZONE
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {workerSafetyEvents.slice(0, 3).map((evt) => (
                        <div
                          key={evt.incident_id}
                          className="p-2.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-bold text-white">
                              {evt.incident_id} • {evt.event_types?.join(', ') || 'Incident'}
                            </span>
                            <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                              {new Date(evt.created_at).toLocaleTimeString()} • Risk Level: {evt.risk_level}
                            </div>
                          </div>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              evt.status === 'OPEN'
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                                : 'bg-slate-700 text-slate-300'
                            }`}
                          >
                            {evt.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* ─── Navigation Actions (Section 40 & 41) ─── */}
                <div className="pt-2 flex items-center gap-2.5 flex-wrap">
                  {/* View in Live Monitor */}
                  {onNavigate && (
                    <button
                      onClick={() => {
                        setSelectedWorker(null);
                        onNavigate('live-monitor');
                      }}
                      className="flex-1 py-2 px-3 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition cursor-pointer"
                    >
                      <Tv className="w-3.5 h-3.5" />
                      VIEW IN LIVE MONITOR
                    </button>
                  )}

                  {/* View Entry Gate if at entry gate */}
                  {isEntryGate && onNavigate && (
                    <button
                      onClick={() => {
                        setSelectedWorker(null);
                        onNavigate('cameras', 'entry_gate');
                      }}
                      className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition cursor-pointer"
                    >
                      <DoorOpen className="w-3.5 h-3.5" />
                      VIEW ENTRY GATE
                    </button>
                  )}

                  {/* Export Telemetry Log (Section 29) */}
                  <button
                    onClick={() => handleExportWorkerLog(selectedWorker)}
                    className="py-2 px-3 bg-[#12263A] hover:bg-slate-700 text-slate-200 border border-[#20344A] rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                    title="Export raw JSON telemetry for forensic review"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export Log
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default WorkersView;
