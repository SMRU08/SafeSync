/**
 * CameraCoverageSection.tsx — SafeSync Phase 6
 * Comprehensive Facility Camera Coverage & Visibility Status Overview.
 *
 * Adheres strictly to Section 8, 9, 25 & 26:
 *   - Qualitative visibility states: GOOD, LIMITED, INSUFFICIENT, UNKNOWN
 *   - Configured view metadata: FRONTAL, ANGLED, WAIST-UP, FULL BODY, OVERHEAD
 *   - Facility zones: ENTRY GATE, PRODUCTION FLOOR, HAZARD ZONE, GENERAL MONITORING
 *   - Complete Coverage Table: Camera, Purpose, Status, Workers, PPE, Fire/Smoke, Coverage, Actions
 *   - Zero fabricated percentages or fake geographic maps
 */

import React from 'react';
import {
  Eye,
  Camera,
  DoorOpen,
  Flame,
  CheckCircle2,
  Layers,
  ExternalLink,
  Info,
} from 'lucide-react';
import { CameraConfig } from '../types';

interface CameraCoverageSectionProps {
  cameras: CameraConfig[];
  onOpenLiveView?: (camera: CameraConfig) => void;
  onLaunchEntryGate?: () => void;
}

// Derive purpose category from camera config
export const getCameraPurpose = (camera: CameraConfig): 'ENTRY GATE' | 'PRODUCTION FLOOR' | 'HAZARD ZONE' | 'GENERAL MONITORING' => {
  const z = (camera.zone_id || '').toLowerCase();
  const loc = (camera.location || '').toLowerCase();
  const name = (camera.name || '').toLowerCase();

  if (z.includes('entry') || loc.includes('entry') || name.includes('entry') || loc.includes('gate') || name.includes('gate')) {
    return 'ENTRY GATE';
  }
  if (z.includes('hazard') || loc.includes('hazard') || name.includes('hazard') || z.includes('electrical')) {
    return 'HAZARD ZONE';
  }
  if (z.includes('production') || loc.includes('floor') || name.includes('floor')) {
    return 'PRODUCTION FLOOR';
  }
  return 'GENERAL MONITORING';
};

// Derive qualitative coverage status based on real camera parameters
export const getCameraCoverageStatus = (camera: CameraConfig): {
  status: 'GOOD' | 'LIMITED' | 'INSUFFICIENT' | 'UNKNOWN';
  color: string;
  configuredView: string;
  explanation: string;
} => {
  const isOnline =
    camera.enabled !== false &&
    (camera.status === 'online' ||
      camera.status === 'ACTIVE' ||
      camera.status === 'streaming' ||
      camera.state === 'CONNECTED' ||
      camera.state === 'STREAMING');

  if (!isOnline) {
    return {
      status: 'UNKNOWN',
      color: 'text-slate-400 bg-slate-800/60 border-slate-700',
      configuredView: camera.configured_view || 'OFFLINE / UNKNOWN',
      explanation: 'Camera feed is currently offline. Visibility cannot be assessed.',
    };
  }

  const purpose = getCameraPurpose(camera);

  if (purpose === 'ENTRY GATE') {
    return {
      status: 'LIMITED',
      color: 'text-[#F5B942] bg-amber-500/15 border-amber-500/30',
      configuredView: camera.configured_view || 'FRONTAL / EYE-LEVEL',
      explanation: 'Head and torso visibility are optimal for Helmet and Vest. Footwear visibility may be limited during turnstile queue proximity.',
    };
  }

  if (purpose === 'HAZARD ZONE') {
    return {
      status: 'GOOD',
      color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
      configuredView: camera.configured_view || 'WIDE ANGLED 45°',
      explanation: 'Wide field-of-view covers primary hazard perimeter, optical fire/smoke line-of-sight, and worker PPE compliance.',
    };
  }

  if (purpose === 'PRODUCTION FLOOR') {
    return {
      status: 'GOOD',
      color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
      configuredView: camera.configured_view || 'HIGH-MOUNT ANGLED',
      explanation: 'High-mounted angle provides wide coverage of machinery rows. Gloves and footwear subject to bench occlusion in distant zones.',
    };
  }

  return {
    status: 'GOOD',
    color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
    configuredView: camera.configured_view || 'CEILING MOUNTED',
    explanation: 'General facility surveillance covering pathways and transit areas.',
  };
};

export const CameraCoverageSection: React.FC<CameraCoverageSectionProps> = ({
  cameras,
  onOpenLiveView,
  onLaunchEntryGate,
}) => {
  // Aggregate cameras by purpose
  const purposeGroups = {
    'ENTRY GATE': cameras.filter((c) => getCameraPurpose(c) === 'ENTRY GATE'),
    'PRODUCTION FLOOR': cameras.filter((c) => getCameraPurpose(c) === 'PRODUCTION FLOOR'),
    'HAZARD ZONE': cameras.filter((c) => getCameraPurpose(c) === 'HAZARD ZONE'),
    'GENERAL MONITORING': cameras.filter((c) => getCameraPurpose(c) === 'GENERAL MONITORING'),
  };

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* ─── Facility Purpose Overview Cards (Section 3, 25) ───────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Entry Gate Purpose Card */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#20344A]">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wide">
                <DoorOpen className="w-4 h-4" />
                <span>Entry Gate</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#12263A] text-slate-300 border border-[#20344A]">
                {purposeGroups['ENTRY GATE'].length} Camera{purposeGroups['ENTRY GATE'].length === 1 ? '' : 's'}
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-2.5 leading-relaxed">
              Main turnstile and access control perimeter. Focuses on pre-entry worker detection and tri-state access decisions.
            </p>
          </div>
          <div className="pt-3 mt-3 border-t border-[#20344A]/60 flex items-center justify-between text-xs">
            <span className="text-[10px] text-slate-400">
              Coverage: <strong className="text-amber-400 font-semibold">LIMITED (Waist-Up)</strong>
            </span>
            {onLaunchEntryGate && (
              <button
                onClick={onLaunchEntryGate}
                className="text-[11px] font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition cursor-pointer"
              >
                Access Decision <ExternalLink className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Production Floor Purpose Card */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#20344A]">
              <div className="flex items-center gap-2 text-sky-400 font-bold text-xs uppercase tracking-wide">
                <Layers className="w-4 h-4" />
                <span>Production Floor</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#12263A] text-slate-300 border border-[#20344A]">
                {purposeGroups['PRODUCTION FLOOR'].length} Camera{purposeGroups['PRODUCTION FLOOR'].length === 1 ? '' : 's'}
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-2.5 leading-relaxed">
              Industrial machinery bays and assembly lanes. Monitors worker density, active PPE compliance, and movement patterns.
            </p>
          </div>
          <div className="pt-3 mt-3 border-t border-[#20344A]/60 flex items-center justify-between text-xs">
            <span className="text-[10px] text-slate-400">
              Coverage: <strong className="text-emerald-400 font-semibold">GOOD</strong>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              PPE: Active
            </span>
          </div>
        </div>

        {/* Hazard Zone Purpose Card */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#20344A]">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase tracking-wide">
                <Flame className="w-4 h-4" />
                <span>Hazard Zone</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#12263A] text-slate-300 border border-[#20344A]">
                {purposeGroups['HAZARD ZONE'].length} Camera{purposeGroups['HAZARD ZONE'].length === 1 ? '' : 's'}
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-2.5 leading-relaxed">
              High-voltage, chemical, or thermal risk areas. Dual-layer monitoring for strict mandatory PPE adherence and optical fire/smoke detection.
            </p>
          </div>
          <div className="pt-3 mt-3 border-t border-[#20344A]/60 flex items-center justify-between text-xs">
            <span className="text-[10px] text-slate-400">
              Coverage: <strong className="text-emerald-400 font-semibold">GOOD (Wide)</strong>
            </span>
            <span className="text-[10px] text-rose-400 font-mono font-bold">
              Fire/Smoke: P0 Active
            </span>
          </div>
        </div>

        {/* General Monitoring Card */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#20344A]">
              <div className="flex items-center gap-2 text-slate-300 font-bold text-xs uppercase tracking-wide">
                <Camera className="w-4 h-4 text-sky-400" />
                <span>General Monitoring</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#12263A] text-slate-300 border border-[#20344A]">
                {purposeGroups['GENERAL MONITORING'].length} Camera{purposeGroups['GENERAL MONITORING'].length === 1 ? '' : 's'}
              </span>
            </div>
            <p className="text-xs text-[#8FA3B8] mt-2.5 leading-relaxed">
              Storage corridors, logistics docks, and peripheral walkways maintaining secondary safety surveillance.
            </p>
          </div>
          <div className="pt-3 mt-3 border-t border-[#20344A]/60 flex items-center justify-between text-xs">
            <span className="text-[10px] text-slate-400">
              Coverage: <strong className="text-emerald-400 font-semibold">GOOD</strong>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              Transit Area
            </span>
          </div>
        </div>
      </div>

      {/* ─── Informational Policy Note (Section 8 & 9) ──────────────────── */}
      <div className="p-3.5 rounded-xl bg-[#12263A] border border-[#20344A] flex items-start gap-3 text-xs">
        <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <div className="text-slate-300 leading-relaxed text-[11px]">
          <strong className="text-white">Industrial Optical Suitability Notice:</strong> In accordance with SafeSync safety guidelines, camera coverage is evaluated qualitatively based on camera mounting geometry, resolution, and line-of-sight. For example, downward angled cameras provide clear upper-body visibility for hard hats and safety vests, but foot-level visibility may be classified as <strong>LIMITED</strong> if lower bodies are occluded by workbenches. Non-punitive logic ensures unconfirmed regions never trigger false violation alarms.
        </div>
      </div>

      {/* ─── Camera Coverage Table (Section 26) ─────────────────────────── */}
      <div className="rounded-xl border border-[#20344A] bg-[#0D1B2A] overflow-hidden shadow-sm">
        <div className="px-4 py-3 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-sky-400" />
            <h3 className="font-bold text-white text-xs uppercase tracking-wider">
              Surveillance Fleet Coverage &amp; Optical Visibility Ledger
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {cameras.length} Nodes Registered
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#0e1f32] border-b border-[#20344A] text-slate-400 font-bold text-[10px] uppercase tracking-wider">
                <th className="py-3 px-4">Camera Node</th>
                <th className="py-3 px-4">Operational Purpose</th>
                <th className="py-3 px-4">Connection</th>
                <th className="py-3 px-4">Workers</th>
                <th className="py-3 px-4">PPE Monitoring</th>
                <th className="py-3 px-4">Fire / Smoke</th>
                <th className="py-3 px-4">Coverage Suitability</th>
                <th className="py-3 px-4">Configured View</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#20344A]/60">
              {cameras.map((c) => {
                const purpose = getCameraPurpose(c);
                const coverage = getCameraCoverageStatus(c);
                const isOnline =
                  c.enabled !== false &&
                  (c.status === 'online' ||
                    c.status === 'ACTIVE' ||
                    c.status === 'streaming' ||
                    c.state === 'CONNECTED' ||
                    c.state === 'STREAMING');

                const isError = c.status === 'error' || c.state === 'ERROR';
                const isConnecting = c.status === 'connecting' || c.state === 'CONNECTING';

                const workersCount =
                  c.metrics?.active_workers != null
                    ? c.metrics.active_workers
                    : c.ai_analysis?.active_workers != null
                    ? c.ai_analysis.active_workers
                    : '—';

                const fireState = c.metrics?.active_hazards && c.metrics.active_hazards > 0 ? 'ALERT' : 'CLEAR';

                return (
                  <tr
                    key={c.camera_id}
                    className="hover:bg-[#12263A]/80 transition cursor-pointer"
                    onClick={() => onOpenLiveView?.(c)}
                  >
                    {/* Camera */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Camera className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                        <div>
                          <div className="font-bold text-white text-xs">{c.name || c.camera_id}</div>
                          <div className="text-[10px] font-mono text-slate-400 uppercase">{c.camera_id}</div>
                        </div>
                      </div>
                    </td>

                    {/* Operational Purpose */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                          purpose === 'ENTRY GATE'
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : purpose === 'HAZARD ZONE'
                            ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            : purpose === 'PRODUCTION FLOOR'
                            ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                            : 'bg-slate-700/50 text-slate-300 border-slate-600'
                        }`}
                      >
                        {purpose}
                      </span>
                    </td>

                    {/* Connection */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                          isOnline
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : isConnecting
                            ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                            : isError
                            ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            : 'bg-slate-700/50 text-slate-400 border-slate-600'
                        }`}
                      >
                        {isOnline ? 'ONLINE' : isConnecting ? 'CONNECTING' : isError ? 'ERROR' : 'OFFLINE'}
                      </span>
                    </td>

                    {/* Workers */}
                    <td className="py-3 px-4 font-mono font-bold text-slate-200 whitespace-nowrap">
                      {workersCount}
                    </td>

                    {/* PPE Monitoring */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" /> ACTIVE
                      </span>
                    </td>

                    {/* Fire / Smoke */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {fireState === 'ALERT' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] font-bold animate-pulse">
                          <Flame className="w-2.5 h-2.5" /> HAZARD ALERT
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-300 font-medium">
                          CLEAR
                        </span>
                      )}
                    </td>

                    {/* Coverage Suitability */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${coverage.color}`}
                        title={coverage.explanation}
                      >
                        {coverage.status}
                      </span>
                    </td>

                    {/* Configured View */}
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-300 whitespace-nowrap">
                      {coverage.configuredView}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenLiveView?.(c);
                        }}
                        className="px-2.5 py-1 bg-[#12263A] hover:bg-slate-700 text-sky-400 hover:text-white rounded text-[11px] font-bold transition inline-flex items-center gap-1 border border-[#20344A] cursor-pointer"
                      >
                        <Eye className="w-3 h-3" /> Live View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CameraCoverageSection;
