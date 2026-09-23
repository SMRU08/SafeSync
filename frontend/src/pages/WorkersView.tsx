/**
 * WorkersView.tsx — RAKSHYA VISION Professional SOC
 * Real-Time Worker Tracking & PPE Compliance Evaluation.
 * Features live ByteTrack tracking table, itemized compliance checklist (Helmet, Vest, Gloves, Footwear),
 * strict UNKNOWN separation, and slide-over worker detail drawer.
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
} from 'lucide-react';
import { WorkerTrack, ComplianceSummary, PPEPresence } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface WorkersViewProps {
  complianceConfig?: any;
}

export const WorkersView: React.FC<WorkersViewProps> = () => {
  const [workers, setWorkers] = useState<WorkerTrack[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<WorkerTrack | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompliance, setFilterCompliance] = useState<'ALL' | 'COMPLIANT' | 'VIOLATION'>('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchWorkers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/compliance/live`);
      if (response.ok) {
        const data = await response.json();
        if (data) {
          if (Array.isArray(data.workers)) {
            setWorkers(data.workers);
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
  }, []);

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
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <Check className="w-2.5 h-2.5" /> Present
        </span>
      );
    }
    if (status === 'ABSENT') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <X className="w-2.5 h-2.5" /> Absent
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500 border border-slate-200">
        <Minus className="w-2.5 h-2.5" /> Unknown
      </span>
    );
  };

  const total = summary?.total_workers ?? workers.length;
  const compliant = summary?.compliant_workers ?? workers.filter((w) => w.overall_compliant).length;
  const nonCompliant = summary?.non_compliant_workers ?? workers.filter((w) => !w.overall_compliant).length;
  const compliancePct = total > 0 ? Math.round((compliant / total) * 100) : 100;

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

        <button
          onClick={fetchWorkers}
          className="self-start sm:self-auto px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-xs flex items-center gap-1.5 cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-sky-600" />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* KPI Metrics Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Tracked Workers</span>
          <div className="text-xl font-extrabold text-slate-900 font-mono-nums mt-1">
            {total} Active
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Live ByteTrack detections</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Fully Compliant</span>
          <div className="text-xl font-extrabold text-emerald-600 font-mono-nums mt-1">
            {compliant}
          </div>
          <p className="text-[10px] text-emerald-600 mt-0.5">All required PPE verified</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Active Infractions</span>
          <div
            className={`text-xl font-extrabold font-mono-nums mt-1 ${
              nonCompliant > 0 ? 'text-rose-600' : 'text-slate-900'
            }`}
          >
            {nonCompliant}
          </div>
          <p className="text-[10px] text-rose-500 mt-0.5">Missing safety equipment</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Fleet Compliance Rate</span>
          <div className="text-xl font-extrabold text-slate-900 font-mono-nums mt-1">
            {compliancePct}%
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1 mt-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-1 rounded-full"
              style={{ width: `${compliancePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Ledger Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        {/* Table Filter Toolbar */}
        <div className="p-3 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white">
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Worker ID or Zone..."
                className="w-full bg-slate-50 border border-slate-200 text-xs rounded-md pl-8 pr-3 py-1.5 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div className="flex items-center bg-slate-100 p-0.5 rounded-md text-xs font-medium">
              <button
                onClick={() => setFilterCompliance('ALL')}
                className={`px-2.5 py-1 rounded transition cursor-pointer ${
                  filterCompliance === 'ALL'
                    ? 'bg-white text-slate-800 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({workers.length})
              </button>
              <button
                onClick={() => setFilterCompliance('COMPLIANT')}
                className={`px-2.5 py-1 rounded transition cursor-pointer ${
                  filterCompliance === 'COMPLIANT'
                    ? 'bg-white text-emerald-700 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Compliant ({compliant})
              </button>
              <button
                onClick={() => setFilterCompliance('VIOLATION')}
                className={`px-2.5 py-1 rounded transition cursor-pointer ${
                  filterCompliance === 'VIOLATION'
                    ? 'bg-white text-rose-700 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Violations ({nonCompliant})
              </button>
            </div>
          </div>

          <span className="text-[11px] text-slate-400 font-mono-nums">
            Showing {filteredWorkers.length} tracked workers
          </span>
        </div>

        {/* Ledger Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold text-[10px] uppercase tracking-wider">
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
              {isLoading && workers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-400">
                    Loading live worker tracks...
                  </td>
                </tr>
              ) : filteredWorkers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-slate-400">
                    <ShieldCheck className="w-8 h-8 text-emerald-500 mx-auto mb-1.5" />
                    <p className="text-xs font-semibold text-slate-700">No Active Workers Found</p>
                    <p className="text-[10px] text-slate-400">
                      Stand in front of the active camera to register live ByteTrack detection.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredWorkers.map((w) => {
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
                      <td className="py-2.5 px-3 font-mono-nums text-slate-600">
                        CAM-01
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {w.zone_id || 'production_floor'}
                      </td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.helmet)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.safety_vest)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.gloves)}</td>
                      <td className="py-2.5 px-3">{renderBadge(w.ppe_status?.safety_footwear)}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isCompliant
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-rose-100 text-rose-800'
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
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition cursor-pointer"
                        >
                          <Eye className="w-3 h-3 inline mr-1" /> Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-Over Worker Detail Drawer */}
      {selectedWorker && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-md bg-white shadow-2xl h-full flex flex-col p-5 overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-sky-600" />
                <h3 className="font-extrabold text-slate-900 text-base">
                  Worker #{selectedWorker.track_id} Detail
                </h3>
              </div>
              <button
                onClick={() => setSelectedWorker(null)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Tracking Status:</span>
                  <span
                    className={`font-bold ${
                      selectedWorker.overall_compliant ? 'text-emerald-600' : 'text-rose-600'
                    }`}
                  >
                    {selectedWorker.overall_compliant ? 'Compliant' : 'Non-Compliant'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Zone:</span>
                  <span className="font-medium text-slate-800">
                    {selectedWorker.zone_id || 'production_floor'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Active Tracking Frames:</span>
                  <span className="font-mono-nums font-bold text-slate-800">
                    {selectedWorker.active_frames || 1} frames
                  </span>
                </div>
              </div>

              {/* PPE Verification Breakdown */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wider">
                  Itemized PPE Checklist
                </h4>
                <div className="space-y-2">
                  {[
                    { label: '🪖 Safety Helmet', status: selectedWorker.ppe_status?.helmet },
                    { label: '🦺 High-Visibility Vest', status: selectedWorker.ppe_status?.safety_vest },
                    { label: '🧤 Safety Gloves', status: selectedWorker.ppe_status?.gloves },
                    { label: '🥾 Safety Footwear', status: selectedWorker.ppe_status?.safety_footwear },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg border border-slate-200 bg-white flex items-center justify-between text-xs"
                    >
                      <span className="font-medium text-slate-800">{item.label}</span>
                      {renderBadge(item.status)}
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setSelectedWorker(null)}
                className="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold transition mt-6 cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkersView;
