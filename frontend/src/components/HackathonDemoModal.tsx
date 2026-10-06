/**
 * HackathonDemoModal.tsx — SafeSync Industrial SOC
 * Phase 10: Master Hackathon Demonstration, System Architecture & Evaluator Guide.
 *
 * Implements:
 * - 60-Second & 3-Minute structured presentation paths with click-to-navigate action
 * - Interactive Demo Scenarios (1 through 5) selector
 * - Complete End-to-End System Architecture and decoupled pipeline flow
 * - Edge CPU Deployment specification (Intel Core i5-13420H reference)
 * - Authoritative Last Validated Readiness Evidence Grid
 * - Honest Known Deployment Limitations & "Do Not Claim" ethical disclosures
 */

import React, { useState } from 'react';
import {
  X,
  Award,
  Sparkles,
  Layers,
  Cpu,
  Tv,
  Users,
  Flame,
  AlertTriangle,
  FileCheck,
  ArrowRight,
  Camera,
  BarChart3,
  Activity,
} from 'lucide-react';
import { DemoScenarioId } from './DemoTopBanner';

interface HackathonDemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateTab: (tab: any, subTab?: any) => void;
  onSelectDemoScenario: (id: DemoScenarioId) => void;
  activeScenario?: DemoScenarioId;
  isDemoMode?: boolean;
  onToggleDemoMode?: (enable: boolean) => void;
}

type ModalTab = 'walkthrough' | 'scenarios' | 'architecture' | 'deployment';

export const HackathonDemoModal: React.FC<HackathonDemoModalProps> = ({
  isOpen,
  onClose,
  onNavigateTab,
  onSelectDemoScenario,
  activeScenario = 'safe_worker',
  isDemoMode = false,
  onToggleDemoMode,
}) => {
  const [activeTab, setActiveTab] = useState<ModalTab>('walkthrough');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-in fade-in select-none">
      <div className="relative w-full max-w-5xl max-h-[92vh] flex flex-col rounded-xl bg-[#090f1d] border border-slate-700/80 shadow-2xl text-slate-100 overflow-hidden">
        {/* ─── Top Modal Header ─────────────────────────────────────────────── */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-[#0d1527] flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
                <Award className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-black text-white uppercase tracking-tight">
                SafeSync — BPUT Hackathon 2026 Executive Guide
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold">
                V3 PRODUCTION ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Smart Vision • Safe Workers • Faster Response — AI-Assisted Industrial Safety Monitoring Prototype
            </p>
          </div>

          <div className="flex items-center gap-2">
            {onToggleDemoMode && (
              <button
                onClick={() => onToggleDemoMode(!isDemoMode)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer border ${
                  isDemoMode
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isDemoMode ? 'Demo Mode Active' : 'Enable Demo Mode'}</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ─── Sub-Tab Navigation Bar ───────────────────────────────────────── */}
        <div className="flex items-center gap-1 px-4 sm:px-5 pt-3 border-b border-slate-800 bg-[#0a1122]">
          {[
            { id: 'walkthrough' as const, label: '60s & 3m Demo Flows', icon: ArrowRight },
            { id: 'scenarios' as const, label: 'Demo Scenario Selector', icon: Sparkles },
            { id: 'architecture' as const, label: 'System Architecture', icon: Layers },
            { id: 'deployment' as const, label: 'Validation & Disclosures', icon: Cpu },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 text-xs font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
                  isActive
                    ? 'border-sky-500 text-sky-400 bg-sky-500/10 rounded-t-md'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ─── Modal Content Area ──────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {/* TAB 1: WALKTHROUGH ─────────────────────────────────────────────── */}
          {activeTab === 'walkthrough' && (
            <div className="space-y-6">
              {/* 60-Second Sequence */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <ArrowRight className="w-4 h-4 text-sky-400" />
                    60-Second Rapid Judge Demonstration Walkthrough
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    Recommended Fast Track
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
                  {[
                    {
                      step: 'Step 1',
                      time: '0:00–0:10',
                      title: 'Overview Command Center',
                      desc: 'Introduce SafeSync as a centralized, multi-stream industrial safety command center.',
                      tab: 'overview',
                      icon: LayoutIcon,
                    },
                    {
                      step: 'Step 2',
                      time: '0:10–0:20',
                      title: 'Live Monitor & Bounding HUD',
                      desc: 'Demonstrate real-time worker tracking, 4-point PPE association, and anatomical overlays.',
                      tab: 'live-monitor',
                      icon: Tv,
                    },
                    {
                      step: 'Step 3',
                      time: '0:20–0:30',
                      title: 'Tri-State Worker Explainability',
                      desc: 'Highlight GREEN Safe vs YELLOW Unknown. Emphasize why UNKNOWN != VIOLATION.',
                      tab: 'workers',
                      icon: Users,
                    },
                    {
                      step: 'Step 4',
                      time: '0:30–0:38',
                      title: 'Camera Fleet & Entry Gate Policy',
                      desc: 'Show Entry Gate access evaluation (Allow, Verification Required, Deny).',
                      tab: 'cameras',
                      subTab: 'entry_gate',
                      icon: Camera,
                    },
                    {
                      step: 'Step 5',
                      time: '0:38–0:44',
                      title: 'Decoupled Fire & Smoke Monitor',
                      desc: 'Show independent combustion pipeline (P0 Emergency) decoupled from PPE.',
                      tab: 'hazards',
                      icon: Flame,
                    },
                    {
                      step: 'Step 6',
                      time: '0:44–0:50',
                      title: 'Smart Alerts & Triage Hierarchy',
                      desc: 'Demonstrate P0/P1/P2/P3 priority queue with tamper-evident SHA-256 evidence.',
                      tab: 'alerts',
                      icon: AlertTriangle,
                    },
                    {
                      step: 'Step 7',
                      time: '0:50–0:55',
                      title: 'Authentic Analytics Trends',
                      desc: 'Show real historical buckets with zero synthetic curves or fake diurnal math.',
                      tab: 'analytics',
                      icon: BarChart3,
                    },
                    {
                      step: 'Step 8',
                      time: '0:55–1:00',
                      title: 'Edge Health & V3 Cryptography',
                      desc: 'Display ~32.5 ms AI forward-pass latency on CPU and V3 model hash (9b414f...6efe).',
                      tab: 'health',
                      icon: Activity,
                    },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition flex items-start justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 font-bold">
                            {item.step} • {item.time}
                          </span>
                          <span className="font-bold text-white">{item.title}</span>
                        </div>
                        <p className="text-[11px] text-slate-400">{item.desc}</p>
                      </div>

                      <button
                        onClick={() => {
                          onNavigateTab(item.tab, (item as any).subTab);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-sky-600 text-slate-200 hover:text-white transition font-mono text-[10px] font-bold shrink-0 cursor-pointer flex items-center gap-1"
                      >
                        <span>Jump</span>
                        <ArrowRight className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3-Minute Comprehensive Flow */}
              <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
                <span className="font-bold text-sky-400 uppercase tracking-wider text-[11px] block">
                  3-Minute Deep Dive Hackathon Presentation Timeline:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-1 text-[11px]">
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 font-mono block">00:00–00:20</span>
                    <span className="font-bold text-white">Problem &amp; Overview</span>
                    <p className="text-slate-400 text-[10px] mt-0.5">Industrial accidents &amp; Command Center integration</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 font-mono block">00:20–01:00</span>
                    <span className="font-bold text-white">Live Monitor &amp; PPE HUD</span>
                    <p className="text-slate-400 text-[10px] mt-0.5">Real-time worker tracking &amp; Hungarian association</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 font-mono block">01:00–01:45</span>
                    <span className="font-bold text-white">UNKNOWN Protection</span>
                    <p className="text-slate-400 text-[10px] mt-0.5">Occlusion mitigation; zero false alarms on UNKNOWN</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 font-mono block">01:45–02:20</span>
                    <span className="font-bold text-white">Entry Gate &amp; Fire/Smoke</span>
                    <p className="text-slate-400 text-[10px] mt-0.5">Access policy &amp; decoupled P0 combustion halt</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SCENARIOS ───────────────────────────────────────────────── */}
          {activeTab === 'scenarios' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    Interactive Validation Scenario Triggers
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Click any scenario to safely simulate the specific worker or hazard state across all screens.
                  </p>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  Client Safe • Non-Destructive
                </span>
              </div>

              <div className="space-y-3">
                {[
                  {
                    id: 'safe_worker' as const,
                    title: 'Scenario 1: Fully Equipped Worker (Compliant)',
                    statusBadge: 'SAFE (GREEN)',
                    badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
                    desc: 'Worker detected with Helmet, Vest, Gloves, and Safety Footwear observed on anatomical zones.',
                    expected: 'Overall state is GREEN / SAFE. Zero alerts created. Entry Gate allows entry.',
                    reason: 'All mandatory zone PPE is observed and verified on worker anatomical zones.',
                  },
                  {
                    id: 'unknown_worker' as const,
                    title: 'Scenario 2: Unknown State / Partial Visibility (Neutral)',
                    statusBadge: 'UNKNOWN (YELLOW)',
                    badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
                    desc: 'Hands or footwear are occluded by workbench or camera angle. Visibility insufficient to confirm presence or absence.',
                    expected: 'State held in neutral UNKNOWN evaluation. Zero violations levied. Zero alarms triggered.',
                    reason: 'Required PPE cannot be conclusively evaluated due to optical occlusion. Preserves neutral stance.',
                  },
                  {
                    id: 'confirmed_violation' as const,
                    title: 'Scenario 3: Confirmed PPE Violation (Temporal Debounced)',
                    statusBadge: 'VIOLATION (RED)',
                    badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
                    desc: 'Cranial zone is clearly visible without hard hat across 15 consecutive frames (~0.5s tolerance).',
                    expected: 'State escalates to RED VIOLATION. P2 Alert generated. Entry Gate denies entry.',
                    reason: 'Hard hat absence confirmed after the full 15-frame temporal debouncing period.',
                  },
                  {
                    id: 'multi_worker' as const,
                    title: 'Scenario 4: Multi-Worker Concurrent Independence',
                    statusBadge: 'MULTI-TRACK (3 WORKERS)',
                    badgeColor: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
                    desc: 'Worker A (Safe), Worker B (Unknown), Worker C (Violation) monitored simultaneously in the same scene.',
                    expected: 'Each worker track maintains distinct ByteTrack identity. Zero cross-worker gear contamination.',
                    reason: 'Hungarian bipartite association ensures spatial boxes match only corresponding worker bodies.',
                  },
                  {
                    id: 'fire_smoke' as const,
                    title: 'Scenario 5: Decoupled Combustion Emergency (Fire & Smoke)',
                    statusBadge: 'P0 EMERGENCY (FIRE/SMOKE)',
                    badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse',
                    desc: 'Open combustion flame and smoke plume detected in electrical hazard area.',
                    expected: 'Bypasses worker tracking. Triggers immediate P0 incident, audible alarm, and evacuation halt.',
                    reason: 'Combustion detection event received from decoupled thermal pipeline.',
                  },
                ].map((sc) => {
                  const isCurrent = activeScenario === sc.id;
                  return (
                    <div
                      key={sc.id}
                      className={`p-4 rounded-lg border transition ${
                        isCurrent
                          ? 'bg-slate-900/90 border-sky-500 ring-1 ring-sky-500/30'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-black uppercase border ${sc.badgeColor}`}>
                            {sc.statusBadge}
                          </span>
                          <h4 className="font-bold text-white text-xs">{sc.title}</h4>
                        </div>

                        <button
                          onClick={() => {
                            if (onToggleDemoMode) onToggleDemoMode(true);
                            onSelectDemoScenario(sc.id);
                            onNavigateTab('live-monitor');
                            onClose();
                          }}
                          className={`px-3 py-1 rounded text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                            isCurrent
                              ? 'bg-sky-600 text-white'
                              : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                          }`}
                        >
                          <Sparkles className="w-3 h-3" />
                          <span>{isCurrent ? 'Active Scenario (Loaded)' : 'Load Scenario into HUD'}</span>
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2.5">
                        <div>
                          <span className="text-slate-500 text-[10px] uppercase font-bold block">Scenario Input:</span>
                          <p className="text-slate-300 text-[11px] mt-0.5">{sc.desc}</p>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[10px] uppercase font-bold block">Expected Evaluator Result:</span>
                          <p className="text-slate-300 text-[11px] mt-0.5">{sc.expected}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: ARCHITECTURE ────────────────────────────────────────────── */}
          {activeTab === 'architecture' && (
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Layers className="w-4 h-4 text-sky-400" />
                    End-to-End System Architecture &amp; Data Pipeline
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Strict separation of worker PPE tracking from decoupled combustion hazard triage.
                  </p>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Deterministic Pipeline
                </span>
              </div>

              {/* Pipeline Flow Diagram */}
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] space-y-3 overflow-x-auto">
                <div className="text-slate-400 text-center font-bold">
                  [ CAMERA / CCTV VIDEO STREAMS (USB, RTSP, Video File) ]
                </div>
                <div className="text-center text-sky-500">↓ (Threaded cv2.VideoCapture &amp; Non-blocking Queue)</div>

                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-center text-white font-bold">
                  YOLOv8n V3 INFERENCE CORE (384 &times; 384 Letterboxed • Single Forward Pass ~32.5 ms on CPU)
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {/* Left Branch: Worker & PPE */}
                  <div className="p-3 rounded bg-slate-900/60 border border-slate-800 space-y-1.5">
                    <div className="text-emerald-400 font-bold border-b border-slate-800 pb-1">
                      BRANCH A: Worker &amp; PPE Tracking
                    </div>
                    <div className="text-slate-300">1. Person Detections &rarr; ByteTrack Kalman Filter</div>
                    <div className="text-slate-300">2. PPE Detections &rarr; Hungarian Bipartite Association</div>
                    <div className="text-slate-300">3. Anatomical Overlap (Helmet, Vest, Gloves, Boots)</div>
                    <div className="text-amber-400">4. Occlusion Handling &rarr; UNKNOWN (Neutral, No Penalty)</div>
                    <div className="text-rose-400">5. 15-Frame Temporal Confirmation &rarr; Confirmed Absence</div>
                    <div className="text-sky-300">6. Zone Policy Evaluation &rarr; P2 / P1 Smart Alerts</div>
                  </div>

                  {/* Right Branch: Decoupled Thermal */}
                  <div className="p-3 rounded bg-slate-900/60 border border-rose-900/40 space-y-1.5">
                    <div className="text-rose-400 font-bold border-b border-rose-900/30 pb-1">
                      BRANCH B: Decoupled Combustion Pipeline
                    </div>
                    <div className="text-slate-300">1. Fire &amp; Smoke Detection (Threshold &ge; 0.20)</div>
                    <div className="text-slate-300">2. Minimum Area Check (Smoke Area &ge; 0.05 Filters Dust)</div>
                    <div className="text-slate-300">3. 3-Frame Consecutive Debounce Confirmation</div>
                    <div className="text-rose-400 font-bold">4. Bypasses Worker Tracking &rarr; P0 Emergency Alert</div>
                    <div className="text-slate-300">5. Autonomous Siren Dispatch &amp; Facility Evacuation</div>
                    <div className="text-emerald-400">6. 10s Continuous Spatial Clearance Cooldown</div>
                  </div>
                </div>

                <div className="text-center text-sky-500 pt-1">↓ (Asynchronous Event Dispatch)</div>
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-center text-slate-200">
                  WebSocket Pub/Sub (/api/ws/events) &rarr; SafeSync Industrial SOC Operations Center
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DEPLOYMENT & DISCLOSURES ─────────────────────────────────── */}
          {activeTab === 'deployment' && (
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-sky-400" />
                    Edge CPU Deployment Specs &amp; Ethical Disclosures
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Authoritative benchmark results, known deployment limitations, and claims boundaries.
                  </p>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Verified Readiness
                </span>
              </div>

              {/* Host Platform Reference */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Validated Host Hardware</span>
                  <div className="font-bold text-white">Intel Core i5-13420H</div>
                  <p className="text-[10px] text-slate-400">8 Physical / 12 Logical Cores • 15.59 GB RAM</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Inference Target</span>
                  <div className="font-bold text-emerald-400">CPU-Only PyTorch TorchScript</div>
                  <p className="text-[10px] text-slate-400">Zero GPU requirement for edge execution</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Future Acceleration</span>
                  <div className="font-bold text-amber-400">Jetson / TensorRT / GPU</div>
                  <p className="text-[10px] text-slate-400">Labeled strictly as future roadmap work</p>
                </div>
              </div>

              {/* 30-Minute Run Readiness Grid */}
              <div className="p-3.5 rounded-lg bg-slate-950 border border-amber-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white flex items-center gap-1.5">
                    <FileCheck className="w-4 h-4 text-amber-400" />
                    Last Validated Readiness Evidence (30-Minute Continuous Run)
                  </span>
                  <span className="text-[10px] font-mono text-amber-300 bg-amber-500/20 px-2 py-0.2 rounded border border-amber-500/30">
                    Static Benchmark Proof
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] pt-1">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Regression Suite</span>
                    <span className="text-emerald-400 font-bold">276 / 276 (100%)</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Thermal Suite</span>
                    <span className="text-emerald-400 font-bold">23 / 23 (100%)</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Frames Evaluated</span>
                    <span className="text-white font-bold">6,843 Frames</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">PPE Association</span>
                    <span className="text-emerald-400 font-bold">738 / 738 (100%)</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Cross-Contamination</span>
                    <span className="text-emerald-400 font-bold">0 Instances</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">False Violations</span>
                    <span className="text-emerald-400 font-bold">0 False Penalties</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">Heap Memory Drift</span>
                    <span className="text-emerald-400 font-bold">0 MB Drift</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block text-[9px]">System Crashes</span>
                    <span className="text-emerald-400 font-bold">0 Crashes</span>
                  </div>
                </div>
              </div>

              {/* Known Deployment Limitations */}
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                <span className="font-bold text-amber-400 uppercase tracking-wider text-[11px] block">
                  Known Deployment Limitations (Engineering Transparency):
                </span>
                <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
                  <li>Gloves can be challenging to detect in wide-angle views when hand bounding boxes are sub-pixel.</li>
                  <li>Distant safety footwear may lack optical resolution, appropriately triggering the UNKNOWN state.</li>
                  <li>Waist-up or desk-mounted camera angles naturally occlude boots; SafeSync marks boots UNKNOWN without penalty.</li>
                  <li>Eye protection (goggles) is unmonitored by the V3 production detector due to wide-area camera constraints.</li>
                  <li>Physical gate PLC/SCADA control is not implemented; Entry Gate provides policy advisory decisions only.</li>
                  <li>Biometric facial identification is not linked to production safety evaluation.</li>
                </ul>
              </div>

              {/* DO NOT CLAIM List */}
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-1 text-[11px]">
                <span className="font-bold uppercase tracking-wider block">Do Not Claim Boundaries:</span>
                <p>
                  SafeSync does <strong>not</strong> claim 100% real-world optical detection accuracy, automatic physical gate actuation,
                  biometric identity matching, or GPU hardware dependency. SafeSync is presented honestly as an
                  <strong> AI-assisted industrial safety monitoring prototype</strong>.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* ─── Bottom Footer ────────────────────────────────────────────────── */}
        <div className="p-3 sm:p-4 border-t border-slate-800 bg-[#0d1527] flex items-center justify-between text-xs">
          <div className="text-[11px] text-slate-400">
            Current Scenario: <span className="text-sky-400 font-bold uppercase">{activeScenario.replace(/_/g, ' ')}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-bold cursor-pointer"
            >
              Close Guide
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper icon
const LayoutIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className || 'w-4 h-4'} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
  </svg>
);

export default HackathonDemoModal;
