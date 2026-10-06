/**
 * SystemStatusBar.tsx — SafeSync Industrial SOC
 * Compact Persistent System Operations Bar (Phase 30).
 * Displays real-time heartbeat of API, AI Engine, Database, WebSocket, and Camera Matrix.
 */

import React from 'react';
import {
  Camera,
  Shield,
} from 'lucide-react';
import { ActiveTab } from './Sidebar';
import { WebSocketStatus } from '../hooks/useWebSocket';

interface SystemStatusBarProps {
  apiStatus?: 'online' | 'offline' | 'checking';
  aiEngineStatus?: string;
  databaseStatus?: 'connected' | 'disconnected' | 'checking';
  wsStatus?: WebSocketStatus;
  camerasCount?: number;
  activeCamerasCount?: number;
  lastChecked?: string;
  onNavigate?: (tab: ActiveTab) => void;
}

export const SystemStatusBar: React.FC<SystemStatusBarProps> = ({
  apiStatus = 'online',
  aiEngineStatus = 'Ready',
  databaseStatus = 'connected',
  wsStatus = 'CONNECTED',
  camerasCount = 0,
  activeCamerasCount = 0,
  lastChecked,
  onNavigate,
}) => {
  const isApiOnline = apiStatus === 'online';
  const isAiReady = ['connected', 'ready', 'available', 'loaded'].includes(
    (aiEngineStatus || '').trim().toLowerCase()
  );
  const isDbConnected = databaseStatus === 'connected';
  const isWsConnected = wsStatus === 'CONNECTED';

  return (
    <div className="h-7 bg-[#080d17] border-t border-slate-800/80 px-4 flex items-center justify-between text-[11px] text-slate-400 select-none z-10">
      {/* Left: Operational Indicators */}
      <div className="flex items-center gap-4">
        {/* Core Heartbeat */}
        <div
          onClick={() => onNavigate?.('health')}
          className="flex items-center gap-1.5 cursor-pointer hover:text-slate-200 transition"
          title="Click to view detailed system health"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isApiOnline && isAiReady && isDbConnected ? 'bg-emerald-500' : 'bg-amber-500'
            }`}
          />
          <span className="font-bold text-slate-200">SafeSync Core</span>
        </div>

        <div className="h-3 w-px bg-slate-800" />

        {/* API Indicator */}
        <div
          onClick={() => onNavigate?.('health')}
          className="flex items-center gap-1.5 cursor-pointer hover:text-slate-200 transition"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isApiOnline ? 'bg-emerald-500' : apiStatus === 'checking' ? 'bg-amber-500' : 'bg-rose-500'}`} />
          <span className="font-semibold text-slate-300">API:</span>
          <span className={isApiOnline ? 'text-emerald-400 font-mono' : 'text-rose-400 font-mono'}>
            {apiStatus === 'online' ? 'OK' : apiStatus === 'checking' ? 'CHECKING' : apiStatus === 'offline' ? 'DOWN' : 'UNKNOWN'}
          </span>
        </div>

        {/* AI Ready Indicator */}
        <div
          onClick={() => onNavigate?.('health')}
          className="flex items-center gap-1.5 cursor-pointer hover:text-slate-200 transition"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isAiReady ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          <span className="font-semibold text-slate-300">AI:</span>
          <span className={isAiReady ? 'text-emerald-400 font-mono' : 'text-amber-400 font-mono'}>
            {isAiReady ? 'Ready' : aiEngineStatus || 'Standby'}
          </span>
        </div>

        {/* DB WAL Indicator */}
        <div
          onClick={() => onNavigate?.('health')}
          className="flex items-center gap-1.5 cursor-pointer hover:text-slate-200 transition"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isDbConnected ? 'bg-emerald-500' : databaseStatus === 'checking' ? 'bg-amber-500' : 'bg-rose-500'}`} />
          <span className="font-semibold text-slate-300">DB:</span>
          <span className={isDbConnected ? 'text-emerald-400 font-mono' : 'text-rose-400 font-mono'}>
            {isDbConnected ? 'WAL' : databaseStatus === 'checking' ? 'SYNC' : 'OFFLINE'}
          </span>
        </div>

        {/* WebSocket Stream */}
        <div
          onClick={() => onNavigate?.('health')}
          className="flex items-center gap-1.5 cursor-pointer hover:text-slate-200 transition hidden sm:flex"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-sky-400' : 'bg-rose-500'}`} />
          <span className="font-semibold text-slate-300">WebSocket:</span>
          <span className={isWsConnected ? 'text-sky-400 font-mono' : 'text-rose-400 font-mono'}>
            {wsStatus || '—'}
          </span>
        </div>

        {/* Active Cameras Count */}
        <div
          onClick={() => onNavigate?.('cameras')}
          className="flex items-center gap-1 cursor-pointer hover:text-slate-200 transition hidden md:flex"
        >
          <Camera className="w-3 h-3 text-slate-500" />
          <span>Matrix:</span>
          <span className="text-slate-200 font-mono-nums">
            {activeCamerasCount}/{camerasCount} Online
          </span>
        </div>
      </div>

      {/* Right: Last Heartbeat & Target Metric */}
      <div className="flex items-center gap-3 text-[10px]">
        {lastChecked && (
          <span className="text-slate-500 hidden sm:inline">
            Heartbeat: <span className="font-mono text-slate-400">{lastChecked}</span>
          </span>
        )}
        <span className="flex items-center gap-1 text-emerald-400/90 font-medium">
          <Shield className="w-3 h-3 text-emerald-400" />
          Zero Incident Standard
        </span>
      </div>
    </div>
  );
};

export default SystemStatusBar;
