/**
 * CameraCard.tsx — SafeSync Professional SOC
 * Compact camera hardware card for multi-camera fleet grids.
 * Clearly differentiates LIVE, OFFLINE, STANDBY, and DEGRADED states.
 */

import React from 'react';
import { Camera, AlertTriangle, Users, VideoOff, Volume2, VolumeX } from 'lucide-react';
import { CameraConfig } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface CameraCardProps {
  camera: CameraConfig;
  isSelected?: boolean;
  onSelect?: (cameraId: string) => void;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
}

export const CameraCard: React.FC<CameraCardProps> = ({
  camera,
  isSelected = false,
  onSelect,
  onToggleSpeaker,
}) => {
  const isOnline =
    camera.state === 'CONNECTED' || camera.state === 'DEGRADED' || camera.status === 'ACTIVE';
  const isDegraded = camera.state === 'DEGRADED';
  const isOffline = camera.state === 'ERROR' || camera.state === 'DISCONNECTED' || camera.status === 'OFFLINE';

  const badgeConfig = isOnline
    ? isDegraded
      ? { label: 'DEGRADED', bg: 'bg-amber-500', text: 'text-white' }
      : { label: 'LIVE', bg: 'bg-emerald-500', text: 'text-white' }
    : isOffline
    ? { label: 'OFFLINE', bg: 'bg-rose-500', text: 'text-white' }
    : { label: 'STANDBY', bg: 'bg-slate-500', text: 'text-white' };

  return (
    <div
      onClick={() => onSelect?.(camera.camera_id)}
      className={`border rounded-lg overflow-hidden bg-slate-50 flex flex-col justify-between transition cursor-pointer hover:shadow-md ${
        isSelected
          ? 'border-sky-500 ring-2 ring-sky-500/20 shadow-sm'
          : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      {/* Card Header */}
      <div className="px-2.5 py-1.5 bg-white border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="font-bold text-[10px] text-slate-800 tracking-tight">
            {camera.camera_id.toUpperCase().replace('_', '-')}
          </span>
          {onToggleSpeaker && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleSpeaker(camera.camera_id, camera.speaker_enabled === false);
              }}
              title={`Camera Speaker is ${camera.speaker_enabled !== false ? 'ON (Localized Audio Active)' : 'OFF (Audio Suppressed)'}`}
              className={`p-0.5 rounded transition cursor-pointer ${
                camera.speaker_enabled !== false
                  ? 'text-emerald-600 hover:bg-emerald-50'
                  : 'text-slate-400 hover:bg-slate-100'
              }`}
            >
              {camera.speaker_enabled !== false ? (
                <Volume2 className="w-3 h-3" />
              ) : (
                <VolumeX className="w-3 h-3 text-rose-400" />
              )}
            </button>
          )}
        </div>
        <span
          className={`text-[8px] ${badgeConfig.bg} ${badgeConfig.text} font-bold px-1.5 py-0.5 rounded tracking-wide`}
        >
          {badgeConfig.label}
        </span>
      </div>

      {/* Snapshot Preview Viewport */}
      <div className="relative aspect-video bg-slate-900 overflow-hidden flex items-center justify-center">
        {isOnline ? (
          <img
            alt={camera.name}
            src={`${API_BASE_URL}/api/cameras/${camera.camera_id}/snapshot?t=${Date.now()}`}
            onError={(e) => {
              // Hide image and show fallback icon
              (e.target as HTMLElement).style.display = 'none';
            }}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-500">
            {isOffline ? (
              <VideoOff className="w-6 h-6 opacity-40 mb-1" />
            ) : (
              <Camera className="w-6 h-6 opacity-40 mb-1" />
            )}
            <span className="text-[9px] font-medium text-slate-400">
              {isOffline ? 'No Signal' : 'Standby Mode'}
            </span>
          </div>
        )}
      </div>

      {/* Card Footer Details */}
      <div className="p-2 bg-white">
        <p className="text-[10px] font-medium text-slate-700 truncate" title={camera.name}>
          {camera.name}
        </p>
        <div className="flex items-center justify-between text-[9px] text-slate-400 mt-1">
          <span className="font-mono-nums">
            {isOnline ? `${camera.metrics?.fps?.toFixed(1) ?? '15.0'} FPS` : '0.0 FPS'}
          </span>
          <span className="flex items-center gap-0.5 text-slate-600 font-mono-nums">
            <Users className="w-2.5 h-2.5" /> {camera.metrics?.active_workers ?? 0}
          </span>
          <span
            className={`font-bold flex items-center gap-0.5 font-mono-nums ${
              (camera.metrics?.active_violations ?? 0) > 0 ? 'text-rose-500' : 'text-slate-400'
            }`}
          >
            <AlertTriangle className="w-2.5 h-2.5" /> {camera.metrics?.active_violations ?? 0}
          </span>
        </div>

        {/* Status Line */}
        <div
          className={`w-full h-1 rounded-full mt-1.5 ${
            isOnline
              ? isDegraded
                ? 'bg-amber-500'
                : 'bg-emerald-500'
              : isOffline
              ? 'bg-rose-500'
              : 'bg-slate-200'
          }`}
        />
      </div>
    </div>
  );
};

export default CameraCard;
