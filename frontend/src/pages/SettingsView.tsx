/**
 * SettingsView.tsx — SafeSync Industrial SOC
 * Phase 9: System Configuration, AI Hyperparameters & Authentic Notification Channels.
 *
 * Enforces:
 * - Sub-tab switching between "Safety Zones & PPE Policy" and "System Parameters & AI Hyperparameters"
 * - Clear distinction of Production V3 (Active, SHA-256: 9b414f...6efe) vs V6 Shadow (Shadow only, SHA-256: c47705...b3cc)
 * - Read-only display of validated detection thresholds (Helmet 0.25, Vest 0.25, Gloves 0.22, Footwear 0.22, Fire 0.20, Smoke 0.20)
 * - 15-frame temporal tolerance (~0.5s) and UNKNOWN neutral stance
 * - 7 Canonical classes (person, helmet, safety_vest, gloves, safety_footwear, fire, smoke)
 * - Goggles extensible non-detection status
 * - Live inspection of external alert notification providers (Webhook, Email, SMS) via /api/alerts/providers/status
 */

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  ShieldCheck,
  Shield,
  Flame,
  Bell,
  ChevronDown,
  ChevronUp,
  Database,
  Eye,
  CheckCircle2,
  Lock,
  Radio,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { SafetyZonesPolicySection } from '../components/SafetyZonesPolicySection';
import { fetchAlertProvidersStatus } from '../services/api';

interface SettingsViewProps {
  complianceConfig?: any;
  hazardConfig?: any;
  cameras?: CameraConfig[];
  onNavigate?: (tab: any, opts?: any) => void;
  initialSubTab?: 'safety_zones' | 'parameters';
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  complianceConfig: _complianceConfig,
  hazardConfig: _hazardConfig,
  cameras = [],
  onNavigate,
  initialSubTab = 'safety_zones',
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'safety_zones' | 'parameters'>(initialSubTab);
  const [providerStatuses, setProviderStatuses] = useState<Record<string, any> | null>(null);

  // Accordion open/close states
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    ai_models: true,
    thresholds: true,
    tracking: true,
    combustion: true,
    notifications: true,
    storage: false,
    policy_preview: false,
  });

  const toggleSection = (id: string) => {
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  useEffect(() => {
    fetchAlertProvidersStatus()
      .then((data) => setProviderStatuses(data))
      .catch(() => setProviderStatuses(null));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#07111F] text-[#E8F0F7] select-none">
      {/* ─── Top Sub-Navigation Bar ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-[#20344A] pb-3">
        <button
          onClick={() => setActiveSubTab('safety_zones')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeSubTab === 'safety_zones'
              ? 'bg-[#2388FF] text-white shadow-sm'
              : 'text-[#8FA3B8] hover:text-white hover:bg-[#12263A]'
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Safety Zones &amp; PPE Policy</span>
        </button>

        <button
          onClick={() => setActiveSubTab('parameters')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeSubTab === 'parameters'
              ? 'bg-[#2388FF] text-white shadow-sm'
              : 'text-[#8FA3B8] hover:text-white hover:bg-[#12263A]'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>System Parameters &amp; AI Hyperparameters</span>
        </button>
      </div>

      {activeSubTab === 'safety_zones' ? (
        <SafetyZonesPolicySection cameras={cameras} onNavigate={onNavigate} />
      ) : (
        <>
          {/* Header for System Parameters */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#20344A]">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
                  <Settings className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2 uppercase">
                    System Configuration &amp; AI Hyperparameters
                  </h2>
                  <p className="text-xs text-[#8FA3B8] mt-0.5">
                    Production model hashes, validated thresholds, ByteTrack heuristics, and notification dispatchers
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold uppercase">
                Runtime Mode: Production Enforced
              </span>
            </div>
          </div>

          {/* Accordion Panels Container */}
          <div className="space-y-4 max-w-5xl">
            {/* ─── Panel 1: Neural Network Architecture & Model Registry ─────── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('ai_models')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      1. Neural Network Checkpoint Registry (Production V3 vs Shadow V6)
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold">
                        ACTIVE V3 ENFORCED
                      </span>
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Authoritative SHA-256 cryptographic hashes, resolution configuration, and deployment status
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.ai_models ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.ai_models && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  {/* Two Model Cards: Production V3 vs Shadow V6 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    {/* Model A: Production V3 */}
                    <div className="p-4 rounded-lg bg-slate-950/70 border border-emerald-500/30 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white flex items-center gap-1.5 text-sm">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" /> YOLOv8n — SafeSync V3
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-black">
                          ACTIVE / DEPLOYED
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Primary unified detector handling 4-point PPE items and combustion hazard classes.
                      </p>
                      <div className="space-y-1.5 pt-1 border-t border-slate-800/80 font-mono text-[11px]">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Checkpoint Name:</span>
                          <span className="text-sky-400">ppe_fire_smoke_v3</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Input Resolution:</span>
                          <span className="text-slate-200">384 &times; 384 Letterboxed</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Inference Device:</span>
                          <span className="text-emerald-400">CPU (PyTorch TorchScript)</span>
                        </div>
                        <div className="space-y-0.5 pt-1">
                          <span className="text-slate-500 text-[10px] uppercase font-bold block">
                            Cryptographic SHA-256 Digest:
                          </span>
                          <div className="text-[10px] text-emerald-300 bg-slate-900/80 p-1.5 rounded border border-slate-800 break-all select-all">
                            9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Model B: Shadow V6 */}
                    <div className="p-4 rounded-lg bg-slate-950/70 border border-amber-500/30 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white flex items-center gap-1.5 text-sm">
                          <Lock className="w-4 h-4 text-amber-400" /> YOLOv8 — SafeSync V6 (Shadow)
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-black">
                          SHADOW ONLY — NOT DEPLOYED
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Offline research benchmark model. Evaluated for research mAP comparisons only.
                      </p>
                      <div className="space-y-1.5 pt-1 border-t border-slate-800/80 font-mono text-[11px]">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Execution Status:</span>
                          <span className="text-amber-400">Locked / Offline Benchmarking</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">UI Activation:</span>
                          <span className="text-slate-400">Disabled (No Switch Permitted)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Pipeline Route:</span>
                          <span className="text-slate-400">Bypassed in Runtime</span>
                        </div>
                        <div className="space-y-0.5 pt-1">
                          <span className="text-slate-500 text-[10px] uppercase font-bold block">
                            Cryptographic SHA-256 Digest:
                          </span>
                          <div className="text-[10px] text-amber-300 bg-slate-900/80 p-1.5 rounded border border-slate-800 break-all select-all">
                            c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ─── Panel 2: Validated Detection Confidence Thresholds ─────────── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('thresholds')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      2. Validated Detection Thresholds &amp; Canonical Taxonomy
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/15 border border-sky-500/30 text-sky-400 font-bold">
                        DISPLAY ONLY • READ-ONLY
                      </span>
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Confidence thresholds calibrated against false alarms, and 7 canonical classes taxonomy
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.thresholds ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.thresholds && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  {/* Thresholds Table */}
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 font-semibold uppercase text-[10px]">
                        Validated Production Confidence Thresholds (Display Only)
                      </span>
                      <span className="text-[10px] text-amber-400/90 font-mono flex items-center gap-1">
                        <Lock className="w-3 h-3" /> Runtime Calibration Locked
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-center text-xs">
                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Safety Helmet</span>
                        <span className="font-mono font-bold text-emerald-400 text-base">0.25</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Cranial Zone</span>
                      </div>

                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Safety Vest</span>
                        <span className="font-mono font-bold text-emerald-400 text-base">0.25</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Torso Zone</span>
                      </div>

                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Protective Gloves</span>
                        <span className="font-mono font-bold text-emerald-400 text-base">0.22</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Extremities</span>
                      </div>

                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Safety Footwear</span>
                        <span className="font-mono font-bold text-emerald-400 text-base">0.22</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Base Zone</span>
                      </div>

                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Fire / Flame</span>
                        <span className="font-mono font-bold text-rose-400 text-base">0.20</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Thermal Core</span>
                      </div>

                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-semibold">Smoke Plume</span>
                        <span className="font-mono font-bold text-amber-400 text-base">0.20</span>
                        <span className="text-[9px] text-slate-500 block mt-0.5">Area &ge; 0.05</span>
                      </div>
                    </div>
                  </div>

                  {/* Canonical 7 Classes */}
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-slate-400 font-semibold uppercase text-[10px] block">
                      Canonical Model Classes Taxonomy (7 Canonical Outputs)
                    </span>
                    <div className="flex flex-wrap gap-2 font-mono text-xs">
                      {[
                        { id: 0, name: 'person', role: 'Worker Body Root' },
                        { id: 1, name: 'helmet', role: 'Head Protection' },
                        { id: 2, name: 'safety_vest', role: 'High-Vis Torso' },
                        { id: 3, name: 'gloves', role: 'Hand Protection' },
                        { id: 4, name: 'safety_footwear', role: 'Foot / Boot' },
                        { id: 5, name: 'fire', role: 'Open Combustion' },
                        { id: 6, name: 'smoke', role: 'Atmospheric Plume' },
                      ].map((cls) => (
                        <div
                          key={cls.id}
                          className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 flex items-center gap-1.5"
                        >
                          <span className="text-sky-400 font-bold">{cls.id}:</span>
                          <span className="text-white font-bold">{cls.name}</span>
                          <span className="text-[10px] text-slate-500">({cls.role})</span>
                        </div>
                      ))}
                    </div>
                    <p className="text-[11px] text-slate-400 pt-1 leading-relaxed">
                      SafeSync does <span className="text-amber-300 font-bold">NOT</span> utilize pseudo-classes
                      such as <code className="text-slate-300">no_helmet</code> or <code className="text-slate-300">no_vest</code>.
                      Gear absence is resolved through Hungarian bipartite anatomical zone association combined with 15-frame temporal state machines.
                    </p>
                  </div>

                  {/* Eye Protection Goggles Status */}
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-3">
                    <div className="p-1.5 rounded bg-slate-900 text-slate-400 shrink-0 mt-0.5">
                      <Eye className="w-4 h-4" />
                    </div>
                    <div className="text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">Eye Protection (Goggles) Specification:</span>
                        <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-800 text-slate-400 font-bold">
                          EXTENSIBLE — NOT MONITORED IN V3
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                        Accurate ocular PPE detection requires dedicated sub-inch facial crops or high-resolution pan-tilt-zoom cameras.
                        To prevent false alarms in wide-area facility monitoring, ocular detection is intentionally excluded from the V3 model.
                        Architecture supports future expansion without altering worker tracking.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ─── Panel 3: Worker Tracking & Temporal Validation ─────────────── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('tracking')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400">
                    <Radio className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      3. Worker Tracking &amp; Temporal Validation Heuristics (ByteTrack)
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Kalman filter motion estimation, 15-frame absence tolerance, and Hungarian association
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.tracking ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.tracking && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Tracker Algorithm</span>
                      <div className="font-mono text-slate-200 font-bold">ByteTrack Multi-Object Tracking</div>
                      <p className="text-[10px] text-slate-400">Maintains persistent worker identities across occlusions</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Temporal Absence Tolerance</span>
                      <div className="font-mono text-emerald-400 font-bold">15 Consecutive Frames (~0.5s @ 30 FPS)</div>
                      <p className="text-[10px] text-slate-400">Gear absence must persist across 15 frames before violation</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Spatial IoU Threshold</span>
                      <div className="font-mono text-slate-200 font-bold">0.35 IoU Overlap</div>
                      <p className="text-[10px] text-slate-400">Associates PPE bounding boxes to corresponding worker body</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Occlusion / Unknown Stance</span>
                      <div className="font-mono text-amber-400 font-bold">Neutral Evaluation (UNKNOWN != VIOLATION)</div>
                      <p className="text-[10px] text-slate-400">Prevents false penalties when body parts are camera-obscured</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ─── Panel 4: Combustion Hazard Debouncing & Fire/Smoke Policies ── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('combustion')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
                    <Flame className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      4. Combustion Hazard Validation (Fire &amp; Smoke Debounce)
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Decoupled thermal pipeline, 3-frame confirmation, and 10s continuous clearance cooldown
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.combustion ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.combustion && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Fire Detection Threshold</span>
                      <div className="font-mono text-rose-400 font-bold">&ge; 0.20 Confidence Score</div>
                      <p className="text-[10px] text-slate-400">Calibrated to capture early flicker while filtering vests</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Smoke Minimum Bounding Area</span>
                      <div className="font-mono text-amber-400 font-bold">&ge; 0.05 Normalized Area</div>
                      <p className="text-[10px] text-slate-400">Filters optical dust particles and lens smudges</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Temporal Debounce Confirmation</span>
                      <div className="font-mono text-sky-400 font-bold">3 Consecutive Frames</div>
                      <p className="text-[10px] text-slate-400">Hazard must persist across 3 frames before triggering alarm</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Spatial Clearance Cooldown</span>
                      <div className="font-mono text-emerald-400 font-bold">10 Seconds Continuous Clean</div>
                      <p className="text-[10px] text-slate-400">Zone must remain free of combustion before status reset</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ─── Panel 5: External Notification Dispatchers Status ─────────── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('notifications')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                    <Bell className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      5. External Notification Channels (Authentic Provider Registry)
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Operational status for Webhook, Email, and SMS dispatchers via /api/alerts/providers/status
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.notifications ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.notifications && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    {/* Webhook Channel */}
                    <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">HTTP Webhook Dispatcher</span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                          {providerStatuses?.webhook?.status || 'NOT CONFIGURED'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        Endpoint: {providerStatuses?.webhook?.url || 'None (Disabled in environment)'}
                      </p>
                      <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                        Payload: HMAC-SHA256 Signed JSON
                      </div>
                    </div>

                    {/* Email Channel */}
                    <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">SMTP Email Alerts</span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                          {providerStatuses?.email?.status || 'NOT CONFIGURED'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        Server: {providerStatuses?.email?.smtp_host || 'None (Disabled in environment)'}
                      </p>
                      <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                        Recipients: Safety Officer Group
                      </div>
                    </div>

                    {/* SMS Channel */}
                    <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">SMS Emergency Gateway</span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                          {providerStatuses?.sms?.status || 'NOT CONFIGURED'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        Provider: {providerStatuses?.sms?.provider || 'Twilio / Telco (Disabled)'}
                      </p>
                      <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                        Triage: Critical / Fire Evac Only
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 italic">
                    Note: Unconfigured channels authentically display &quot;NOT CONFIGURED&quot;. SafeSync does not fabricate artificial &quot;Active&quot; indicators for unlinked third-party delivery services.
                  </p>
                </div>
              )}
            </div>

            {/* ─── Panel 6: Persistence Storage & Audit Logging ──────────────── */}
            <div className="glass-card overflow-hidden transition-all duration-200">
              <button
                onClick={() => toggleSection('storage')}
                className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      6. Persistence Storage &amp; Audit Logging (SQLite WAL)
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      SQLite engine flags, connection pooling, and disk retention policies
                    </p>
                  </div>
                </div>
                <div className="text-slate-400 hover:text-white">
                  {openSections.storage ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {openSections.storage && (
                <div className="p-5 border-t border-slate-800/80 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">SQLite Journaling</span>
                      <div className="font-mono text-emerald-400 font-bold">PRAGMA journal_mode=WAL</div>
                      <p className="text-[10px] text-slate-400">Concurrent readers and writer isolation</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Synchronous Setting</span>
                      <div className="font-mono text-slate-200 font-bold">PRAGMA synchronous=NORMAL</div>
                      <p className="text-[10px] text-slate-400">High transactional write rate with safety guarantees</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Snapshot Retention Window</span>
                      <div className="font-mono text-slate-200 font-bold">30 Days Historical Archive</div>
                      <p className="text-[10px] text-slate-400">Automatic pruning of cleared non-critical logs</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                      <span className="text-slate-500 font-semibold uppercase text-[10px]">Evidence Integrity Digest</span>
                      <div className="font-mono text-sky-400 font-bold">SHA-256 Frame Hashing</div>
                      <p className="text-[10px] text-slate-400">Infraction frames hashed for tamper-evident compliance audit</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SettingsView;
