/**
 * TopHeader.tsx — SafeSync Industrial SOC
 * Control-room top header with real-time backend indicators, search, notifications,
 * operator profile, pulsating status rings, and live UTC/Local clock.
 */

import React, { useState, useEffect } from 'react';
import { Search, Bell, ChevronDown, RefreshCw } from 'lucide-react';
import { WebSocketStatus } from '../hooks/useWebSocket';

export interface TopHeaderProps {
  onSearch?: (query: string) => void;
  unreadAlertsCount?: number;
  apiStatus?: 'online' | 'offline' | 'checking';
  aiEngineStatus?: string;
  databaseStatus?: 'connected' | 'disconnected' | 'checking';
  wsStatus?: WebSocketStatus;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onSearch,
  unreadAlertsCount = 0,
  apiStatus = 'online',
  aiEngineStatus = 'Ready',
  databaseStatus = 'connected',
  wsStatus = 'CONNECTED',
  onRefresh,
  isRefreshing = false,
}) => {
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
      setDateStr(
        now.toLocaleDateString('en-GB', {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const isApiOnline = apiStatus === 'online';
  const isAiReady = ['connected', 'ready', 'available', 'loaded'].includes(
    (aiEngineStatus || '').trim().toLowerCase()
  );
  const isDbConnected = databaseStatus === 'connected';
  const isWsConnected = wsStatus === 'CONNECTED';
  const isWsConnecting = wsStatus === 'CONNECTING';

  return (
    <header className="h-14 bg-[#0c1424]/95 backdrop-blur-md border-b border-slate-800/80 px-4 flex items-center justify-between sticky top-0 z-50 shadow-md select-none text-slate-100">
      {/* Brand / Logo Area */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <img
            src="/logo.png"
            alt="SafeSync Logo"
            className="w-9 h-9 object-contain rounded-lg drop-shadow-md border border-slate-800"
          />
          <div>
            <h1 className="text-sm font-black tracking-tight text-white leading-none flex items-center gap-1">
              Safe<span className="text-sky-400">Sync</span>
              <span className="text-[9px] font-mono font-normal px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 ml-1">
                SOC
              </span>
            </h1>
            <p className="text-[9px] text-slate-400 font-medium tracking-wide mt-0.5">
              AI Industrial Hazard &amp; Compliance Monitor
            </p>
          </div>
        </div>

        {/* Header Search Input */}
        <div className="relative w-64 md:w-72 hidden sm:block">
          <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 pointer-events-none text-slate-500">
            <Search className="w-3.5 h-3.5" />
          </span>
          <input
            className="w-full bg-slate-900/80 border border-slate-800 text-xs text-slate-200 rounded-md pl-8 pr-3 py-1.5 focus:bg-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500 transition placeholder:text-slate-500"
            placeholder="Search cameras, workers, infractions..."
            type="text"
            onChange={(e) => onSearch?.(e.target.value)}
          />
        </div>
      </div>

      {/* Health Indicators & User Profile */}
      <div className="flex items-center gap-4 lg:gap-5">
        {/* Real Backend Telemetry Status Badges */}
        <div className="hidden lg:flex items-center gap-2">
          {/* API Status */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isApiOnline
                ? 'bg-slate-900/80 border-emerald-900/40 text-emerald-400'
                : 'bg-slate-900/80 border-rose-900/40 text-rose-400'
            }`}
            title={`Backend API: ${isApiOnline ? 'Online' : 'Offline'}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isApiOnline ? 'bg-emerald-500 ring-pulse-active' : 'bg-rose-500 ring-pulse-offline'
              }`}
            />
            <span>
              API <span className="font-normal text-slate-400">{isApiOnline ? 'Online' : 'Offline'}</span>
            </span>
          </div>

          {/* AI Engine */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isAiReady
                ? 'bg-slate-900/80 border-emerald-900/40 text-emerald-400'
                : 'bg-slate-900/80 border-amber-900/40 text-amber-400'
            }`}
            title={`YOLO / AI Model: ${aiEngineStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isAiReady ? 'bg-emerald-500 ring-pulse-active' : 'bg-amber-500 ring-pulse-warning'
              }`}
            />
            <span>
              AI Engine{' '}
              <span className="font-normal text-slate-400">
                {isAiReady ? aiEngineStatus : 'Standby'}
              </span>
            </span>
          </div>

          {/* Database */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isDbConnected
                ? 'bg-slate-900/80 border-emerald-900/40 text-emerald-400'
                : 'bg-slate-900/80 border-rose-900/40 text-rose-400'
            }`}
            title={`Database: ${databaseStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isDbConnected ? 'bg-emerald-500 ring-pulse-active' : 'bg-rose-500 ring-pulse-offline'
              }`}
            />
            <span>
              DB <span className="font-normal text-slate-400">{isDbConnected ? 'WAL' : 'Offline'}</span>
            </span>
          </div>

          {/* WebSocket */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isWsConnected
                ? 'bg-slate-900/80 border-sky-900/40 text-sky-400'
                : isWsConnecting
                ? 'bg-slate-900/80 border-amber-900/40 text-amber-400'
                : 'bg-slate-900/80 border-rose-900/40 text-rose-400'
            }`}
            title={`Real-Time WebSocket: ${wsStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isWsConnected
                  ? 'bg-sky-500 ring-pulse-active'
                  : isWsConnecting
                  ? 'bg-amber-500 ring-pulse-warning'
                  : 'bg-rose-500 ring-pulse-offline'
              }`}
            />
            <span>
              WS <span className="font-normal text-slate-400 capitalize">{wsStatus.toLowerCase()}</span>
            </span>
          </div>

          {/* Manual Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className={`p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition ${
                isRefreshing ? 'animate-spin text-sky-400' : ''
              }`}
              title="Refresh telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="h-4 w-px bg-slate-800 hidden sm:block" />

        {/* Right Tools: Notification Bell, Profile, Clock */}
        <div className="flex items-center gap-3">
          {/* Notification Bell */}
          <div className="relative">
            <button
              title="Active Notifications"
              className="p-1.5 text-slate-400 hover:text-white rounded-full hover:bg-slate-800 transition cursor-pointer"
            >
              <Bell className="w-4 h-4" />
              {unreadAlertsCount > 0 && (
                <span className="absolute top-0.5 right-0.5 bg-rose-500 text-white font-bold text-[8px] w-3.5 h-3.5 rounded-full flex items-center justify-center ring-2 ring-[#0c1424] animate-pulse">
                  {unreadAlertsCount > 99 ? '99+' : unreadAlertsCount}
                </span>
              )}
            </button>
          </div>

          {/* User Profile Pill */}
          <div className="flex items-center gap-2 pl-1 cursor-pointer group">
            <div className="w-7 h-7 rounded-full bg-sky-600 text-white font-bold text-[10px] flex items-center justify-center shadow-sm">
              SO
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-[11px] font-bold text-slate-200 leading-tight">Safety Officer</div>
              <div className="text-[9px] text-slate-400 font-medium">SOC Control Station</div>
            </div>
            <ChevronDown className="w-3 h-3 text-slate-500 group-hover:text-slate-300 transition" />
          </div>

          <div className="h-4 w-px bg-slate-800 hidden md:block" />

          {/* Real-time Clock */}
          <div className="text-right hidden sm:block">
            <div className="text-[9px] text-slate-400 font-medium">{dateStr || 'Mon, 22 Sep 2026'}</div>
            <div className="text-xs font-bold text-white font-mono-nums">{timeStr || '18:32:17'}</div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopHeader;
