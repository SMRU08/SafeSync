/**
 * PPEStatusBadge.tsx — SafeSync Phase 5
 * Reusable, high-contrast, accessible PPE item status component.
 *
 * Adheres strictly to Section 15, 48 & 51:
 *   - GREEN  (#22C55E): PRESENT   (✓ PRESENT)
 *   - YELLOW (#F5B942): UNKNOWN   (? UNKNOWN / VISIBILITY LIMITED)
 *   - RED    (#EF4444): ABSENT    (✕ ABSENT)
 *   - SLATE  (#94A3B8): PLANNED   (Goggles extensible, not currently active in V3)
 *
 * Never relies on color alone — combines explicit text, accessible icon, and high-contrast borders.
 */

import React from 'react';
import {
  HardHat,
  Shirt,
  Hand,
  Footprints,
  Glasses,
  Check,
  X,
  HelpCircle,
  Clock,
  Shield,
} from 'lucide-react';
import { PPEPresence } from '../types';

export type PPEItemCategory = 'helmet' | 'safety_vest' | 'gloves' | 'safety_footwear' | 'goggles' | string;

interface PPEStatusBadgeProps {
  item: PPEItemCategory;
  status: PPEPresence | 'PLANNED';
  label?: string;
  confidence?: number;
  isOccluded?: boolean;
  compact?: boolean;
  showIcon?: boolean;
  className?: string;
}

const ITEM_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  helmet: { label: 'Safety Helmet', icon: HardHat },
  safety_vest: { label: 'Safety Vest', icon: Shirt },
  gloves: { label: 'Protective Gloves', icon: Hand },
  safety_footwear: { label: 'Safety Footwear', icon: Footprints },
  goggles: { label: 'Eye Protection', icon: Glasses },
};

export const PPEStatusBadge: React.FC<PPEStatusBadgeProps> = ({
  item,
  status,
  label: customLabel,
  confidence,
  isOccluded = false,
  compact = false,
  showIcon = true,
  className = '',
}) => {
  const config = ITEM_CONFIG[item.toLowerCase()] || { label: customLabel || item, icon: Shield };
  const Icon = config.icon;
  const displayLabel = customLabel || config.label;

  // Handle special case for Goggles (Section 2 & 51)
  if (item.toLowerCase() === 'goggles' || status === 'PLANNED') {
    return (
      <div
        className={`inline-flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg border border-slate-700/80 bg-slate-800/40 text-slate-400 text-xs ${className}`}
        title="Goggles detection is planned for future releases (V3 model includes Helmet, Vest, Gloves, Footwear)"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {showIcon && <Icon className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
          <span className="font-semibold text-slate-300 truncate">{displayLabel}</span>
        </div>
        <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-bold shrink-0">
          <Clock className="w-2.5 h-2.5" /> PLANNED
        </span>
      </div>
    );
  }

  if (compact) {
    if (status === 'PRESENT') {
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 ${className}`}
          title={`${displayLabel}: PRESENT${confidence !== undefined ? ` (${Math.round(confidence * 100)}%)` : ''}`}
        >
          <Check className="w-2.5 h-2.5 shrink-0" />
          <span>✓ PRESENT</span>
        </span>
      );
    }
    if (status === 'ABSENT') {
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 ${className}`}
          title={`${displayLabel}: ABSENT (Confirmed after 15 frames)`}
        >
          <X className="w-2.5 h-2.5 shrink-0" />
          <span>✕ ABSENT</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-[#F5B942] border border-amber-500/30 ${className}`}
        title={`${displayLabel}: UNKNOWN (Visibility limited — non-punitive)`}
      >
        <HelpCircle className="w-2.5 h-2.5 shrink-0 text-[#F5B942]" />
        <span>? UNKNOWN</span>
      </span>
    );
  }

  // Full Row / Card display
  if (status === 'PRESENT') {
    return (
      <div
        className={`flex items-center justify-between p-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 transition ${className}`}
      >
        <div className="flex items-center gap-2 min-w-0">
          {showIcon && <Icon className="w-4 h-4 text-emerald-400 shrink-0" />}
          <span className="text-xs font-semibold text-slate-200 truncate">{displayLabel}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {confidence !== undefined && (
            <span className="text-[10px] font-mono text-emerald-400/80">
              {Math.round(confidence * 100)}%
            </span>
          )}
          <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            <Check className="w-2.5 h-2.5" /> ✓ PRESENT
          </span>
        </div>
      </div>
    );
  }

  if (status === 'ABSENT') {
    return (
      <div
        className={`flex items-center justify-between p-2 rounded-lg border border-rose-500/40 bg-rose-500/10 text-rose-300 transition ${className}`}
      >
        <div className="flex items-center gap-2 min-w-0">
          {showIcon && <Icon className="w-4 h-4 text-rose-400 shrink-0" />}
          <span className="text-xs font-semibold text-slate-200 truncate">{displayLabel}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <X className="w-2.5 h-2.5" /> ✕ ABSENT
          </span>
        </div>
      </div>
    );
  }

  // UNKNOWN / VISIBILITY LIMITED (Yellow: #F5B942)
  return (
    <div
      className={`flex items-center justify-between p-2 rounded-lg border border-amber-500/30 bg-amber-500/10 text-[#F5B942] transition ${className}`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {showIcon && <Icon className="w-4 h-4 text-[#F5B942] shrink-0" />}
        <span className="text-xs font-semibold text-slate-200 truncate">{displayLabel}</span>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-[#F5B942] border border-amber-500/40">
          <HelpCircle className="w-2.5 h-2.5" />
          {isOccluded ? '? VISIBILITY LIMITED' : '? UNKNOWN'}
        </span>
      </div>
    </div>
  );
};
