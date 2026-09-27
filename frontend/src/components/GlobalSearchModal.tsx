/**
 * GlobalSearchModal.tsx — SafeSync Industrial SOC
 * Command Palette & Global Telemetry Search (Phase 19).
 * Fast keyboard-navigable search across Cameras, Zones, Workers, Alerts, and Incidents.
 */

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Search,
  X,
  Camera,
  AlertTriangle,
  ArrowRight,
  Activity,
  Tv,
} from 'lucide-react';
import { CameraConfig, Alert, Incident } from '../types';
import { ActiveTab } from './Sidebar';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  cameras: CameraConfig[];
  alerts: Alert[];
  incidents: Incident[];
  onNavigate: (tab: ActiveTab) => void;
  onSelectAlert?: (alert: Alert) => void;
  onSelectIncident?: (incidentId: string) => void;
}

interface SearchResultItem {
  id: string;
  category: 'camera' | 'worker' | 'alert' | 'incident' | 'zone';
  title: string;
  subtitle: string;
  statusBadge: string;
  statusColor: string;
  icon: React.ComponentType<{ className?: string }>;
  tab: ActiveTab;
  onSelectAction: () => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  cameras,
  alerts,
  incidents,
  onNavigate,
  onSelectAlert,
  onSelectIncident,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus on open
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Global Ctrl+K / Cmd+K and Esc listeners
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Search Results Compilation
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const items: SearchResultItem[] = [];

    // 1. Search Cameras
    cameras.forEach((cam) => {
      if (
        cam.camera_id.toLowerCase().includes(q) ||
        cam.name.toLowerCase().includes(q) ||
        (cam.zone_id && cam.zone_id.toLowerCase().includes(q))
      ) {
        const isOnline = cam.state === 'CONNECTED' || cam.status === 'ACTIVE';
        items.push({
          id: `cam-${cam.camera_id}`,
          category: 'camera',
          title: cam.name || cam.camera_id,
          subtitle: `Camera ID: ${cam.camera_id} • Zone: ${cam.zone_id}`,
          statusBadge: isOnline ? 'ONLINE' : 'OFFLINE',
          statusColor: isOnline ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-slate-400 bg-slate-800 border-slate-700',
          icon: Camera,
          tab: 'cameras',
          onSelectAction: () => {
            onNavigate('cameras');
            onClose();
          },
        });
      }
    });

    // 2. Search Alerts
    alerts.forEach((alert) => {
      if (
        alert.title.toLowerCase().includes(q) ||
        alert.event_type.toLowerCase().includes(q) ||
        alert.camera_id.toLowerCase().includes(q) ||
        (alert.zone_id && alert.zone_id.toLowerCase().includes(q)) ||
        alert.alert_id.toLowerCase().includes(q)
      ) {
        items.push({
          id: `alert-${alert.alert_id}`,
          category: 'alert',
          title: alert.title || alert.event_type,
          subtitle: `Camera: ${alert.camera_id} • Zone: ${alert.zone_id || 'N/A'} • ${new Date(alert.timestamp).toLocaleTimeString()}`,
          statusBadge: alert.severity,
          statusColor: alert.severity === 'CRITICAL' ? 'text-rose-400 bg-rose-500/10 border-rose-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30',
          icon: AlertTriangle,
          tab: 'alerts',
          onSelectAction: () => {
            onNavigate('alerts');
            if (onSelectAlert) onSelectAlert(alert);
            onClose();
          },
        });
      }
    });

    // 3. Search Incidents
    incidents.forEach((inc) => {
      const typeStr = inc.event_types?.join(', ') || 'Incident';
      if (
        inc.incident_id.toLowerCase().includes(q) ||
        typeStr.toLowerCase().includes(q) ||
        inc.camera_id.toLowerCase().includes(q) ||
        (inc.zone_id && inc.zone_id.toLowerCase().includes(q))
      ) {
        items.push({
          id: `inc-${inc.incident_id}`,
          category: 'incident',
          title: `Incident: ${typeStr}`,
          subtitle: `ID: ${inc.incident_id.slice(0, 8)}... • Risk Score: ${inc.risk_score} • Status: ${inc.status}`,
          statusBadge: inc.status,
          statusColor: inc.status === 'RESOLVED' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20',
          icon: Activity,
          tab: 'alerts',
          onSelectAction: () => {
            onNavigate('alerts');
            if (onSelectIncident) onSelectIncident(inc.incident_id);
            onClose();
          },
        });
      }
    });

    return items.slice(0, 15);
  }, [query, cameras, alerts, incidents, onNavigate, onSelectAlert, onSelectIncident, onClose]);

  // Handle arrow key navigation in results
  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1 < results.length ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 >= 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) {
        results[selectedIndex].onSelectAction();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-16 sm:pt-24 px-4 select-none animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl bg-[#0c1424] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-800 bg-slate-900/80">
          <Search className="w-5 h-5 text-sky-400 flex-shrink-0 mr-3" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleInputKeyDown}
            placeholder="Search cameras, zones, workers, incidents, alerts... (Type 'camera_01', 'fire', 'helmet')"
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 text-slate-400 hover:text-white rounded"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <span className="hidden sm:inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 ml-2">
            ESC
          </span>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-2 divide-y divide-slate-800/40">
          {query.trim() === '' ? (
            <div className="p-8 text-center text-slate-400">
              <Tv className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-300">Fast SOC Global Search</p>
              <p className="text-[11px] text-slate-500 mt-1">
                Query active cameras, safety zones, personnel, or active incident traces.
              </p>
              <div className="flex items-center justify-center gap-2 mt-4 text-[10px] text-slate-400">
                <span className="px-2 py-1 rounded bg-slate-900 border border-slate-800">
                  ↑↓ to navigate
                </span>
                <span className="px-2 py-1 rounded bg-slate-900 border border-slate-800">
                  ↵ to select
                </span>
                <span className="px-2 py-1 rounded bg-slate-900 border border-slate-800">
                  ESC to close
                </span>
              </div>
            </div>
          ) : results.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <AlertTriangle className="w-7 h-7 text-amber-500/60 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-300">No matching telemetry records</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                No active cameras, incidents, or alerts match "{query}".
              </p>
            </div>
          ) : (
            results.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;

              return (
                <div
                  key={item.id}
                  onClick={item.onSelectAction}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-sky-600/20 border border-sky-500/40 shadow-sm'
                      : 'hover:bg-slate-900/60 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-300 flex-shrink-0">
                      <Icon className="w-4 h-4 text-sky-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{item.title}</span>
                        <span className="text-[9px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">{item.subtitle}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${item.statusColor}`}>
                      {item.statusBadge}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default GlobalSearchModal;
