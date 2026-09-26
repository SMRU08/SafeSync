/**
 * WorkersView.tsx — SafeSync Professional SOC
 * Enhanced Real-Time Worker Tracking, PPE Compliance & Incident Management.
 * Features dual Grid/Ledger view modes, itemized compliance checklist,
 * temporal tracking analytics, and forensic slide-over profile drawer.
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldCheck,
  Search,
  RefreshCw,
  Check,
  X,
  Minus,
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
} from 'lucide-react';
import { WorkerTrack, ComplianceSummary, PPEPresence } from '../types';
import { API_BASE_URL } from '../utils/constants';
import { WorkerComplianceCard } from '../components/WorkerComplianceCard';

interface WorkersViewProps {
  complianceConfig?: any;
  onOpenEnrollModal?: () => void;
}

export const WorkersView: React.FC<WorkersViewProps> = ({ onOpenEnrollModal }) => {
  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<WorkerTrack | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompliance, setFilterCompliance] = useState<'ALL' | 'COMPLIANT' | 'VIOLATION'>('ALL');
  const [viewMode, setViewMode] = useState<'GRID' | 'TABLE'>('GRID');
  const [isLoading, setIsLoading] = useState(true);

  const fetchWorkers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/compliance/live`);
      if (response.ok) {
        const data = await response.json();
        if (data) {
          if (Array.isArray(data.workers)) {
            setWorkers(data.workers);
            // If drawer is open, keep selected worker updated
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
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 1500);
    return () => clearInterval(interval);
  }, [selectedWorker?.track_id]);

  const filteredWorkers = workers.filter((w) => {
    if (filterCompliance === 'COMPLIANT' && !w.overall_compliant) return false;
    if (filterCompliance === 'VIOLATION' && w.overall_compliant) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        w.track_id.toString().includes(q) ||
        (w.zone_id && w.zone_id.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const renderBadge = (status?: PPEPresence) => {
    if (status === 'PRESENT') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <Check className="w-2.5 h-2.5" /> Present
        </span>
      );
    }
    if (status === 'ABSENT') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <X className="w-2.5 h-2.5" /> Absent
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500 border border-slate-200">
        <Minus className="w-2.5 h-2.5" /> Unknown
      </span>
    );
  };

  const total = summary?.total_workers ?? workers.length;
  const compliant = summary?.compliant_workers ?? workers.filter((w) => w.overall_compliant).length;
  const nonCompliant = summary?.non_compliant_workers ?? workers.filter((w) => !w.overall_compliant).length;
  const compliancePct = total > 0 ? Math.round((compliant / total) * 100) : 100;

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
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-sky-600" />
            Workers &amp; PPE Compliance Monitoring
          </h2>
          <p className="text-xs text-slate-500">
            Real-time optical worker tracking, spatial PPE checklist auditing, and temporal compliance verification
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-white border border-slate-200 rounded-lg p-0.5 shadow-xs">
            <button
              onClick={() => setViewMode('GRID')}
              className={`p-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                viewMode === 'GRID' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Card Grid View"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Cards</span>
            </button>
            <button
              onClick={() => setViewMode('TABLE')}
              className={`p-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                viewMode === 'TABLE' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Table Ledger View"
            >
              <List className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ledger</span>
            </button>
          </div>

          <button
            onClick={fetchWorkers}
            className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-xs flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-sky-600 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {onOpenEnrollModal && (
            <button
              onClick={onOpenEnrollModal}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 border border-emerald-700 text-xs font-bold text-white transition shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Enroll Worker</span>
            </button>
          )}
        </div>
      </div>

      {/* KPI Metrics Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Tracked Workers</span>
          <div className="text-2xl font-black text-slate-900 font-mono-nums mt-1">
            {total} Active
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Live ByteTrack confirmed tracks</p>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wide">Fully Compliant</span>
          <div className="text-2xl font-black text-emerald-600 font-mono-nums mt-1">
            {compliant}
          </div>
          <p className="text-[10px] text-emerald-600 mt-0.5">All required PPE verified</p>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-rose-700 uppercase tracking-wide">Active Violations</span>
          <div
            className={`text-2xl font-black font-mono-nums mt-1 ${
              nonCompliant > 0 ? 'text-rose-600' : 'text-slate-900'
            }`}
          >
            {nonCompliant}
          </div>
          <p className="text-[10px] text-rose-500 mt-0.5">Safety policy non-compliance</p>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Compliance Index</span>
          <div className="text-2xl font-black text-slate-900 font-mono-nums mt-1">
            {compliancePct}%
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className={`h-1.5 rounded-full transition-all duration-500 ${
                compliancePct >= 80 ? 'bg-emerald-500' : compliancePct >= 50 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${compliancePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Worker ID or Zone..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-8 pr-3 py-1.5 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500 font-medium text-slate-800"
            />
          </div>

          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-medium">
            <button
              onClick={() => setFilterCompliance('ALL')}
              className={`px-3 py-1 rounded-md transition cursor-pointer ${
                filterCompliance === 'ALL'
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({workers.length})
            </button>
            <button
              onClick={() => setFilterCompliance('COMPLIANT')}
              className={`px-3 py-1 rounded-md transition cursor-pointer ${
                filterCompliance === 'COMPLIANT'
                  ? 'bg-white text-emerald-700 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Compliant ({compliant})
            </button>
            <button
              onClick={() => setFilterCompliance('VIOLATION')}
              className={`px-3 py-1 rounded-md transition cursor-pointer ${
                filterCompliance === 'VIOLATION'
                  ? 'bg-white text-rose-700 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Violations ({nonCompliant})
            </button>
          </div>
        </div>

        <span className="text-[11px] text-slate-400 font-mono-nums">
          Showing <strong>{filteredWorkers.length}</strong> of {workers.length} active workers
        </span>
      </div>

      {/* Content View: Cards vs Table */}
      {filteredWorkers.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-slate-800">No Active Workers Matching Filter</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            Ensure camera stream is connected or stand in front of active monitoring feed to register live detections.
          </p>
        </div>
      ) : viewMode === 'GRID' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5">
          {filteredWorkers.map((w) => (
            <WorkerComplianceCard
              key={w.track_id}
              worker={w}
              onInspect={(worker) => setSelectedWorker(worker)}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-3">Worker ID</th>
                  <th className="py-2.5 px-3">Camera Node</th>
                  <th className="py-2.5 px-3">Plant Zone</th>
                  <th className="py-2.5 px-3">Helmet</th>
                  <th className="py-2.5 px-3">Safety Vest</th>
                  <th className="py-2.5 px-3">Gloves</th>
                  <th className="py-2.5 px-3">Footwear</th>
                  <th className="py-2.5 px-3">Compliance</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredWorkers.map((w) => {
                  const isCompliant = w.overall_compliant;
                  return (
                    <tr
                      key={w.track_id}
                      onClick={() => setSelectedWorker(w)}
                      className="hover:bg-sky-50/40 transition cursor-pointer"
                    >
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">
                        #{w.track_id.toString().padStart(3, '0')}
                      </td>
                      <td className="py-2.5 px-3 font-mono-nums text-slate-600">CAM-01</td>
                      <td className="py-2.5 px-3 text-slate-600">{w.zone_id || 'Production Floor'}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.helmet)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.safety_vest)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.gloves)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.safety_footwear)}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isCompliant ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {isCompliant ? 'COMPLIANT' : 'VIOLATION'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedWorker(w);
                          }}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-semibold transition cursor-pointer inline-flex items-center gap-1"
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

      {/* Enhanced Slide-Over Worker Forensic Profile Drawer */}
      {selectedWorker && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/50 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-white shadow-2xl h-full flex flex-col p-6 overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div className="flex items-center gap-3">
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-base ${
                    selectedWorker.overall_compliant ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}
                >
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-black text-slate-900 text-lg tracking-tight">
                      Worker #{selectedWorker.track_id.toString().padStart(3, '0')} Profile
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                        selectedWorker.overall_compliant
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : 'bg-rose-100 text-rose-800 border border-rose-300'
                      }`}
                    >
                      {selectedWorker.overall_compliant ? 'COMPLIANT' : 'VIOLATION'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">Live safety audit and itemized PPE adherence log</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedWorker(null)}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="mt-5 space-y-5 flex-1">
              {/* Telemetry Metrics Grid */}
              <div className="grid grid-cols-3 gap-2.5">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Plant Zone</span>
                  <div className="text-xs font-extrabold text-slate-800 mt-1 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-sky-600" />
                    {selectedWorker.zone_id || 'Production Floor'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Active Dwell Time</span>
                  <div className="text-xs font-extrabold text-slate-800 mt-1 font-mono-nums flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-sky-600" />
                    {Math.round((selectedWorker.active_frames || 1) / 30)}s
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Tracking Frames</span>
                  <div className="text-xs font-extrabold text-slate-800 mt-1 font-mono-nums flex items-center gap-1">
                    <Activity className="w-3.5 h-3.5 text-sky-600" />
                    {selectedWorker.active_frames || 1}
                  </div>
                </div>
              </div>

              {/* Spatial Coordinates Box */}
              <div className="p-3 rounded-xl bg-slate-900 text-white font-mono text-[11px] space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Bounding Box [x1, y1, x2, y2]:</span>
                  <span className="text-sky-300">
                    [{selectedWorker.bbox ? selectedWorker.bbox.map((v) => Math.round(v)).join(', ') : 'N/A'}]
                  </span>
                </div>
                {selectedWorker.normalized_bbox && (
                  <div className="flex justify-between text-slate-400">
                    <span>Normalized BBox:</span>
                    <span className="text-emerald-400">
                      [{selectedWorker.normalized_bbox.map((v) => v.toFixed(3)).join(', ')}]
                    </span>
                  </div>
                )}
              </div>

              {/* Itemized PPE Standards Audit */}
              <div>
                <h4 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-sky-600" />
                  Itemized Regulatory PPE Checklist
                </h4>

                <div className="space-y-2">
                  {[
                    {
                      label: 'Industrial Safety Helmet',
                      standard: 'EN 397 / ANSI Z89.1 Type 1 Class E',
                      status: selectedWorker.ppe_status?.helmet,
                      icon: <HardHat className="w-4 h-4 text-amber-500" />,
                    },
                    {
                      label: 'High-Visibility Safety Vest',
                      standard: 'EN ISO 20471 Class 2 Fluorescent',
                      status: selectedWorker.ppe_status?.safety_vest,
                      icon: <Shirt className="w-4 h-4 text-emerald-500" />,
                    },
                    {
                      label: 'Protective Work Gloves',
                      standard: 'EN 388 Mechanical & Puncture Guard',
                      status: selectedWorker.ppe_status?.gloves,
                      icon: <Hand className="w-4 h-4 text-sky-500" />,
                    },
                    {
                      label: 'Steel-Toe Safety Footwear',
                      standard: 'EN ISO 20345 S3 Crush Resistant',
                      status: selectedWorker.ppe_status?.safety_footwear,
                      icon: <Footprints className="w-4 h-4 text-indigo-500" />,
                    },
                  ].map((item, idx) => {
                    const isOk = item.status === 'PRESENT';
                    const isMissing = item.status === 'ABSENT';
                    return (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border flex items-center justify-between transition ${
                          isOk
                            ? 'bg-emerald-50/40 border-emerald-200'
                            : isMissing
                            ? 'bg-rose-50/50 border-rose-200 ring-1 ring-rose-100'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-1.5 rounded-lg bg-white shadow-xs border border-slate-100">
                            {item.icon}
                          </div>
                          <div>
                            <span className="text-xs font-bold text-slate-900 block">{item.label}</span>
                            <span className="text-[10px] text-slate-400 font-mono">{item.standard}</span>
                          </div>
                        </div>

                        <div>{renderBadge(item.status)}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Forensic Action Toolbar */}
              <div className="pt-4 border-t border-slate-200 space-y-2">
                <button
                  onClick={() => handleExportWorkerLog(selectedWorker)}
                  className="w-full py-2.5 px-3 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <Download className="w-4 h-4" /> Export Worker Forensic Audit JSON
                </button>

                <button
                  onClick={() => setSelectedWorker(null)}
                  className="w-full py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition cursor-pointer"
                >
                  Close Profile Inspector
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
