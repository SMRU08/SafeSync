/**
 * CamerasView.tsx — SafeSync Phase 6: Cameras + Multi-Camera + Camera Coverage
 * Premier Mission-Critical Multi-Camera Surveillance & Optical Coverage Command Center.
 *
 * Implements:
 *   - Clean Industrial Safety SOC Design (#07111F, #0D1B2A, #12263A, #20344A)
 *   - Operational KPI Ribbon (Total, Online, Offline, AI Alerts, Environmental Hazards)
 *   - Category Switcher:
 *       • [ Surveillance Matrix ]  (High-performance live multi-camera monitoring)
 *       • [ Coverage & Visibility ] (Optical suitability, geometry explanation, and coverage table)
 *       • [ Entry Gate ]           (Turnstile pre-entry PPE access decision workflow)
 *   - Purpose-Aware Multi-Camera Filter Tabs & Search
 *   - CameraLiveCard Grid & List ledger modes with dedicated [ OPEN LIVE VIEW ] triggers
 *   - Full CameraDetailModal with real-time ByteTrack bounding boxes and safety diagnostics
 *   - Zero fake telemetry, zero fake workers, zero fake percentages
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Video,
  Camera,
  Plus,
  RefreshCw,
  LayoutGrid,
  List,
  DoorOpen,
  Search,
  Eye,
  Settings,
} from 'lucide-react';
import { CameraConfig } from '../types';
import { CameraLiveCard } from '../components/CameraLiveCard';
import { AddCameraModal } from '../components/AddCameraModal';
import { EntryGateView } from '../components/EntryGateView';
import { CameraCoverageSection, getCameraPurpose } from '../components/CameraCoverageSection';
import { CameraDetailModal } from '../components/CameraDetailModal';
import {
  fetchCameras,
  deleteCamera,
  reconnectCamera,
  startCamera,
  stopCamera,
  toggleCameraSpeaker,
} from '../services/api';
import { EmptyState } from '../components/ui/EmptyState';

interface CamerasViewProps {
  cameras: CameraConfig[];
  hazardConfig?: any;
  onRefreshCameras?: () => void;
  onToggleSpeaker?: (cameraId: string, enabled: boolean) => void;
  initialSubTab?: 'matrix' | 'entry_gate' | 'coverage';
  onSubTabChange?: (subTab: 'matrix' | 'entry_gate') => void;
}

type FilterTab =
  | 'all'
  | 'online'
  | 'offline'
  | 'entry_gate'
  | 'production_floor'
  | 'hazard_zone'
  | 'general'
  | 'violations'
  | 'fire_smoke';

type ViewMode = 'grid' | 'list';

export const CamerasView: React.FC<CamerasViewProps> = ({
  cameras: initialCameras,
  hazardConfig: _hazardConfig,
  onRefreshCameras,
  onToggleSpeaker,
  initialSubTab = 'matrix',
  onSubTabChange,
}) => {
  const [cameraList, setCameraList] = useState<CameraConfig[]>(initialCameras);
  const [activeCategory, setActiveCategory] = useState<'matrix' | 'entry_gate' | 'coverage'>(
    initialSubTab === 'entry_gate' ? 'entry_gate' : 'matrix'
  );

  useEffect(() => {
    if (initialSubTab) {
      if (initialSubTab === 'entry_gate') setActiveCategory('entry_gate');
      else if (initialSubTab === 'matrix') setActiveCategory('matrix');
    }
  }, [initialSubTab]);

  const handleCategorySwitch = (cat: 'matrix' | 'entry_gate' | 'coverage') => {
    setActiveCategory(cat);
    if (cat === 'entry_gate') onSubTabChange?.('entry_gate');
    else onSubTabChange?.('matrix');
  };

  const [filterTab, setFilterTab] = useState<FilterTab>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  // Modals state
  const [editingCamera, setEditingCamera] = useState<CameraConfig | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedDetailCamera, setSelectedDetailCamera] = useState<CameraConfig | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

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
          last_attempt: c.last_attempt || c.metrics?.last_attempt,
          last_error: c.last_error || c.metrics?.last_error,
          retry_count: c.retry_count ?? c.metrics?.retry_count ?? 0,
          metrics: c.metrics,
          ai_analysis: c.ai_analysis,
          speaker_enabled: c.speaker_enabled,
        }));
        setCameraList(mapped);

        // Update selected detail camera if open
        if (selectedDetailCamera) {
          const updated = mapped.find((m) => m.camera_id === selectedDetailCamera.camera_id);
          if (updated) setSelectedDetailCamera(updated);
        }
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

  // Operational Dashboard Metrics (Real values only)
  const totalCount = cameraList.length;
  const onlineCount = cameraList.filter(
    (c) =>
      c.enabled !== false &&
      (c.status === 'online' || c.status === 'ACTIVE' || c.status === 'streaming' || c.state === 'CONNECTED')
  ).length;
  const offlineCount = totalCount - onlineCount;
  const totalViolations = cameraList.reduce(
    (acc, c) => acc + (c.metrics?.active_violations ?? 0),
    0
  );
  const totalHazards = cameraList.reduce(
    (acc, c) => acc + (c.metrics?.active_hazards ?? 0),
    0
  );

  // Filtered cameras based on filter tab and search query
  const filteredCameras = useMemo(() => {
    return cameraList.filter((c) => {
      const isOnline =
        c.enabled !== false &&
        (c.status === 'online' || c.status === 'ACTIVE' || c.status === 'streaming' || c.state === 'CONNECTED');
      const purpose = getCameraPurpose(c);

      // Filter Tab Check
      if (filterTab === 'online' && !isOnline) return false;
      if (filterTab === 'offline' && isOnline) return false;
      if (filterTab === 'entry_gate' && purpose !== 'ENTRY GATE') return false;
      if (filterTab === 'production_floor' && purpose !== 'PRODUCTION FLOOR') return false;
      if (filterTab === 'hazard_zone' && purpose !== 'HAZARD ZONE') return false;
      if (filterTab === 'general' && purpose !== 'GENERAL MONITORING') return false;
      if (filterTab === 'violations' && (c.metrics?.active_violations ?? 0) === 0) return false;
      if (filterTab === 'fire_smoke' && (c.metrics?.active_hazards ?? 0) === 0) return false;

      // Search Query Check (by Camera Name, Camera ID, Location/Zone)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = (c.name || '').toLowerCase().includes(q);
        const matchesId = c.camera_id.toLowerCase().includes(q);
        const matchesLoc = (c.location || '').toLowerCase().includes(q);
        const matchesZone = (c.zone_id || '').toLowerCase().includes(q);
        if (!matchesName && !matchesId && !matchesLoc && !matchesZone) return false;
      }

      return true;
    });
  }, [cameraList, filterTab, searchQuery]);

  const handleToggleSpeaker = async (cameraId: string, enabled: boolean) => {
    if (onToggleSpeaker) {
      onToggleSpeaker(cameraId, enabled);
    } else {
      try {
        await toggleCameraSpeaker(cameraId, enabled);
      } catch {
        // tolerate dropouts
      }
    }
    setCameraList((prev) =>
      prev.map((c) => (c.camera_id === cameraId ? { ...c, speaker_enabled: enabled } : c))
    );
  };

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

  const handleToggleStartStop = async (cameraId: string, start: boolean) => {
    try {
      setCameraList((prev) =>
        prev.map((c) =>
          c.camera_id === cameraId
            ? {
                ...c,
                enabled: start,
                status: start ? 'connecting' : 'offline',
              }
            : c
        )
      );

      if (start) {
        await startCamera(cameraId);
      } else {
        await stopCamera(cameraId);
      }
      await loadCameras();
    } catch (err: any) {
      console.error(`Failed to ${start ? 'start' : 'stop'} camera ${cameraId}:`, err);
      await loadCameras();
    }
  };

  // If active category is Entry Gate, render dedicated workflow
  if (activeCategory === 'entry_gate') {
    return (
      <EntryGateView
        cameras={cameraList}
        onRefreshCameras={loadCameras}
        onBackToMatrix={() => handleCategorySwitch('matrix')}
      />
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5 bg-[#07111F] text-[#E8F0F7] select-none">
      {/* ─── Top Dashboard Header & SOC Telemetry Bar ───────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#20344A]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-white tracking-tight">
                  SURVEILLANCE CAMERAS
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-sky-400 border border-slate-700 font-bold uppercase">
                  Multi-Camera Matrix
                </span>
              </div>
              <p className="text-xs text-[#8FA3B8] mt-0.5">
                Central industrial camera management, real-time live video streams, and optical coverage auditing
              </p>
            </div>
          </div>
        </div>

        {/* View Mode Category Switcher (Matrix vs Coverage vs Entry Gate) */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto flex-wrap">
          <div className="flex items-center p-1 bg-[#0D1B2A] rounded-xl border border-[#20344A]">
            <button
              onClick={() => handleCategorySwitch('matrix')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                activeCategory === 'matrix'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Surveillance Matrix</span>
            </button>
            <button
              onClick={() => handleCategorySwitch('coverage')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                activeCategory === 'coverage'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Coverage &amp; Visibility</span>
            </button>
            <button
              onClick={() => handleCategorySwitch('entry_gate')}
              className="px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer text-slate-400 hover:text-emerald-400"
            >
              <DoorOpen className="w-3.5 h-3.5 text-emerald-400" />
              <span>Entry Gate</span>
            </button>
          </div>

          <button
            onClick={() => {
              setEditingCamera(null);
              setIsAddModalOpen(true);
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl shadow-sm text-xs font-bold transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Add Camera
          </button>
        </div>
      </div>

      {/* ─── Operational Summary KPI Ribbon (Section 4 & 22) ────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <span className="text-[10px] font-bold text-[#8FA3B8] uppercase tracking-wider block">
            Total Nodes
          </span>
          <span className="text-xl font-black text-white font-mono mt-1 block">
            {totalCount}
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Configured</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">
            Online Feeds
          </span>
          <span className="text-xl font-black text-emerald-400 font-mono mt-1 block">
            {onlineCount}
          </span>
          <span className="text-[10px] text-emerald-500 font-mono mt-0.5 block">Active Streaming</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block">
            Offline / Error
          </span>
          <span className="text-xl font-black text-rose-400 font-mono mt-1 block">
            {offlineCount}
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Check Source</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
            AI Violations
          </span>
          <span className="text-xl font-black text-[#F5B942] font-mono mt-1 block">
            {totalViolations}
          </span>
          <span className="text-[10px] text-amber-500 font-mono mt-0.5 block">Active Alerts</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Fire / Smoke
          </span>
          <span
            className={`text-xl font-black font-mono mt-1 block ${
              totalHazards > 0 ? 'text-rose-400 animate-pulse' : 'text-slate-300'
            }`}
          >
            {totalHazards > 0 ? 'ALERT' : 'CLEAR'}
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">P0 Emergency Layer</span>
        </div>
      </div>

      {/* ─── Conditional Content: Coverage vs Matrix View ───────────────── */}
      {activeCategory === 'coverage' ? (
        <CameraCoverageSection
          cameras={cameraList}
          onOpenLiveView={(cam) => setSelectedDetailCamera(cam)}
          onLaunchEntryGate={() => handleCategorySwitch('entry_gate')}
        />
      ) : (
        <>
          {/* ─── Surveillance Controls & Filter Toolbar (Section 14 & 15) ─── */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-1">
            {/* Multi-Camera Filter Tabs */}
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0D1B2A] border border-[#20344A] text-xs overflow-x-auto">
              {(
                [
                  { id: 'all', label: 'All Feeds', count: totalCount },
                  { id: 'online', label: 'Online', count: onlineCount },
                  { id: 'offline', label: 'Offline', count: offlineCount },
                  { id: 'entry_gate', label: 'Entry Gate', count: cameraList.filter((c) => getCameraPurpose(c) === 'ENTRY GATE').length },
                  { id: 'production_floor', label: 'Floor', count: cameraList.filter((c) => getCameraPurpose(c) === 'PRODUCTION FLOOR').length },
                  { id: 'hazard_zone', label: 'Hazard', count: cameraList.filter((c) => getCameraPurpose(c) === 'HAZARD ZONE').length },
                  { id: 'violations', label: 'Violations', count: cameraList.filter((c) => (c.metrics?.active_violations ?? 0) > 0).length },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setFilterTab(tab.id)}
                  className={`px-3 py-1 font-bold rounded-lg transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                    filterTab === tab.id
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <span>{tab.label}</span>
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-black/30">
                    {tab.count}
                  </span>
                </button>
              ))}
            </div>

            {/* Search Input, View Mode, and Refresh */}
            <div className="flex items-center gap-2.5 flex-wrap">
              {/* Search Bar (Section 15) */}
              <div className="relative w-48 sm:w-56">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search Camera, Zone..."
                  className="w-full bg-[#0D1B2A] border border-[#20344A] rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Grid vs List View */}
              <div className="flex items-center gap-1 p-1 rounded-lg bg-[#0D1B2A] border border-[#20344A]">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded-md transition cursor-pointer ${
                    viewMode === 'grid' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                  title="Grid Matrix"
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded-md transition cursor-pointer ${
                    viewMode === 'list' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                  title="List Ledger"
                >
                  <List className="w-3.5 h-3.5" />
                </button>
              </div>

              <button
                onClick={loadCameras}
                disabled={isRefreshing}
                className="p-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-slate-300 hover:text-white hover:border-slate-600 transition cursor-pointer"
                title="Refresh Camera Matrix"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`} />
              </button>
            </div>
          </div>

          {/* ─── Surveillance Grid / List Surface (Section 4 & 13) ─────────── */}
          {filteredCameras.length === 0 ? (
            <EmptyState
              icon={Camera}
              title={totalCount === 0 ? 'NO CAMERAS CONFIGURED' : 'NO CAMERAS MATCH THIS FILTER'}
              description={
                totalCount === 0
                  ? 'Add your first surveillance camera stream (USB Webcam, IP Camera, RTSP) to begin automated PPE and hazard monitoring.'
                  : 'No surveillance camera feeds currently match the selected filter criteria or search query.'
              }
            />
          ) : viewMode === 'grid' ? (
            /* Responsive 2-column (tablet) to 3-column (desktop) Matrix */
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {filteredCameras.map((camera) => (
                <CameraLiveCard
                  key={camera.camera_id}
                  camera={camera}
                  onRefresh={handleReconnect}
                  onDelete={handleDeleteCamera}
                  onOpenLiveView={(cam) => setSelectedDetailCamera(cam)}
                  onToggleSpeaker={handleToggleSpeaker}
                  onToggleStartStop={handleToggleStartStop}
                  onEdit={(cam) => {
                    setEditingCamera(cam);
                    setIsAddModalOpen(true);
                  }}
                />
              ))}
            </div>
          ) : (
            /* Table Ledger Mode (Section 26) */
            <div className="rounded-xl border border-[#20344A] bg-[#0D1B2A] overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#12263A] border-b border-[#20344A] text-slate-400 font-bold text-[10px] uppercase tracking-wider">
                      <th className="py-3 px-4">Camera Node</th>
                      <th className="py-3 px-4">Operational Purpose</th>
                      <th className="py-3 px-4">Source Type</th>
                      <th className="py-3 px-4">Resolution</th>
                      <th className="py-3 px-4">Live FPS</th>
                      <th className="py-3 px-4">Workers</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#20344A]/60">
                    {filteredCameras.map((camera) => {
                      const isEnabled = camera.enabled !== false;
                      const isOnline =
                        isEnabled &&
                        (camera.status === 'online' ||
                          camera.status === 'ACTIVE' ||
                          camera.status === 'streaming' ||
                          camera.state === 'CONNECTED');
                      const purpose = getCameraPurpose(camera);

                      return (
                        <tr
                          key={camera.camera_id}
                          className="hover:bg-[#12263A]/80 transition cursor-pointer"
                          onClick={() => setSelectedDetailCamera(camera)}
                        >
                          <td className="py-3 px-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Camera className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                              <div>
                                <span className="font-bold text-white text-xs block">
                                  {camera.name || camera.camera_id}
                                </span>
                                <span className="font-mono text-[10px] text-slate-400 uppercase">
                                  {camera.camera_id}
                                </span>
                              </div>
                            </div>
                          </td>

                          <td className="py-3 px-4 whitespace-nowrap">
                            <span className="text-slate-300 font-semibold">{purpose}</span>
                          </td>

                          <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                            {camera.source_type?.toUpperCase() || 'USB'}
                          </td>

                          <td className="py-3 px-4 font-mono text-slate-300 whitespace-nowrap">
                            {camera.resolution || '1280x720'}
                          </td>

                          <td className="py-3 px-4 font-mono font-bold text-emerald-400 whitespace-nowrap">
                            {camera.metrics?.fps != null && camera.metrics.fps > 0
                              ? camera.metrics.fps.toFixed(1)
                              : camera.fps > 0
                              ? camera.fps.toFixed(1)
                              : '—'}
                          </td>

                          <td className="py-3 px-4 font-mono text-slate-200 whitespace-nowrap">
                            {camera.metrics?.active_workers ?? '—'}
                          </td>

                          <td className="py-3 px-4 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                                !isEnabled
                                  ? 'bg-slate-700/60 text-slate-400 border-slate-600'
                                  : isOnline
                                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                                  : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                              }`}
                            >
                              {!isEnabled ? 'STOPPED' : isOnline ? 'ONLINE' : 'OFFLINE'}
                            </span>
                          </td>

                          <td className="py-3 px-4 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedDetailCamera(camera);
                                }}
                                className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-[11px] font-bold transition inline-flex items-center gap-1 cursor-pointer"
                              >
                                <Eye className="w-3 h-3" /> Live View
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setEditingCamera(camera);
                                  setIsAddModalOpen(true);
                                }}
                                className="p-1 rounded bg-[#12263A] hover:bg-slate-700 text-slate-300 border border-[#20344A] transition cursor-pointer"
                                title="Configure Source"
                              >
                                <Settings className="w-3 h-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ─── Add / Edit Camera Modal (Section 16–19) ────────────────────── */}
      <AddCameraModal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false);
          setEditingCamera(null);
        }}
        onCameraAdded={loadCameras}
        editCamera={editingCamera}
      />

      {/* ─── Detailed Live Camera Inspector Modal (Section 6, 7, 8, 9, 20) ─ */}
      <CameraDetailModal
        camera={selectedDetailCamera}
        isOpen={Boolean(selectedDetailCamera)}
        onClose={() => setSelectedDetailCamera(null)}
        onReconnect={handleReconnect}
        onEdit={(cam) => {
          setSelectedDetailCamera(null);
          setEditingCamera(cam);
          setIsAddModalOpen(true);
        }}
        onToggleSpeaker={handleToggleSpeaker}
        onLaunchEntryGate={() => {
          setSelectedDetailCamera(null);
          handleCategorySwitch('entry_gate');
        }}
      />
    </div>
  );
};

export default CamerasView;
