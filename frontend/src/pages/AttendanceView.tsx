/**
 * AttendanceView.tsx — RAKSHYA VISION
 * Real-time daily attendance log with face recognition check-ins.
 * Shows today's check-ins and 7-day history with worker details.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Users,
  Clock,
  Camera,
  Check,
  RefreshCw,
  UserCheck,
  AlertTriangle,
  X,
} from 'lucide-react';
import { API_BASE_URL } from '../utils/constants';

interface AttendanceRecord {
  id: number;
  worker_id: string;
  worker_name: string;
  job_role: string;
  date: string;
  check_in_time: string;
  camera_id: string;
  camera_name: string;
}

interface AttendanceViewProps {
  cameras?: { camera_id: string; name: string }[];
}

export const AttendanceView: React.FC<AttendanceViewProps> = ({ cameras = [] }) => {
  const [todayLogs, setTodayLogs] = useState<AttendanceRecord[]>([]);
  const [historyLogs, setHistoryLogs] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'today' | 'history'>('today');
  const [historyDays, setHistoryDays] = useState(7);

  // Face match panel
  const [showFaceMatch, setShowFaceMatch] = useState(false);
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [matchResult, setMatchResult] = useState<any | null>(null);
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const fetchToday = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/workers/attendance/today`);
      if (r.ok) {
        const d = await r.json();
        setTodayLogs(d.logs || []);
      }
    } catch {}
    setIsLoading(false);
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/workers/attendance/history?days=${historyDays}`);
      if (r.ok) {
        const d = await r.json();
        setHistoryLogs(d.logs || []);
      }
    } catch {}
  }, [historyDays]);

  useEffect(() => {
    fetchToday();
    const iv = setInterval(fetchToday, 10000);
    return () => clearInterval(iv);
  }, [fetchToday]);

  useEffect(() => {
    if (activeTab === 'history') fetchHistory();
  }, [activeTab, fetchHistory]);

  // Face match camera
  const startMatchCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch {
      setMatchError('Camera access denied.');
    }
  };

  const stopMatchCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsCameraActive(false);
  };

  useEffect(() => {
    if (showFaceMatch) startMatchCamera();
    return () => stopMatchCamera();
  }, [showFaceMatch]);

  const captureAndMatch = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    stopMatchCamera();
    setIsMatching(true);
    setMatchError(null);
    setMatchResult(null);
    try {
      const camObj = cameras.find((c) => c.camera_id === selectedCameraId);
      const r = await fetch(`${API_BASE_URL}/api/workers/match-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_image_b64: dataUrl,
          camera_id: selectedCameraId || 'manual',
          camera_name: camObj?.name || 'Manual Check-In',
        }),
      });
      const d = await r.json();
      setMatchResult(d);
      if (d.matched) fetchToday();
    } catch {
      setMatchError('Network error during face matching.');
    } finally {
      setIsMatching(false);
    }
  };

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
    catch { return iso; }
  };

  const formatDate = (d: string) => {
    try { return new Date(d).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }); }
    catch { return d; }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Attendance & Face Recognition</h2>
          <p className="text-xs text-slate-500">Automated daily attendance via live facial recognition</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowFaceMatch(true); setMatchResult(null); setMatchError(null); }}
            className="flex items-center gap-2 px-3 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-lg shadow-sm transition"
          >
            <Camera className="w-4 h-4" />
            Manual Face Check-In
          </button>
          <button onClick={fetchToday} className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition text-slate-500">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-emerald-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Today's Check-Ins</span>
          <span className="text-3xl font-black text-white font-mono-nums">{todayLogs.length}</span>
          <span className="text-[10px] text-emerald-400">{new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-sky-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">First Check-In</span>
          <span className="text-sm font-black text-white font-mono-nums">
            {todayLogs.length > 0 ? formatTime(todayLogs[todayLogs.length - 1].check_in_time) : '--:--:--'}
          </span>
          <span className="text-[10px] text-sky-400">Earliest today</span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-amber-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Last Check-In</span>
          <span className="text-sm font-black text-white font-mono-nums">
            {todayLogs.length > 0 ? formatTime(todayLogs[0].check_in_time) : '--:--:--'}
          </span>
          <span className="text-[10px] text-amber-400">Most recent</span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-purple-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Unique Cameras</span>
          <span className="text-3xl font-black text-white font-mono-nums">
            {new Set(todayLogs.map((l) => l.camera_id)).size}
          </span>
          <span className="text-[10px] text-purple-400">Active entry points</span>
        </div>
      </div>

      {/* Tab Switch */}
      <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-1 w-fit shadow-sm">
        <button
          onClick={() => setActiveTab('today')}
          className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${activeTab === 'today' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}
        >
          Today's Log
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${activeTab === 'history' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}
        >
          History ({historyDays}d)
        </button>
      </div>

      {/* Log Table */}
      <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 overflow-hidden shadow-xl">
        <div className="px-4 py-3 bg-[#111f35] border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wide">
              {activeTab === 'today' ? "Today's Attendance" : `${historyDays}-Day History`}
            </h3>
            <span className="bg-sky-700 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
              {activeTab === 'today' ? todayLogs.length : historyLogs.length}
            </span>
          </div>
          {activeTab === 'history' && (
            <select
              value={historyDays}
              onChange={(e) => setHistoryDays(Number(e.target.value))}
              className="text-xs bg-slate-700 border border-slate-600 text-slate-200 rounded px-2 py-1 focus:outline-none"
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          )}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
            <span className="text-sm">Loading attendance...</span>
          </div>
        ) : (activeTab === 'today' ? todayLogs : historyLogs).length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <Users className="w-10 h-10 mb-2 opacity-40" />
            <p className="text-sm font-semibold text-slate-400">No attendance records</p>
            <p className="text-[11px] text-slate-500 mt-1">Records appear when workers check in via face recognition</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/50">
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Worker</th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Role</th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Check-In Time</th>
                  {activeTab === 'history' && <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Date</th>}
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Camera</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {(activeTab === 'today' ? todayLogs : historyLogs).map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-sky-700 flex items-center justify-center text-white font-bold text-[10px] flex-shrink-0">
                          {log.worker_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-white">{log.worker_name}</div>
                          <div className="text-[10px] text-slate-400 font-mono">{log.worker_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{log.job_role || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-300 font-mono-nums font-semibold">{formatTime(log.check_in_time)}</span>
                      </div>
                    </td>
                    {activeTab === 'history' && (
                      <td className="px-4 py-3 text-slate-400 text-[10px]">{formatDate(log.date)}</td>
                    )}
                    <td className="px-4 py-3">
                      <span className="text-[10px] bg-sky-900/60 border border-sky-700/50 text-sky-300 px-2 py-0.5 rounded-full font-medium">
                        {log.camera_name}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Face Match Modal */}
      {showFaceMatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0c1a2e] border border-slate-700 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 bg-[#111f35] border-b border-slate-700">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white">Manual Face Check-In</h3>
              </div>
              <button onClick={() => { stopMatchCamera(); setShowFaceMatch(false); }} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4">
              {/* Camera selector */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Select Camera</label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none"
                >
                  <option value="manual">Manual (No Camera)</option>
                  {cameras.map((c) => (
                    <option key={c.camera_id} value={c.camera_id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* Video preview */}
              <div className="relative w-full aspect-[4/3] bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
                {isMatching ? (
                  <div className="flex flex-col items-center justify-center w-full h-full gap-3">
                    <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
                    <p className="text-xs text-slate-300 font-semibold">Matching face...</p>
                  </div>
                ) : matchResult ? (
                  <div className={`flex flex-col items-center justify-center w-full h-full gap-3 p-6 ${matchResult.matched ? 'bg-emerald-950/60' : 'bg-rose-950/60'}`}>
                    {matchResult.matched ? (
                      <>
                        <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center"><Check className="w-6 h-6 text-white" /></div>
                        <div className="text-center">
                          <p className="text-sm font-black text-emerald-300">{matchResult.name}</p>
                          <p className="text-[10px] text-slate-400">{matchResult.job_role} • {matchResult.worker_id}</p>
                          <p className="text-[10px] text-slate-400 mt-1">Match confidence: {Math.round((1 - matchResult.distance) * 100)}%</p>
                          {matchResult.attendance_logged ? (
                            <p className="text-[11px] text-emerald-400 font-bold mt-2">✅ Attendance Logged!</p>
                          ) : (
                            <p className="text-[11px] text-amber-400 font-bold mt-2">⚠️ Already checked in today</p>
                          )}
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="w-12 h-12 bg-rose-500 rounded-full flex items-center justify-center"><X className="w-6 h-6 text-white" /></div>
                        <p className="text-sm font-bold text-rose-300">No match found</p>
                        <p className="text-[11px] text-slate-400">{matchResult.reason || 'Worker not registered'}</p>
                      </>
                    )}
                  </div>
                ) : (
                  <video ref={videoRef} className="w-full h-full object-cover scale-x-[-1]" muted playsInline autoPlay />
                )}
                {isCameraActive && !matchResult && (
                  <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/60 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
                    <span className="text-[9px] text-white font-bold">LIVE</span>
                  </div>
                )}
              </div>
              <canvas ref={canvasRef} className="hidden" />

              {matchError && (
                <div className="flex items-center gap-2 px-3 py-2 bg-rose-900/40 border border-rose-600/50 rounded-lg">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  <p className="text-[11px] text-rose-300">{matchError}</p>
                </div>
              )}

              {!matchResult ? (
                <button
                  onClick={captureAndMatch}
                  disabled={!isCameraActive || isMatching}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-bold rounded-xl transition"
                >
                  <Camera className="w-4 h-4" />
                  Capture & Match Face
                </button>
              ) : (
                <button
                  onClick={() => { setMatchResult(null); setMatchError(null); startMatchCamera(); }}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-slate-700 hover:bg-slate-600 text-white text-sm font-bold rounded-xl transition"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Another Face
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceView;
