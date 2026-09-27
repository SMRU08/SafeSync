import React from 'react';
import { AlertOctagon, RefreshCw, WifiOff, Database, Cpu, CameraOff } from 'lucide-react';

export type ErrorType = 'api' | 'database' | 'ai' | 'websocket' | 'camera' | 'generic';

interface ErrorStateProps {
  type?: ErrorType;
  title?: string;
  description?: string;
  errorDetail?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  type = 'generic',
  title,
  description,
  errorDetail,
  onRetry,
  className = '',
}) => {
  const getIcon = () => {
    switch (type) {
      case 'api':
      case 'websocket':
        return WifiOff;
      case 'database':
        return Database;
      case 'ai':
        return Cpu;
      case 'camera':
        return CameraOff;
      default:
        return AlertOctagon;
    }
  };

  const getDefaultTitle = () => {
    switch (type) {
      case 'api':
        return 'Backend API Unavailable';
      case 'database':
        return 'Database Connection Lost';
      case 'ai':
        return 'AI Inference Engine Offline';
      case 'websocket':
        return 'Telemetry Stream Disconnected';
      case 'camera':
        return 'Camera Source Unreachable';
      default:
        return 'System Communication Advisory';
    }
  };

  const getDefaultDesc = () => {
    switch (type) {
      case 'api':
        return 'The FastAPI backend server is not responding. Check host connectivity or uvicorn process.';
      case 'database':
        return 'SQLite / database file is inaccessible or locked. Verify WAL journal mode.';
      case 'ai':
        return 'YOLO neural model weights failed to initialize or CUDA/CPU runtime encountered an exception.';
      case 'websocket':
        return 'Real-time WebSocket event connection dropped. Automated reconnect cycle active.';
      case 'camera':
        return 'Video capture failed from hardware device or IP stream. Check RTSP/HTTP URL.';
      default:
        return 'An unexpected service interruption occurred. Telemetry updates may be delayed.';
    }
  };

  const Icon = getIcon();

  return (
    <div
      className={`glass-card rounded-2xl p-7 flex flex-col items-center justify-center text-center border border-rose-900/40 shadow-xl ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-4 shadow-inner">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-white tracking-tight mb-1">
        {title || getDefaultTitle()}
      </h3>
      <p className="text-xs text-slate-400 max-w-md leading-relaxed mb-4">
        {description || getDefaultDesc()}
      </p>

      {errorDetail && (
        <pre className="text-[10px] font-mono bg-slate-950/80 text-rose-300 p-2.5 rounded-lg border border-slate-800 max-w-md overflow-x-auto text-left mb-4 w-full">
          {errorDetail}
        </pre>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-200 hover:text-white text-xs font-semibold rounded-lg border border-slate-700 transition flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
};
