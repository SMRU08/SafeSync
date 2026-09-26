/**
 * AttendanceView.tsx — SafeSync
 * Real-time daily attendance log with biometric face recognition check-ins.
 * Supports:
 * - Webcam facial check-in
 * - Photo file upload check-in (drag & drop / browse)
 * - System camera snapshot check-in
 * - Deduplicated daily check-in logs and historical audit trails
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
  UploadCloud,
  Video,
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

type CheckInSource = 'webcam' | 'upload' | 'camera_stream';

export const AttendanceView: React.FC<AttendanceViewProps> = ({ cameras = [] }) => {
  const [todayLogs, setTodayLogs] = useState<AttendanceRecord[]>([]);
  const [historyLogs, setHistoryLogs] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'today' | 'history'>('today');
  const [historyDays, setHistoryDays] = useState(7);

  // Face match modal state
  const [showFaceMatch, setShowFaceMatch] = useState(false);
  const [checkInSource, setCheckInSource] = useState<CheckInSource>('webcam');
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || 'manual');
  const [matchResult, setMatchResult] = useState<any | null>(null);
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [uploadedPreview, setUploadedPreview] = useState<string | null>(null);
  const [isCapturingStream, setIsCapturingStream] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    const iv = setInterval(fetchToday, 8000);
    return () => clearInterval(iv);
  }, [fetchToday]);

  useEffect(() => {
    if (activeTab === 'history') fetchHistory();
  }, [activeTab, fetchHistory]);

  // Webcam controls
  const startMatchCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err: any) {
      setCameraError('Camera access denied or webcam not found.');
      setIsCameraActive(false);
    }
  };

  const stopMatchCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsCameraActive(false);
  };

  useEffect(() => {
    if (showFaceMatch && checkInSource === 'webcam') {
      startMatchCamera();
    } else {
      stopMatchCamera();
    }
    return () => stopMatchCamera();
  }, [showFaceMatch, checkInSource]);

  // Send photo to backend for matching
  const sendMatchRequest = async (imageDataUrl: string, camId?: string) => {
    setIsMatching(true);
    setMatchError(null);
    setMatchResult(null);
    try {
      const targetCamId = camId || selectedCameraId || 'manual';
      const camObj = cameras.find((c) => c.camera_id === targetCamId);
      const r = await fetch(`${API_BASE_URL}/api/workers/match-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_image_b64: imageDataUrl,
          camera_id: targetCamId,
          camera_name: camObj?.name || 'Manual Check-In',
        }),
      });
      const d = await r.json();
      setMatchResult(d);
      if (d.matched) {
        fetchToday();
      }
    } catch {
      setMatchError('Network error during face matching.');
    } finally {
      setIsMatching(false);
    }
  };

  // Capture from webcam & match
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
    await sendMatchRequest(dataUrl);
  };

  // Upload photo file & match
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      const result = event.target?.result as string;
      setUploadedPreview(result);
      await sendMatchRequest(result);
    };
    reader.readAsDataURL(file);
  };

  // Capture snapshot from system stream & match
  const captureStreamAndMatch = async () => {
    if (!selectedCameraId || selectedCameraId === 'manual') return;
    setIsCapturingStream(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/cameras/${selectedCameraId}/snapshot?t=${Date.now()}`);
      if (!res.ok) throw new Error('Could not get frame from camera.');
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onloadend = async () => {
        const b64 = reader.result as string;
        setUploadedPreview(b64);
        setIsCapturingStream(false);
        await sendMatchRequest(b64, selectedCameraId);
      };
      reader.readAsDataURL(blob);
    } catch (err: any) {
      setMatchError(err.message || 'Stream capture failed');
      setIsCapturingStream(false);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const formatDate = (d: string) => {
    try {
      return new Date(d).toLocaleDateString('en-IN', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
      });
    } catch {
      return d;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 bg-[#eef3f9]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Attendance &amp; Biometrics</h2>
          <p className="text-xs text-slate-500">Automated daily attendance logging via facial biometric matching</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setShowFaceMatch(true);
              setMatchResult(null);
              setMatchError(null);
              setUploadedPreview(null);
              setCheckInSource('webcam');
            }}
            className="flex items-center gap-2 px-3.5 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-lg shadow-sm transition"
          >
            <Camera className="w-4 h-4" />
            Biometric Check-In
          </button>
          <button
            onClick={fetchToday}
            className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition text-slate-500"
            title="Refresh Attendance Log"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden shadow-lg">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-emerald-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Today's Check-Ins</span>
          <span className="text-3xl font-black text-white font-mono-nums">{todayLogs.length}</span>
          <span className="text-[10px] text-emerald-400">
            {new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
          </span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden shadow-lg">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-sky-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">First Check-In</span>
          <span className="text-sm font-black text-white font-mono-nums">
            {todayLogs.length > 0 ? formatTime(todayLogs[todayLogs.length - 1].check_in_time) : '--:--:--'}
          </span>
          <span className="text-[10px] text-sky-400">Earliest check-in</span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden shadow-lg">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-amber-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Latest Check-In</span>
          <span className="text-sm font-black text-white font-mono-nums">
            {todayLogs.length > 0 ? formatTime(todayLogs[0].check_in_time) : '--:--:--'}
          </span>
          <span className="text-[10px] text-amber-400">Most recent</span>
        </div>
        <div className="bg-[#0c1a2e] rounded-xl border border-slate-700 p-4 flex flex-col gap-1 relative overflow-hidden shadow-lg">
          <div className="absolute inset-x-0 bottom-0 h-1 bg-purple-500" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Monitored Cameras</span>
          <span className="text-3xl font-black text-white font-mono-nums">
            {new Set(todayLogs.map((l) => l.camera_id)).size}
          </span>
          <span className="text-[10px] text-purple-400">Active entry gates</span>
        </div>
      </div>

      {/* Tab Switch */}
      <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-1 w-fit shadow-xs">
        <button
          onClick={() => setActiveTab('today')}
          className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${
            activeTab === 'today' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-500 hover:bg-slate-100'
          }`}
        >
          Today's Log
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${
            activeTab === 'history' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-500 hover:bg-slate-100'
          }`}
        >
          History ({historyDays}d)
        </button>
      </div>

      {/* Attendance Ledger Table */}
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
            <span className="text-sm">Loading attendance ledger...</span>
          </div>
        ) : (activeTab === 'today' ? todayLogs : historyLogs).length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <Users className="w-10 h-10 mb-2 opacity-30 text-slate-400" />
            <p className="text-sm font-semibold text-slate-400">No attendance entries recorded yet</p>
            <p className="text-[11px] text-slate-500 mt-1">
              Check-ins appear automatically upon successful facial biometric matching
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/50">
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Worker
                  </th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Designation
                  </th>
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Check-In Time
                  </th>
                  {activeTab === 'history' && (
                    <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Date
                    </th>
                  )}
                  <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Origin Gate / Camera
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {(activeTab === 'today' ? todayLogs : historyLogs).map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
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
                        <span className="text-emerald-300 font-mono-nums font-semibold">
                          {formatTime(log.check_in_time)}
                        </span>
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

      {/* Biometric Check-In Modal */}
      {showFaceMatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0c1a2e] border border-slate-700 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between px-5 py-3.5 bg-[#111f35] border-b border-slate-700">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-white">Biometric Face Check-In</h3>
              </div>
              <button
                onClick={() => {
                  stopMatchCamera();
                  setShowFaceMatch(false);
                }}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex flex-col gap-4">
              {/* Method Switch Tabs */}
              {!matchResult && (
                <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl">
                  <button
                    onClick={() => {
                      setCheckInSource('webcam');
                      setUploadedPreview(null);
                      setMatchError(null);
                    }}
                    className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 ${
                      checkInSource === 'webcam'
                        ? 'bg-sky-600 text-white shadow-xs'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Camera className="w-3.5 h-3.5" />
                    Webcam
                  </button>
                  <button
                    onClick={() => {
                      setCheckInSource('upload');
                      stopMatchCamera();
                      setMatchError(null);
                    }}
                    className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 ${
                      checkInSource === 'upload'
                        ? 'bg-sky-600 text-white shadow-xs'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <UploadCloud className="w-3.5 h-3.5" />
                    Upload File
                  </button>
                  <button
                    onClick={() => {
                      setCheckInSource('camera_stream');
                      stopMatchCamera();
                      setMatchError(null);
                    }}
                    className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 ${
                      checkInSource === 'camera_stream'
                        ? 'bg-sky-600 text-white shadow-xs'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Video className="w-3.5 h-3.5" />
                    Stream Frame
                  </button>
                </div>
              )}

              {/* Camera Selector (Gate/Station assignment) */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Assign Entry Gate / Camera
                </label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none"
                >
                  <option value="manual">Manual Verification Station</option>
                  {cameras.map((c) => (
                    <option key={c.camera_id} value={c.camera_id}>
                      {c.name} ({c.camera_id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Media Preview & Match Status */}
              <div className="relative w-full aspect-[4/3] bg-slate-900 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center">
                {isMatching ? (
                  <div className="flex flex-col items-center justify-center w-full h-full gap-3">
                    <RefreshCw className="w-9 h-9 text-sky-400 animate-spin" />
                    <p className="text-xs text-slate-300 font-bold">Scanning Face Biometrics...</p>
                  </div>
                ) : matchResult ? (
                  <div
                    className={`flex flex-col items-center justify-center w-full h-full gap-3 p-5 text-center ${
                      matchResult.matched ? 'bg-emerald-950/70' : 'bg-rose-950/70'
                    }`}
                  >
                    {matchResult.matched ? (
                      <>
                        <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                          <Check className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <p className="text-base font-black text-white">{matchResult.name}</p>
                          <p className="text-xs text-emerald-300 font-semibold">{matchResult.job_role}</p>
                          <p className="text-[10px] text-slate-400 mt-1">ID: {matchResult.worker_id}</p>
                          {matchResult.attendance_logged ? (
                            <div className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/20 border border-emerald-500/40 rounded-full text-emerald-300 text-xs font-bold">
                              <Check className="w-3.5 h-3.5" /> Attendance Recorded
                            </div>
                          ) : (
                            <div className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/20 border border-amber-500/40 rounded-full text-amber-300 text-xs font-bold">
                              <Clock className="w-3.5 h-3.5" /> Already Checked In Today
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="w-12 h-12 bg-rose-500 rounded-full flex items-center justify-center shadow-lg">
                          <X className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white">Face Not Recognized</p>
                          <p className="text-[11px] text-slate-400 mt-1">
                            {matchResult.reason || 'Worker is not enrolled in the database.'}
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                ) : uploadedPreview ? (
                  <img src={uploadedPreview} alt="Preview" className="w-full h-full object-cover" />
                ) : checkInSource === 'webcam' ? (
                  isCameraActive ? (
                    <video
                      ref={videoRef}
                      className="w-full h-full object-cover scale-x-[-1]"
                      muted
                      playsInline
                      autoPlay
                    />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-slate-400 p-4 text-center">
                      <Camera className="w-9 h-9 text-slate-500" />
                      {cameraError ? (
                        <div className="space-y-2">
                          <p className="text-[11px] text-amber-300 font-semibold">{cameraError}</p>
                          <button
                            onClick={() => setCheckInSource('upload')}
                            className="mt-1 px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white text-[10px] font-bold rounded shadow transition"
                          >
                            Switch to Upload Photo
                          </button>
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400">Initializing webcam...</p>
                      )}
                    </div>
                  )
                ) : checkInSource === 'upload' ? (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center justify-center w-full h-full p-4 border-2 border-dashed border-slate-600 hover:border-sky-500 rounded-xl cursor-pointer text-center group transition"
                  >
                    <UploadCloud className="w-9 h-9 text-sky-400 group-hover:scale-110 transition" />
                    <p className="text-xs font-bold text-white mt-2">Click to Upload Worker Photo</p>
                    <p className="text-[10px] text-slate-400 mt-1">JPG, PNG, WEBP</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center w-full h-full p-3 text-center gap-1.5">
                    <Video className="w-8 h-8 text-sky-400" />
                    <p className="text-xs font-bold text-white">Capture from Stream</p>
                    <p className="text-[10px] text-slate-400">Grab frame from {selectedCameraId}</p>
                  </div>
                )}

                {/* Webcam Live Indicator */}
                {isCameraActive && !matchResult && checkInSource === 'webcam' && (
                  <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/60 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
                    <span className="text-[9px] text-white font-bold">WEBCAM</span>
                  </div>
                )}
              </div>

              {/* Hidden elements */}
              <canvas ref={canvasRef} className="hidden" />
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileUpload}
              />

              {matchError && (
                <div className="flex items-center gap-2 px-3 py-2 bg-rose-900/40 border border-rose-600/50 rounded-lg">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                  <p className="text-[11px] text-rose-300">{matchError}</p>
                </div>
              )}

              {/* Action Buttons */}
              {!matchResult ? (
                checkInSource === 'webcam' ? (
                  <button
                    onClick={captureAndMatch}
                    disabled={!isCameraActive || isMatching}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-bold rounded-xl transition shadow"
                  >
                    <Camera className="w-4 h-4" />
                    Scan &amp; Check In
                  </button>
                ) : checkInSource === 'upload' ? (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isMatching}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-xl transition shadow"
                  >
                    <UploadCloud className="w-4 h-4" />
                    Browse Photo File
                  </button>
                ) : (
                  <button
                    onClick={captureStreamAndMatch}
                    disabled={isCapturingStream || isMatching || selectedCameraId === 'manual'}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-bold rounded-xl transition shadow"
                  >
                    {isCapturingStream ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Video className="w-4 h-4" />
                    )}
                    Snapshot &amp; Verify Face
                  </button>
                )
              ) : (
                <button
                  onClick={() => {
                    setMatchResult(null);
                    setMatchError(null);
                    setUploadedPreview(null);
                    if (checkInSource === 'webcam') {
                      startMatchCamera();
                    }
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold rounded-xl transition shadow"
                >
                  <RefreshCw className="w-4 h-4" />
                  Scan Another Worker
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
