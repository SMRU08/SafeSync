/**
 * DemoTopBanner.tsx — SafeSync Industrial SOC
 * Phase 10: Persistent Demonstration Mode Top Ribbon.
 *
 * Clearly marks demo state across all views:
 * - Never masquerades as live production telemetry
 * - Provides quick switching between the 5 canonical validation scenarios
 * - Offers direct trigger for Hackathon Guide & Architecture modal
 * - Supports seamless one-click return to LIVE MODE
 */

import React from 'react';
import {
  Sparkles,
  Tv,
  HelpCircle,
  AlertTriangle,
  Users,
  Flame,
  Award,
  Radio,
} from 'lucide-react';

export type DemoScenarioId =
  | 'safe_worker'
  | 'unknown_worker'
  | 'confirmed_violation'
  | 'multi_worker'
  | 'fire_smoke';

interface DemoTopBannerProps {
  activeScenario: DemoScenarioId;
  onSelectScenario: (id: DemoScenarioId) => void;
  onExitDemo: () => void;
  onOpenDemoGuide: () => void;
}

export const DemoTopBanner: React.FC<DemoTopBannerProps> = ({
  activeScenario,
  onSelectScenario,
  onExitDemo,
  onOpenDemoGuide,
}) => {
  const scenarios = [
    {
      id: 'safe_worker' as const,
      label: 'S1: Safe Worker',
      shortLabel: 'S1: Safe',
      icon: Tv,
      color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      activeColor: 'bg-emerald-600 text-white shadow-md',
      tooltip: 'Fully equipped worker with all required PPE present (Green / Compliant)',
    },
    {
      id: 'unknown_worker' as const,
      label: 'S2: Unknown State',
      shortLabel: 'S2: Unknown',
      icon: HelpCircle,
      color: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      activeColor: 'bg-amber-600 text-white shadow-md',
      tooltip: 'Occluded gear / limited angle; neutral evaluation with zero violation penalty',
    },
    {
      id: 'confirmed_violation' as const,
      label: 'S3: Confirmed Violation',
      shortLabel: 'S3: Violation',
      icon: AlertTriangle,
      color: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      activeColor: 'bg-rose-600 text-white shadow-md',
      tooltip: 'Missing helmet confirmed absent after 15 consecutive frames (~0.5s tolerance)',
    },
    {
      id: 'multi_worker' as const,
      label: 'S4: Multi-Worker',
      shortLabel: 'S4: Multi-Person',
      icon: Users,
      color: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
      activeColor: 'bg-sky-600 text-white shadow-md',
      tooltip: '3 concurrent workers (Safe, Unknown, Violation) tracked independently',
    },
    {
      id: 'fire_smoke' as const,
      label: 'S5: Fire & Smoke (P0)',
      shortLabel: 'S5: Combustion',
      icon: Flame,
      color: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
      activeColor: 'bg-orange-600 text-white shadow-md',
      tooltip: 'Decoupled thermal emergency; P0 incident, audible alarm, evacuation protocol',
    },
  ];

  return (
    <div className="w-full bg-[#1A120B] border-b border-amber-500/40 px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 z-35 select-none shadow-md">
      {/* Left Demo Identifier */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-black uppercase tracking-wider font-mono">
          <Sparkles className="w-3 h-3 text-amber-400 animate-spin" style={{ animationDuration: '3s' }} />
          <span>DEMO MODE ACTIVE</span>
        </div>
        <span className="text-[11px] text-amber-200/90 font-medium hidden md:inline">
          Pre-recorded benchmark scenarios • Zero alteration to production model or database
        </span>
      </div>

      {/* Middle Scenario Quick Selector */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
        {scenarios.map((sc) => {
          const isActive = activeScenario === sc.id;
          const Icon = sc.icon;
          return (
            <button
              key={sc.id}
              onClick={() => onSelectScenario(sc.id)}
              title={sc.tooltip}
              className={`px-2.5 py-1 rounded text-[11px] font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap border ${
                isActive
                  ? `${sc.activeColor} border-white/20 font-black scale-105`
                  : 'bg-slate-900/80 text-slate-300 hover:text-white border-slate-800 hover:border-slate-700'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span className="hidden sm:inline">{sc.label}</span>
              <span className="sm:hidden">{sc.shortLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Right Actions: Guide & Exit */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenDemoGuide}
          className="px-2.5 py-1 rounded bg-sky-600/30 hover:bg-sky-600/50 border border-sky-500/40 text-sky-200 text-[11px] font-bold flex items-center gap-1.5 transition cursor-pointer"
        >
          <Award className="w-3 h-3 text-sky-400" />
          <span>Guide &amp; Arch</span>
        </button>

        <button
          onClick={onExitDemo}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-[11px] font-bold flex items-center gap-1.5 transition cursor-pointer"
          title="Return to real-time live monitoring"
        >
          <Radio className="w-3 h-3 text-emerald-400" />
          <span>Live Mode</span>
        </button>
      </div>
    </div>
  );
};

export default DemoTopBanner;
