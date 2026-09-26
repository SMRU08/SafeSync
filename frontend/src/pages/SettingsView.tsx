/**
 * SettingsView.tsx — SafeSync Professional SOC
 * Clean industrial configuration panel for inspection of AI models,
 * camera configs, PPE compliance rules, hazard thresholds, and alert policies.
 */

import React from 'react';
import {
  Settings,
  Cpu,
  ShieldCheck,
  Flame,
  Bell,
} from 'lucide-react';

interface SettingsViewProps {
  complianceConfig?: any;
  hazardConfig?: any;
}

export const SettingsView: React.FC<SettingsViewProps> = () => {
  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div>
        <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-sky-600" />
          System Configuration &amp; AI Hyperparameters
        </h2>
        <p className="text-xs text-slate-500">
          Inspection of neural network checkpoints, ByteTrack association heuristics, and deterministic risk thresholds
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. AI Detection Engine */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
            <Cpu className="w-4 h-4 text-sky-600" />
            <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">
              1. Detection Engine (YOLOv8n-PPE)
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Base Architecture:</span>
              <span className="font-mono font-semibold text-slate-800">Ultralytics YOLOv8n</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Active Checkpoint:</span>
              <span className="font-mono text-slate-800 text-[11px]">ppe_fire_smoke_v2/weights/best.pt</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Canonical Classes:</span>
              <span className="font-mono text-slate-800 text-[10px]">
                person, helmet, vest, gloves, shoes, fire, smoke
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Inference Target:</span>
              <span className="font-mono font-semibold text-emerald-600">30-60 ms / frame</span>
            </div>
          </div>
        </div>

        {/* 2. Worker Tracking & Association */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">
              2. Worker Tracking &amp; PPE Rules
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Tracker Algorithm:</span>
              <span className="font-mono font-semibold text-slate-800">ByteTrack Kalman Filter</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Spatial IoU Threshold:</span>
              <span className="font-mono font-semibold text-slate-800">0.35 IoU</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Unknown Classification:</span>
              <span className="font-mono font-semibold text-amber-600">Preserved as Neutral</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Track Persistence:</span>
              <span className="font-mono font-semibold text-slate-800">30 lost frame grace</span>
            </div>
          </div>
        </div>

        {/* 3. Hazard Detection Policies */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
            <Flame className="w-4 h-4 text-rose-500" />
            <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">
              3. Fire &amp; Smoke Temporal Policies
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Fire Confidence Threshold:</span>
              <span className="font-mono font-semibold text-slate-800">0.45</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Smoke Plume Minimum Area:</span>
              <span className="font-mono font-semibold text-slate-800">0.05 normalized bbox</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Temporal Debounce Window:</span>
              <span className="font-mono font-semibold text-slate-800">3 consecutive frames</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Spatial Clearance Cooldown:</span>
              <span className="font-mono font-semibold text-slate-800">10 seconds clean</span>
            </div>
          </div>
        </div>

        {/* 4. Alert & Incident Engine */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
            <Bell className="w-4 h-4 text-amber-500" />
            <h3 className="font-bold text-xs text-slate-800 uppercase tracking-wider">
              4. Alert Deduplication &amp; Cooldown
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Alert Cooldown Window:</span>
              <span className="font-mono font-semibold text-slate-800">30 seconds / track</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Auto-Escalation Threshold:</span>
              <span className="font-mono font-semibold text-rose-600">3 repeated violations</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Database Storage Mode:</span>
              <span className="font-mono font-semibold text-slate-800">SQLite WAL with SHA256</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">WebSocket Broadcast:</span>
              <span className="font-mono font-semibold text-emerald-600">Event-Driven (push)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
