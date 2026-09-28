/**
 * WorkersView.tsx — SafeSync Professional SOC
 * Real-Time Worker Tracking & PPE Compliance Auditing (Phase 9 & 10).
 * Features dual Grid/Ledger view modes, itemized compliance checklist,
 * strict distinction between ABSENT and UNKNOWN states, and slide-over forensic profile drawer.
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldCheck,
  Search,
  Check,
  X,
  HelpCircle,
  Eye,
  LayoutGrid,
  List,
  MapPin,
  Clock,
  HardHat,
  Shirt,
  Hand,
  Footprints,
  Download,
  Activity,
  UserPlus,
  ShieldAlert,
} from 'lucide-react';
import { WorkerTrack, ComplianceSummary, PPEPresence } from '../types';
import { API_BASE_URL } from '../utils/constants';
import { WorkerComplianceCard } from '../components/WorkerComplianceCard';
import { EmptyState } from '../components/ui/EmptyState';

interface WorkersViewProps {
  complianceConfig?: any;
  onOpenEnrollModal?: () => void;
}

export const WorkersView: React.FC<WorkersViewProps> = ({ onOpenEnrollModal }) => {
  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<WorkerTrack | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompliance, setFilterCompliance] = useState<'ALL' | 'COMPLIANT' | 'VIOLATION' | 'UNKNOWN'>('ALL');
  const [viewMode, setViewMode] = useState<'GRID' | 'TABLE'>('GRID');

  const fetchWorkers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/compliance/live`);
      if (response.ok) {
        const data = await response.json();
        if (data) {
          if (Array.isArray(data.workers)) {
            setWorkers(data.workers);
            if (selectedWorker) {
              const updated = data.workers.find((w: WorkerTrack) => w.track_id === selectedWorker.track_id);
              if (updated) setSelectedWorker(updated);
            }
          }
          if (data.summary) {
            setSummary(data.summary);
          }
        }
      }
    } catch {
      // Tolerate dropouts
    }
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 1500);
    return () => clearInterval(interval);
  }, [selectedWorker?.track_id]);

  const filteredWorkers = workers.filter((w) => {
    const isUnknown = Object.values(w.ppe_status || {}).some((st) => st === 'UNKNOWN');
    if (filterCompliance === 'COMPLIANT' && !w.overall_compliant) return false;
    if (filterCompliance === 'VIOLATION' && w.overall_compliant) return false;
    if (filterCompliance === 'UNKNOWN' && !isUnknown) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        w.track_id.toString().includes(q) ||
        (w.zone_id && w.zone_id.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Strict distinction: UNKNOWN must NEVER look like ABSENT
  const renderBadge = (status?: PPEPresence) => {
    if (status === 'PRESENT') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <Check className="w-2.5 h-2.5" /> Present
        </span>
      );
    }
    if (status === 'ABSENT') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
          <X className="w-2.5 h-2.5" /> Absent
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <HelpCircle className="w-2.5 h-2.5" /> Unknown
      </span>
    );
  };

  const total = summary?.total_workers ?? workers.length;
  const compliant = summary?.compliant_workers ?? workers.filter((w) => w.overall_compliant).length;
  const nonCompliant = summary?.non_compliant_workers ?? workers.filter((w) => !w.overall_compliant).length;
  const unknownCount = workers.filter((w) =>
    Object.values(w.ppe_status || {}).some((st) => st === 'UNKNOWN')
  ).length;
  const hasWorkers = total > 0;
  const compliancePct = hasWorkers ? Math.round((compliant / total) * 100) : null;

  const handleExportWorkerLog = (w: WorkerTrack) => {
    const reportData = {
      worker_id: w.track_id,
      zone: w.zone_id || 'production_floor',
      compliant: w.overall_compliant,
      ppe_status: w.ppe_status,
      active_frames: w.active_frames,
      bounding_box: w.bbox,
      normalized_bbox: w.normalized_bbox,
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `worker_${w.track_id}_safety_log.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#070b14] text-slate-100 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
                Workers &amp; PPE Compliance
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time optical worker tracking, spatial PPE checklist auditing, and temporal compliance verification
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls: Search & Register */}
        <div className="flex items-center gap-3">
          <div className="relative w-56">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Worker ID, Zone..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          {onOpenEnrollModal && (
            <button
              onClick={onOpenEnrollModal}
              className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
            >
              <UserPlus className="w-3.5 h-3.5" />
              Enroll Face Biometrics
            </button>
          )}
        </div>
      </div>

      {/* ─── Summary KPI Ribbon (Phase 9: Tracked, Compliant, Non-Compliant, Unknown) ─── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        {/* Tracked Workers */}
        <div className="glass-card p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Tracked Personnel
          </span>
          <div className="text-2xl font-black text-white font-mono-nums mt-1 leading-none">
            {total}
          </div>
          <span className="text-[10px] text-sky-400 font-medium mt-1">Live in video feeds</span>
        </div>

        {/* Compliant */}
        <div className="glass-card p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Compliant Personnel
          </span>
          <div className="text-2xl font-black text-emerald-400 font-mono-nums mt-1 leading-none">
            {compliant}
          </div>
          <span className="text-[10px] text-emerald-400 font-medium mt-1">
            {hasWorkers ? `${compliancePct}% rate` : 'N/A — No workers'}
          </span>
        </div>

        {/* Non-Compliant */}
        <div className="glass-card p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Violations (Non-Compliant)
          </span>
          <div className="text-2xl font-black text-rose-400 font-mono-nums mt-1 leading-none">
            {nonCompliant}
          </div>
          <span className="text-[10px] text-rose-400 font-medium mt-1">Missing mandatory gear</span>
        </div>

        {/* Unknown Status */}
        <div className="glass-card p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Occluded / Unknown
          </span>
          <div className="text-2xl font-black text-amber-400 font-mono-nums mt-1 leading-none">
            {unknownCount}
          </div>
          <span className="text-[10px] text-amber-400 font-medium mt-1">Awaiting clear angle</span>
        </div>
      </div>

      {/* Filter Tabs & View Mode Switcher */}
      <div className="flex items-center justify-between gap-3 pb-1">
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          {(['ALL', 'COMPLIANT', 'VIOLATION', 'UNKNOWN'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterCompliance(tab)}
              className={`px-3 py-1 font-semibold rounded-md transition ${
                filterCompliance === tab
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab === 'ALL' ? 'All Personnel' : tab === 'COMPLIANT' ? 'Compliant' : tab === 'VIOLATION' ? 'Violations' : 'Unknown'}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900 border border-slate-800">
          <button
            onClick={() => setViewMode('GRID')}
            className={`p-1.5 rounded transition ${viewMode === 'GRID' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'}`}
            title="Grid Cards"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('TABLE')}
            className={`p-1.5 rounded transition ${viewMode === 'TABLE' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'}`}
            title="Table Ledger"
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Personnel Grid / Table */}
      {filteredWorkers.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No Active Workers in View"
          description="There are currently no workers detected matching the selected filter criteria."
        />
      ) : viewMode === 'GRID' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredWorkers.map((w) => (
            <WorkerComplianceCard
              key={w.track_id}
              worker={w}
              onInspect={(worker) => setSelectedWorker(worker)}
            />
          ))}
        </div>
      ) : (
        <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase tracking-wider">
                  <th className="py-3 px-4">Worker ID</th>
                  <th className="py-3 px-4">Camera Node</th>
                  <th className="py-3 px-4">Plant Zone</th>
                  <th className="py-3 px-4">Helmet</th>
                  <th className="py-3 px-4">Safety Vest</th>
                  <th className="py-3 px-4">Gloves</th>
                  <th className="py-3 px-4">Footwear</th>
                  <th className="py-3 px-4">Compliance</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredWorkers.map((w) => {
                  const isCompliant = w.overall_compliant;
                  return (
                    <tr
                      key={w.track_id}
                      onClick={() => setSelectedWorker(w)}
                      className="hover:bg-slate-900/80 transition cursor-pointer"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        #{w.track_id.toString().padStart(3, '0')}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">CAM-01</td>
                      <td className="py-3 px-4 text-slate-300">{w.zone_id || 'Production Floor'}</td>
                      <td className="py-3 px-4">{renderBadge(w.ppe_status?.helmet)}</td>
                      <td className="py-3 px-4">{renderBadge(w.ppe_status?.safety_vest)}</td>
                      <td className="py-3 px-4">{renderBadge(w.ppe_status?.gloves)}</td>
                      <td className="py-3 px-4">{renderBadge(w.ppe_status?.safety_footwear)}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                            isCompliant
                              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                              : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                          }`}
                        >
                          {isCompliant ? 'COMPLIANT' : 'VIOLATION'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedWorker(w);
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-semibold transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" /> Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slide-Over Worker Forensic Profile Drawer */}
      {selectedWorker && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-[#0c1424] text-slate-100 border-l border-slate-800 shadow-2xl h-full flex flex-col p-6 overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-base border ${
                    selectedWorker.overall_compliant
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  }`}
                >
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-black text-white text-lg tracking-tight">
                      Worker #{selectedWorker.track_id.toString().padStart(3, '0')} Profile
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                        selectedWorker.overall_compliant
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                          : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {selectedWorker.overall_compliant ? 'COMPLIANT' : 'VIOLATION'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">Live safety audit and itemized PPE adherence log</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedWorker(null)}
                className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="mt-5 space-y-5 flex-1">
              {/* Telemetry Metrics Grid */}
              <div className="grid grid-cols-3 gap-2.5">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Plant Zone</span>
                  <div className="text-xs font-extrabold text-white mt-1 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-sky-400" />
                    {selectedWorker.zone_id || 'Production Floor'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Dwell Time</span>
                  <div className="text-xs font-extrabold text-white mt-1 font-mono-nums flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-sky-400" />
                    {Math.round((selectedWorker.active_frames || 1) / 30)}s
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Tracking Frames</span>
                  <div className="text-xs font-extrabold text-white mt-1 font-mono-nums flex items-center gap-1">
                    <Activity className="w-3.5 h-3.5 text-sky-400" />
                    {selectedWorker.active_frames || 1}
                  </div>
                </div>
              </div>

              {/* Itemized PPE Checklist */}
              <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Itemized PPE Checklist
                </h4>

                <div className="space-y-2.5 text-xs">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 border border-slate-800">
                    <span className="flex items-center gap-2 text-slate-300">
                      <HardHat className="w-4 h-4 text-amber-400" /> Hard Hat / Safety Helmet
                    </span>
                    {renderBadge(selectedWorker.ppe_status?.helmet)}
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 border border-slate-800">
                    <span className="flex items-center gap-2 text-slate-300">
                      <Shirt className="w-4 h-4 text-yellow-400" /> High-Visibility Vest
                    </span>
                    {renderBadge(selectedWorker.ppe_status?.safety_vest)}
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 border border-slate-800">
                    <span className="flex items-center gap-2 text-slate-300">
                      <Hand className="w-4 h-4 text-sky-400" /> Protective Gloves
                    </span>
                    {renderBadge(selectedWorker.ppe_status?.gloves)}
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/70 border border-slate-800">
                    <span className="flex items-center gap-2 text-slate-300">
                      <Footprints className="w-4 h-4 text-indigo-400" /> Safety Footwear
                    </span>
                    {renderBadge(selectedWorker.ppe_status?.safety_footwear)}
                  </div>
                </div>
              </div>

              {/* Violation Causality Flow: Detection -> Validation -> Violation -> Alert */}
              {!selectedWorker.overall_compliant && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 space-y-2.5">
                  <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4" />
                    Infraction Causality Pipeline
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                      <span className="text-slate-400 block font-bold">1. DETECT</span>
                      <span className="text-white mt-1 block">Head / Torso</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                      <span className="text-slate-400 block font-bold">2. VALIDATE</span>
                      <span className="text-amber-400 mt-1 block">Conf &gt; 0.40</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                      <span className="text-slate-400 block font-bold">3. VIOLATION</span>
                      <span className="text-rose-400 mt-1 block">Gear Absent</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                      <span className="text-slate-400 block font-bold">4. ALERT</span>
                      <span className="text-sky-400 mt-1 block">P2 Dispatched</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  onClick={() => handleExportWorkerLog(selectedWorker)}
                  className="flex-1 py-2 px-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export Telemetry Log
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkersView;
