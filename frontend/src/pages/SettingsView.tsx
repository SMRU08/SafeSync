/**
 * SettingsView.tsx — SafeSync Industrial SOC
 * Clean industrial configuration panel with Collapsible Accordion Panels,
 * glassmorphic surfaces, and detailed parameter tuning inspection.
 */

import React, { useState } from 'react';
import {
  Settings,
  Cpu,
  ShieldCheck,
  Flame,
  Bell,
  ChevronDown,
  ChevronUp,
  Database,
} from 'lucide-react';

interface SettingsViewProps {
  complianceConfig?: any;
  hazardConfig?: any;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  complianceConfig: _complianceConfig,
  hazardConfig: _hazardConfig,
}) => {
  // Accordion open/close state: all open by default or toggleable
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    ai_engine: true,
    tracking: true,
    hazard_debouncing: true,
    alerts: false,
    storage: false,
  });

  const toggleSection = (id: string) => {
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6 bg-[#070b14] text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
                System Configuration &amp; AI Hyperparameters
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect active neural network checkpoints, ByteTrack association heuristics, and deterministic risk parameters
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Runtime Mode: Production Enforced
          </span>
        </div>
      </div>

      {/* Accordion Panels Container */}
      <div className="space-y-4 max-w-5xl">
        {/* Panel 1: AI Detection Engine */}
        <div className="glass-card overflow-hidden transition-all duration-200">
          <button
            onClick={() => toggleSection('ai_engine')}
            className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  1. Edge AI Inference Engine (YOLOv8n-PPE &amp; Hazards)
                </h3>
                <p className="text-[11px] text-slate-400">
                  Neural network weights, model input dimensions, and canonical class mappings
                </p>
              </div>
            </div>
            <div className="text-slate-400 hover:text-white">
              {openSections.ai_engine ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </button>

          {openSections.ai_engine && (
            <div className="p-5 border-t border-slate-800/80 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Architecture Checkpoint</span>
                  <div className="font-mono text-slate-200 font-bold">Ultralytics YOLOv8n (Multi-Task)</div>
                  <p className="text-[10px] text-slate-400">Weights: ppe_fire_smoke_v2/weights/best.pt</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Input Resolution &amp; Device</span>
                  <div className="font-mono text-slate-200 font-bold">640 &times; 640 Letterboxed</div>
                  <p className="text-[10px] text-slate-400">Execution: CUDA with CPU Autotune Fallback</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Canonical Model Classes</span>
                  <div className="font-mono text-sky-400 font-semibold text-[11px]">
                    person, helmet, vest, gloves, shoes, fire, smoke
                  </div>
                  <p className="text-[10px] text-slate-400">7 classes mapped via unified semantic taxonomy</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Latency SLA Target</span>
                  <div className="font-mono text-emerald-400 font-bold text-sm">30 &ndash; 60 ms / frame</div>
                  <p className="text-[10px] text-slate-400">Guarantees 15-30 FPS throughput without frame backpressure</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Panel 2: Worker Tracking & PPE Rules */}
        <div className="glass-card overflow-hidden transition-all duration-200">
          <button
            onClick={() => toggleSection('tracking')}
            className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  2. Worker Tracking &amp; PPE Spatial Association (ByteTrack)
                </h3>
                <p className="text-[11px] text-slate-400">
                  Kalman filter velocity estimation, spatial IoU matching, and track persistence
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
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Tracker Algorithm</span>
                  <div className="font-mono text-slate-200 font-bold">ByteTrack Multi-Object Tracking</div>
                  <p className="text-[10px] text-slate-400">Maintains persistent worker identities across occlusions</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Spatial IoU Threshold</span>
                  <div className="font-mono text-slate-200 font-bold">0.35 IoU Overlap</div>
                  <p className="text-[10px] text-slate-400">Associates PPE bounding boxes to corresponding worker body</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Occlusion / Unknown Rule</span>
                  <div className="font-mono text-amber-400 font-bold">Neutral Evaluation</div>
                  <p className="text-[10px] text-slate-400">Prevents false penalties when body parts are camera-obscured</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Track Memory Grace Period</span>
                  <div className="font-mono text-slate-200 font-bold">30 Lost Frames (1.5 seconds)</div>
                  <p className="text-[10px] text-slate-400">Preserves track context during brief optical pass-through</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Panel 3: Hazard Detection Policies (Fire & Smoke) */}
        <div className="glass-card overflow-hidden transition-all duration-200">
          <button
            onClick={() => toggleSection('hazard_debouncing')}
            className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  3. Combustion Hazard Validation (Fire &amp; Smoke Debounce)
                </h3>
                <p className="text-[11px] text-slate-400">
                  Confidence filtering, minimum bounding area, and multi-frame temporal confirmation
                </p>
              </div>
            </div>
            <div className="text-slate-400 hover:text-white">
              {openSections.hazard_debouncing ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </button>

          {openSections.hazard_debouncing && (
            <div className="p-5 border-t border-slate-800/80 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Fire Detection Threshold</span>
                  <div className="font-mono text-slate-200 font-bold">&ge; 0.45 Confidence Score</div>
                  <p className="text-[10px] text-slate-400">Calibrated against high-lumen reflections and safety vests</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Smoke Minimum Bounding Area</span>
                  <div className="font-mono text-slate-200 font-bold">0.05 Normalized Area</div>
                  <p className="text-[10px] text-slate-400">Filters optical dust specks and camera lens smudge</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Temporal Debounce Confirmation</span>
                  <div className="font-mono text-sky-400 font-bold">3 Consecutive Frames</div>
                  <p className="text-[10px] text-slate-400">Hazard must persist across 3 frames before triggering alarm</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Spatial Clearance Cooldown</span>
                  <div className="font-mono text-emerald-400 font-bold">10 Seconds Continuous Clean</div>
                  <p className="text-[10px] text-slate-400">Zone must remain free of hazard before resetting status</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Panel 4: Alert Deduplication & Escalation */}
        <div className="glass-card overflow-hidden transition-all duration-200">
          <button
            onClick={() => toggleSection('alerts')}
            className="w-full p-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900/90 transition text-left cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  4. Alert Deduplication &amp; Escalation Policies
                </h3>
                <p className="text-[11px] text-slate-400">
                  Deduplication windows, incident formation thresholds, and operator siren controls
                </p>
              </div>
            </div>
            <div className="text-slate-400 hover:text-white">
              {openSections.alerts ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </button>

          {openSections.alerts && (
            <div className="p-5 border-t border-slate-800/80 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Alert Deduplication Cooldown</span>
                  <div className="font-mono text-slate-200 font-bold">30 Seconds / Target Track</div>
                  <p className="text-[10px] text-slate-400">Prevents alarm fatigue from recurring momentary alerts</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Incident Auto-Escalation</span>
                  <div className="font-mono text-rose-400 font-bold">3 Repeated Infractions</div>
                  <p className="text-[10px] text-slate-400">Automatically creates persistent Incident investigation dossier</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Real-Time Broadcast Protocol</span>
                  <div className="font-mono text-emerald-400 font-bold">WebSocket Event-Driven Push</div>
                  <p className="text-[10px] text-slate-400">Low-latency event streaming to SOC workstations</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Cryptographic Evidence</span>
                  <div className="font-mono text-slate-200 font-bold">SHA-256 Digesting</div>
                  <p className="text-[10px] text-slate-400">All captured infraction frames are hashed for compliance audit</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Panel 5: Database & Persistence Layer */}
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
                  5. Persistence Storage &amp; Audit Logging
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
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">SQLite Journaling</span>
                  <div className="font-mono text-emerald-400 font-bold">PRAGMA journal_mode=WAL</div>
                  <p className="text-[10px] text-slate-400">Concurrent readers and writer isolation</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Synchronous Setting</span>
                  <div className="font-mono text-slate-200 font-bold">PRAGMA synchronous=NORMAL</div>
                  <p className="text-[10px] text-slate-400">High transactional write rate with safety guarantees</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Snapshot Retention Window</span>
                  <div className="font-mono text-slate-200 font-bold">30 Days Historical Archive</div>
                  <p className="text-[10px] text-slate-400">Automatic pruning of cleared non-critical logs</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                  <span className="text-slate-500 font-semibold uppercase text-[10px]">Access Control &amp; RBAC</span>
                  <div className="font-mono text-sky-400 font-bold">Role-Based Triage Matrix</div>
                  <p className="text-[10px] text-slate-400">Operator, Supervisor, and Administrator permission boundaries</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
