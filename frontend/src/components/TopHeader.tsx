import React, { useState, useEffect } from 'react';

interface TopHeaderProps {
  onSearch?: (query: string) => void;
  unreadAlertsCount?: number;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onSearch,
  unreadAlertsCount = 3,
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

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between sticky top-0 z-50">
      {/* Brand / Logo Area */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-700 to-cyan-500 flex items-center justify-center text-white shadow-sm shadow-cyan-500/20">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 2.18l7 3.12v4.7c0 4.67-3.13 9.07-7 10.18-3.87-1.11-7-5.51-7-10.18V6.3l7-3.12z" />
              <path d="M12 6a4 4 0 100 8 4 4 0 000-8zm0 6a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-extrabold tracking-tight text-slate-900 leading-none flex items-center gap-1">
              RAKSHYA <span className="text-sky-600">VISION</span>
            </h1>
            <p className="text-[9px] text-slate-400 font-medium tracking-wide mt-0.5">
              AI-Powered Safety &amp; Hazard Monitoring System
            </p>
          </div>
        </div>

        {/* Header Search Input */}
        <div className="relative w-72">
          <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 pointer-events-none text-slate-400">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
              />
            </svg>
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
      <div className="flex items-center gap-5">
        {/* Status Badges */}
        <div className="hidden lg:flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-[10px] font-semibold text-emerald-800">
              API <span className="font-normal text-emerald-600">Online</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-[10px] font-semibold text-emerald-800">
              AI Engine <span className="font-normal text-emerald-600">Ready</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-[10px] font-semibold text-emerald-800">
              Database <span className="font-normal text-emerald-600">Connected</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50/80 border border-emerald-100 rounded-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-[10px] font-semibold text-emerald-800">
              WebSocket <span className="font-normal text-emerald-600">Connected</span>
            </span>
          </div>
        </div>

        <div className="h-4 w-px bg-slate-200 hidden sm:block"></div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-3">
          {/* Notification Bell */}
          <button
            title="Active Notifications"
            className="relative p-1.5 text-slate-500 hover:text-slate-700 rounded-full hover:bg-slate-100 transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
              />
            </svg>
            {unreadAlertsCount > 0 && (
              <span className="absolute top-0.5 right-0.5 bg-rose-500 text-white font-bold text-[8px] w-3.5 h-3.5 rounded-full flex items-center justify-center ring-2 ring-white">
                {unreadAlertsCount}
              </span>
            )}
          </button>

          {/* User Profile Pill */}
          <div className="flex items-center gap-2 pl-1 cursor-pointer group">
            <div className="w-7 h-7 rounded-full bg-sky-700 text-white font-bold text-[10px] flex items-center justify-center">
              SN
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-[11px] font-bold text-slate-800 leading-tight">Sahil</div>
              <div className="text-[9px] text-slate-400 font-medium">Operator</div>
            </div>
            <svg
              className="w-3 h-3 text-slate-400 group-hover:text-slate-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </div>

          <div className="h-4 w-px bg-slate-200"></div>

          {/* Real-time Clock */}
          <div className="text-right">
            <div className="text-[9px] text-slate-400 font-medium">{dateStr || 'Mon, 22 Sep 2026'}</div>
            <div className="text-xs font-bold text-slate-800 font-mono-nums">{timeStr || '18:32:17'}</div>
          </div>
        </div>
      </div>
    </header>
  );
};
