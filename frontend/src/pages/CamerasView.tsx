/**
 * CamerasView.tsx — RAKSHYA VISION Professional SOC
 * High-performance Multi-Camera Surveillance Dashboard.
 * Responsive multi-camera grid with real live streams, operational telemetry,
 * dynamic camera addition/removal, fault-isolated cards, and camera-specific AI analysis.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Video,
  Camera,
  Plus,
  RefreshCw,
  LayoutGrid,
  List,
  AlertTriangle,
  Cpu,
  X,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { CameraLiveCard } from '../components/CameraLiveCard';
import { AddCameraModal } from '../components/AddCameraModal';
import {
  fetchCameras,
  deleteCamera,
  reconnectCamera,
  analyzeCameraLive,
  analyzeCameraUpload,
} from '../services/api';

interface CamerasViewProps {
  cameras: CameraConfig[];
  hazardConfig?: any;
  onRefreshCameras?: () => void;
}

type FilterTab = 'all' | 'online' | 'offline' | 'alerts';
type ViewMode = 'grid' | 'list';

export const CamerasView: React.FC<CamerasViewProps> = ({
  cameras: initialCameras,
  hazardConfig: _hazardConfig,
  onRefreshCameras,
}) => {
  const [cameraList, setCameraList] = useState<CameraConfig[]>(initialCameras);
  const [filterTab, setFilterTab] = useState<FilterTab>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // AI Analysis Modal State
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [analysisCameraId, setAnalysisCameraId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const loadCameras = async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchCameras();
      if (Array.isArray(data)) {
        const mapped: CameraConfig[] = data.map((c: any) => ({
          camera_id: c.camera_id,
          name: c.name,
          location: c.location || c.zone_id,
          zone_id: c.zone_id,
          status: c.status || (c.state === 'CONNECTED' ? 'online' : 'offline'),
          connection_status: c.connection_status || c.state?.toLowerCase(),
          state: c.state,
          source: c.source,
          source_type: c.source_type,
          enabled: c.enabled,
          resolution: c.resolution || '1280x720',
          fps: typeof c.fps === 'number' ? c.fps : (c.metrics?.fps || 0),
          stream_url: c.stream_url || `/api/cameras/${c.camera_id}/stream`,
          safe_source: c.safe_source,
          last_seen: c.last_seen,
          metrics: c.metrics,
          ai_analysis: c.ai_analysis,
        }));
        setCameraList(mapped);
      }
      onRefreshCameras?.();
    } catch (err) {
      console.error('Failed to load cameras:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (initialCameras && initialCameras.length > 0) {
      setCameraList(initialCameras);
    } else {
      loadCameras();
    }
  }, [initialCameras]);

  // Operational Dashboard Metrics
  const totalCount = cameraList.length;
  const onlineCount = cameraList.filter(
    (c) => c.status === 'online' || c.status === 'ACTIVE' || c.state === 'CONNECTED'
  ).length;
  const offlineCount = totalCount - onlineCount;
  const totalViolations = cameraList.reduce(
    (acc, c) => acc + (c.metrics?.active_violations ?? 0),
    0
  );

  // Filtered cameras based on active filter tab
  const filteredCameras = useMemo(() => {
    return cameraList.filter((c) => {
      const isOnline =
        c.status === 'online' || c.status === 'ACTIVE' || c.state === 'CONNECTED';
      if (filterTab === 'online') return isOnline;
      if (filterTab === 'offline') return !isOnline;
      if (filterTab === 'alerts') return (c.metrics?.active_violations ?? 0) > 0;
      return true;
    });
  }, [cameraList, filterTab]);

  const handleDeleteCamera = async (cameraId: string) => {
    try {
      await deleteCamera(cameraId);
      await loadCameras();
    } catch (err: any) {
      alert(`Failed to delete camera: ${err.message || 'Unknown error'}`);
    }
  };

  const handleReconnect = async (cameraId: string) => {
    try {
      await reconnectCamera(cameraId);
      await loadCameras();
    } catch (err) {
      console.error(`Reconnect error on ${cameraId}:`, err);
    }
  };

  const handleAnalyzeLive = async (camera: CameraConfig) => {
    setAnalysisCameraId(camera.camera_id);
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const result = await analyzeCameraLive(camera.camera_id);
      setAnalysisResult(result);
    } catch (err: any) {
      setAnalysisError(err.message || 'AI Live Analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleUploadAnalyze = async (camera: CameraConfig, file: File) => {
    setAnalysisCameraId(camera.camera_id);
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const result = await analyzeCameraUpload(camera.camera_id, file);
      setAnalysisResult(result);
    } catch (err: any) {
      setAnalysisError(err.message || 'Frame analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5 bg-[#eef3f9]">
      {/* ─── Top Dashboard Header & Operational Summary ─────────────── */}
      <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-700 text-white flex items-center justify-center shadow-sm shadow-sky-700/20">
              <Video className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                CAMERAS <span className="text-sky-600 font-medium text-xs">Surveillance Matrix</span>
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                Live multi-camera operational monitoring and real-time PPE compliance tracking
              </p>
            </div>
          </div>
        </div>

        {/* Real Summary Metrics Badges */}
        <div className="flex items-center gap-3 self-start md:self-auto flex-wrap">
          <div className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-center">
            <span className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Total
            </span>
            <span className="text-sm font-extrabold text-slate-800 font-mono">
              {totalCount}
            </span>
          </div>

          <div className="bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg text-center">
            <span className="block text-[10px] uppercase font-bold text-emerald-600 tracking-wider">
              Online
            </span>
            <span className="text-sm font-extrabold text-emerald-700 font-mono">
              {onlineCount}
            </span>
          </div>

          <div className="bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-lg text-center">
            <span className="block text-[10px] uppercase font-bold text-rose-500 tracking-wider">
              Offline
            </span>
            <span className="text-sm font-extrabold text-rose-700 font-mono">
              {offlineCount}
            </span>
          </div>

          <div className="bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg text-center">
            <span className="block text-[10px] uppercase font-bold text-amber-600 tracking-wider">
              AI Alerts
            </span>
            <span className="text-sm font-extrabold text-amber-700 font-mono">
              {totalViolations}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Surveillance Controls Toolbar ──────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Filter Buttons */}
        <div className="inline-flex p-1 bg-white border border-slate-200 rounded-lg shadow-sm">
          <button
            onClick={() => setFilterTab('all')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition ${
              filterTab === 'all'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Cameras ({totalCount})
          </button>
          <button
            onClick={() => setFilterTab('online')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
              filterTab === 'online'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Online ({onlineCount})
          </button>
          <button
            onClick={() => setFilterTab('offline')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
              filterTab === 'offline'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            Offline ({offlineCount})
          </button>
          <button
            onClick={() => setFilterTab('alerts')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
              filterTab === 'alerts'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-amber-300" />
            AI Alerts ({totalViolations})
          </button>
        </div>

        {/* View Toggle & Add Camera Button */}
        <div className="flex items-center gap-2">
          {/* Grid vs List View Switch */}
          <div className="inline-flex p-1 bg-white border border-slate-200 rounded-lg shadow-sm">
            <button
              onClick={() => setViewMode('grid')}
              title="Grid View (Default)"
              className={`p-1.5 rounded-md transition ${
                viewMode === 'grid'
                  ? 'bg-slate-100 text-sky-700 font-bold'
                  : 'text-slate-400 hover:text-slate-700'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              title="List View"
              className={`p-1.5 rounded-md transition ${
                viewMode === 'list'
                  ? 'bg-slate-100 text-sky-700 font-bold'
                  : 'text-slate-400 hover:text-slate-700'
            }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={loadCameras}
            disabled={isRefreshing}
            title="Refresh All Camera Streams"
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg shadow-sm text-xs font-bold transition"
          >
            <Plus className="w-4 h-4" />
            Add Camera
          </button>
        </div>
      </div>

      {/* ─── Responsive Multi-Camera Grid ───────────────────────────── */}
      {filteredCameras.length === 0 ? (
        <div className="bg-white rounded-xl p-12 border border-slate-200 text-center flex flex-col items-center justify-center">
          <Camera className="w-12 h-12 text-slate-300 mb-3 stroke-[1.2]" />
          <h3 className="text-sm font-bold text-slate-700">No cameras match current filter</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm">
            {filterTab !== 'all'
              ? `No cameras currently in "${filterTab}" status.`
              : 'No cameras configured in the system. Click "Add Camera" to register your first stream.'}
          </p>
          {filterTab !== 'all' && (
            <button
              onClick={() => setFilterTab('all')}
              className="mt-4 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-bold transition"
            >
              Show All Cameras
            </button>
          )}
        </div>
      ) : viewMode === 'grid' ? (
        /* Desktop: 2 columns default, 3 columns on large screens; Mobile: 1 column */
        <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5">
          {filteredCameras.map((camera) => (
            <CameraLiveCard
              key={camera.camera_id}
              camera={camera}
              onRefresh={handleReconnect}
              onDelete={handleDeleteCamera}
              onAnalyzeLive={handleAnalyzeLive}
              onUploadAnalyze={handleUploadAnalyze}
            />
          ))}
        </div>
      ) : (
        /* List View */
        <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100 shadow-sm overflow-hidden">
          {filteredCameras.map((camera) => {
            const isOnline =
              camera.status === 'online' ||
              camera.status === 'ACTIVE' ||
              camera.state === 'CONNECTED';
            return (
              <div
                key={camera.camera_id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50 transition"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full shrink-0 ${
                      isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                    }`}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-800">
                        {camera.name || camera.camera_id}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">
                        {camera.camera_id}
                      </span>
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                          isOnline
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {isOnline ? 'ONLINE' : 'OFFLINE'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {camera.location || camera.zone_id} • {camera.source_type} •{' '}
                      {camera.resolution} • {camera.fps?.toFixed(1) ?? '0.0'} FPS
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAnalyzeLive(camera)}
                    className="px-3 py-1.5 rounded-lg bg-sky-50 border border-sky-200 hover:bg-sky-100 text-sky-800 text-xs font-bold transition flex items-center gap-1.5"
                  >
                    <Cpu className="w-3.5 h-3.5" /> Analyze Live
                  </button>
                  <button
                    onClick={() => handleReconnect(camera.camera_id)}
                    className="p-2 rounded-lg text-slate-500 hover:text-sky-700 hover:bg-slate-100 border border-slate-200 transition"
                    title="Reconnect"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ─── Add Camera Modal ────────────────────────────────────────── */}
      <AddCameraModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onCameraAdded={loadCameras}
      />

      {/* ─── AI Analysis Results Modal ──────────────────────────────── */}
      {(analysisResult || isAnalyzing || analysisError) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="px-5 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-800">
                    AI Frame Analysis — {analysisCameraId}
                  </h2>
                  <p className="text-[11px] text-slate-500">
                    YOLO Worker Detection &amp; PPE Compliance Association
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setAnalysisResult(null);
                  setAnalysisError(null);
                  setIsAnalyzing(false);
                }}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {isAnalyzing && (
                <div className="p-12 flex flex-col items-center justify-center text-slate-500">
                  <RefreshCw className="w-8 h-8 animate-spin text-sky-600 mb-3" />
                  <p className="font-semibold text-slate-700">Running AI inference on live frame...</p>
                  <p className="text-[11px] text-slate-400 mt-1">Executing YOLO model and ByteTrack tracking</p>
                </div>
              )}

              {analysisError && (
                <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2.5">
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}

              {analysisResult && (
                <>
                  {/* Annotated Image Viewport */}
                  {analysisResult.annotated_image_base64 && (
                    <div className="rounded-lg overflow-hidden border border-slate-200 bg-slate-950 aspect-video relative flex items-center justify-center">
                      <img
                        src={analysisResult.annotated_image_base64}
                        alt="AI Detection Output"
                        className="w-full h-full object-contain"
                      />
                    </div>
                  )}

                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                      <span className="block text-[10px] text-slate-400 font-bold uppercase">
                        Tracked Workers
                      </span>
                      <span className="text-sm font-extrabold text-slate-800 font-mono">
                        {analysisResult.summary?.total_workers ?? analysisResult.workers?.length ?? 0}
                      </span>
                    </div>

                    <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                      <span className="block text-[10px] text-emerald-600 font-bold uppercase">
                        Compliant
                      </span>
                      <span className="text-sm font-extrabold text-emerald-700 font-mono">
                        {analysisResult.summary?.compliant_workers ?? 0}
                      </span>
                    </div>

                    <div className="p-2.5 bg-rose-50 rounded-lg border border-rose-200">
                      <span className="block text-[10px] text-rose-600 font-bold uppercase">
                        Violations
                      </span>
                      <span className="text-sm font-extrabold text-rose-700 font-mono">
                        {analysisResult.summary?.non_compliant_workers ?? 0}
                      </span>
                    </div>
                  </div>

                  {/* Worker Breakdown Table */}
                  {analysisResult.workers && analysisResult.workers.length > 0 && (
                    <div className="border border-slate-200 rounded-lg overflow-hidden">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-[10px] text-slate-500 font-bold uppercase">
                            <th className="py-2 px-3">Track ID</th>
                            <th className="py-2 px-3">Status</th>
                            <th className="py-2 px-3">Helmet</th>
                            <th className="py-2 px-3">Vest</th>
                            <th className="py-2 px-3">Gloves</th>
                            <th className="py-2 px-3">Footwear</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-[11px]">
                          {analysisResult.workers.map((w: any) => (
                            <tr key={w.track_id} className="hover:bg-slate-50">
                              <td className="py-2 px-3 font-mono font-bold text-slate-800">
                                #{w.track_id}
                              </td>
                              <td className="py-2 px-3">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                    w.overall_compliant
                                      ? 'bg-emerald-50 text-emerald-700'
                                      : 'bg-rose-50 text-rose-700'
                                  }`}
                                >
                                  {w.overall_compliant ? 'COMPLIANT' : 'VIOLATION'}
                                </span>
                              </td>
                              <td className="py-2 px-3 font-mono">
                                {w.ppe_status?.helmet === 'PRESENT' ? '✅' : '❌'}
                              </td>
                              <td className="py-2 px-3 font-mono">
                                {w.ppe_status?.safety_vest === 'PRESENT' ? '✅' : '❌'}
                              </td>
                              <td className="py-2 px-3 font-mono">
                                {w.ppe_status?.gloves === 'PRESENT' ? '✅' : '❌'}
                              </td>
                              <td className="py-2 px-3 font-mono">
                                {w.ppe_status?.safety_footwear === 'PRESENT' ? '✅' : '❌'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => {
                  setAnalysisResult(null);
                  setAnalysisError(null);
                  setIsAnalyzing(false);
                }}
                className="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold rounded-md transition text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
