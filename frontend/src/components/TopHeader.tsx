/**
 * TopHeader.tsx — SafeSync Professional SOC
 * Clean enterprise top header with real-time backend indicators, search, notifications,
 * operator profile, and live UTC/Local clock.
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
  const isAiReady = ['connected', 'ready', 'available', 'loaded'].includes((aiEngineStatus || '').trim().toLowerCase());
  const isDbConnected = databaseStatus === 'connected';
  const isWsConnected = wsStatus === 'CONNECTED';
  const isWsConnecting = wsStatus === 'CONNECTING';

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between sticky top-0 z-50 shadow-sm select-none">
      {/* Brand / Logo Area */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <img
            src="/logo.png"
            alt="SafeSync Logo"
            className="w-10 h-10 object-contain rounded-lg drop-shadow-md"
          />
          <div>
            <h1 className="text-sm font-extrabold tracking-tight text-slate-900 leading-none flex items-center gap-1">
              Safe<span className="text-sky-600">Sync</span>
            </h1>
            <p className="text-[9px] text-slate-400 font-medium tracking-wide mt-0.5">
              AI-Powered Safety &amp; Hazard Monitoring System
            </p>
          </div>
        </div>

        {/* Header Search Input */}
        <div className="relative w-64 md:w-72 hidden sm:block">
          <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 pointer-events-none text-slate-400">
            <Search className="w-3.5 h-3.5" />
          </span>
          <input
            className="w-full bg-slate-50 border border-slate-200 text-xs rounded-md pl-8 pr-3 py-1.5 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500 transition placeholder:text-slate-400"
            placeholder="Search cameras, workers, incidents..."
            type="text"
            onChange={(e) => onSearch?.(e.target.value)}
          />
        </div>
      </div>

      {/* Health Indicators & User Profile */}
      <div className="flex items-center gap-4 lg:gap-5">
        {/* Status Badges — Connected directly to Real Backend */}
        <div className="hidden lg:flex items-center gap-2">
          {/* API Status */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isApiOnline
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                : 'bg-rose-50/80 border-rose-200 text-rose-800'
            }`}
            title={`Backend API: ${isApiOnline ? 'Online' : 'Offline'}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isApiOnline ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'
              }`}
            />
            <span>
              API <span className="font-normal">{isApiOnline ? 'Online' : 'Offline'}</span>
            </span>
          </div>

          {/* AI Engine */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isAiReady
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                : 'bg-amber-50/80 border-amber-200 text-amber-800'
            }`}
            title={`YOLO / AI Model: ${aiEngineStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isAiReady ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
            <span>
              AI Engine{' '}
              <span className="font-normal">
                {isAiReady ? aiEngineStatus : 'Unavailable'}
              </span>
            </span>
          </div>

          {/* Database */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isDbConnected
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                : 'bg-rose-50/80 border-rose-200 text-rose-800'
            }`}
            title={`Database: ${databaseStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isDbConnected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span>
              Database{' '}
              <span className="font-normal">
                {isDbConnected ? 'Connected' : 'Disconnected'}
              </span>
            </span>
          </div>

          {/* WebSocket */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[10px] font-semibold transition ${
              isWsConnected
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                : isWsConnecting
                ? 'bg-amber-50/80 border-amber-200 text-amber-800'
                : 'bg-rose-50/80 border-rose-200 text-rose-800'
            }`}
            title={`Real-Time WebSocket: ${wsStatus}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isWsConnected
                  ? 'bg-emerald-500'
                  : isWsConnecting
                  ? 'bg-amber-500 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span>
              WebSocket{' '}
              <span className="font-normal capitalize">{wsStatus}</span>
            </span>
          </div>

          {/* Manual Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className={`p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 transition ${
                isRefreshing ? 'animate-spin text-sky-600' : ''
              }`}
              title="Refresh telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="h-4 w-px bg-slate-200 hidden sm:block" />

        {/* Right Tools: Notification Bell, Profile, Clock */}
        <div className="flex items-center gap-3">
          {/* Notification Bell */}
          <div className="relative">
            <button
              title="Active Notifications"
              className="p-1.5 text-slate-500 hover:text-slate-700 rounded-full hover:bg-slate-100 transition"
            >
              <Bell className="w-4 h-4" />
              {unreadAlertsCount > 0 && (
                <span className="absolute top-0.5 right-0.5 bg-rose-500 text-white font-bold text-[8px] w-3.5 h-3.5 rounded-full flex items-center justify-center ring-2 ring-white animate-pulse">
                  {unreadAlertsCount > 99 ? '99+' : unreadAlertsCount}
                </span>
              )}
            </button>
          </div>

          {/* User Profile Pill */}
          <div className="flex items-center gap-2 pl-1 cursor-pointer group">
            <div className="w-7 h-7 rounded-full bg-sky-700 text-white font-bold text-[10px] flex items-center justify-center shadow-sm">
              OP
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-[11px] font-bold text-slate-800 leading-tight">Safety Officer</div>
              <div className="text-[9px] text-slate-400 font-medium">SOC Control</div>
            </div>
            <ChevronDown className="w-3 h-3 text-slate-400 group-hover:text-slate-600 transition" />
          </div>

          <div className="h-4 w-px bg-slate-200 hidden md:block" />

          {/* Real-time Clock */}
          <div className="text-right hidden sm:block">
            <div className="text-[9px] text-slate-400 font-medium">{dateStr || 'Mon, 22 Sep 2026'}</div>
            <div className="text-xs font-bold text-slate-800 font-mono-nums">{timeStr || '18:32:17'}</div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopHeader;
