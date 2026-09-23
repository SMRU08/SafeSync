/**
 * AnalyticsView.tsx — RAKSHYA VISION Professional SOC
 * Safety & Compliance Analytics, Incident Distribution, and Temporal Trends.
 * Displays real-time aggregations with clean industrial visualizations.
 */

import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Alert, Incident, RiskSummary } from '../types';

interface AnalyticsViewProps {
  alerts: Alert[];
  incidents?: Incident[];
  summary?: RiskSummary | null;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ alerts }) => {
  // Aggregate real stats
  const totalAlerts = alerts.length;
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length;
  const mediumCount = alerts.filter((a) => a.severity === 'MEDIUM').length;
  const lowCount = alerts.filter((a) => a.severity === 'LOW').length;

  const ppeViolations = alerts.filter((a) => a.event_type.startsWith('MISSING_') || a.event_type.includes('PPE')).length;
  const fireHazards = alerts.filter((a) => a.event_type.includes('FIRE')).length;
  const smokeHazards = alerts.filter((a) => a.event_type.includes('SMOKE')).length;

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div>
        <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-sky-600" />
          Safety Analytics &amp; Compliance Trends
        </h2>
        <p className="text-xs text-slate-500">
          Aggregated plant hazard telemetry, PPE compliance distribution, and incident frequency metrics
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Total Recorded Alerts</span>
          <div className="text-xl font-extrabold text-slate-900 font-mono-nums mt-1">
            {totalAlerts}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Cumulative telemetry logs</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Critical Incidents</span>
          <div className="text-xl font-extrabold text-rose-600 font-mono-nums mt-1">
            {criticalCount}
          </div>
          <p className="text-[10px] text-rose-500 mt-0.5">Requires immediate action</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">PPE Infractions</span>
          <div className="text-xl font-extrabold text-amber-600 font-mono-nums mt-1">
            {ppeViolations}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Non-compliant detections</p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500">Fire / Smoke Events</span>
          <div className="text-xl font-extrabold text-slate-900 font-mono-nums mt-1">
            {fireHazards + smokeHazards}
          </div>
          <p className="text-[10px] text-emerald-600 mt-0.5">Thermal monitoring events</p>
        </div>
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Severity Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <h3 className="text-xs font-bold text-slate-800 mb-3 uppercase tracking-wider">
            Alert Severity Breakdown
          </h3>

          <div className="space-y-3">
            {[
              { label: 'Critical', count: criticalCount, color: 'bg-rose-600' },
              { label: 'High', count: highCount, color: 'bg-rose-500' },
              { label: 'Medium', count: mediumCount, color: 'bg-amber-500' },
              { label: 'Low', count: lowCount, color: 'bg-sky-500' },
            ].map((s, idx) => {
              const pct = totalAlerts > 0 ? Math.round((s.count / totalAlerts) * 100) : 0;
              return (
                <div key={idx}>
                  <div className="flex justify-between items-center text-xs mb-1 font-medium">
                    <span className="text-slate-700">{s.label}</span>
                    <span className="font-mono-nums font-bold text-slate-800">
                      {s.count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full ${s.color}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Hazard Category Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <h3 className="text-xs font-bold text-slate-800 mb-3 uppercase tracking-wider">
            Hazard Categories
          </h3>

          <div className="space-y-3">
            {[
              { label: 'Missing Safety Helmet', count: alerts.filter((a) => a.event_type.includes('HELMET')).length },
              { label: 'Missing Safety Vest', count: alerts.filter((a) => a.event_type.includes('VEST')).length },
              { label: 'Missing Gloves', count: alerts.filter((a) => a.event_type.includes('GLOVE')).length },
              { label: 'Missing Footwear', count: alerts.filter((a) => a.event_type.includes('FOOTWEAR')).length },
              { label: 'Fire Anomaly', count: fireHazards },
              { label: 'Smoke Plume', count: smokeHazards },
            ].map((cat, idx) => {
              const pct = totalAlerts > 0 ? Math.round((cat.count / totalAlerts) * 100) : 0;
              return (
                <div key={idx}>
                  <div className="flex justify-between items-center text-xs mb-1 font-medium">
                    <span className="text-slate-700">{cat.label}</span>
                    <span className="font-mono-nums font-bold text-slate-800">{cat.count}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-sky-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, pct * 2)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsView;
