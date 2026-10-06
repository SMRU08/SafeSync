/**
 * WorkerSafetyLegend.tsx — SafeSync Industrial SOC
 * Standardized reusable Worker Safety State legend.
 * Display priority:
 *   ● GREEN — SAFE
 *   ● YELLOW — UNKNOWN / LIMITED VISIBILITY
 *   ● RED — CONFIRMED VIOLATION
 */

import React from 'react';

interface WorkerSafetyLegendProps {
  className?: string;
  compact?: boolean;
}

export const WorkerSafetyLegend: React.FC<WorkerSafetyLegendProps> = ({
  className = '',
  compact = false,
}) => {
  if (compact) {
    return (
      <div className={`flex items-center gap-3 text-[11px] font-medium text-slate-300 ${className}`}>
        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Safety State:</span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#22C55E]" />
          <span>SAFE</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#F5B942]" />
          <span>UNKNOWN / LIMITED VISIBILITY</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#EF4444]" />
          <span>CONFIRMED VIOLATION</span>
        </span>
      </div>
    );
  }

  return (
    <div className={`p-3 rounded-xl bg-[#0D1B2A] border border-[#20344A] text-slate-200 select-none ${className}`}>
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
        <span>Worker Safety State</span>
        <span className="font-mono text-[9px] text-slate-500">TRI-STATE VALIDATION</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <span className="w-2.5 h-2.5 rounded-full bg-[#22C55E] shrink-0" />
          <div>
            <span className="font-bold text-[#22C55E]">SAFE</span>
            <span className="block text-[10px] text-slate-400">All required PPE present</span>
          </div>
        </div>

        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F5B942] shrink-0" />
          <div>
            <span className="font-bold text-[#F5B942]">UNKNOWN</span>
            <span className="block text-[10px] text-slate-400">Limited visibility / Occluded</span>
          </div>
        </div>

        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444] shrink-0" />
          <div>
            <span className="font-bold text-[#EF4444]">CONFIRMED VIOLATION</span>
            <span className="block text-[10px] text-slate-400">Confirmed absent (&ge;15 frames)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkerSafetyLegend;
