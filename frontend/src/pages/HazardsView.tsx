/**
 * HazardsView.tsx — SafeSync BPUT Hackathon 2026 Phase 7
 * Emergency Fire & Smoke Hazard Monitoring Center.
 * Decoupled combustion flame and smoke plume atmospheric analysis.
 * Real backend camera ingestion, real temporal hazard events, zero fabricated emergencies.
 */

import React, { useState } from 'react';
import {
  Flame,
  CloudRain,
  ShieldAlert,
  Upload,
  Activity,
  CheckCircle2,
  MapPin,
  Radio,
  Video,
  Clock,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { HazardEventDetail } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface HazardsViewProps {
  hazards: HazardEventDetail[];
  hazardConfig?: any;
  cameras?: any[];
  onNavigate?: (tab: any, opts?: any) => void;
  onSelectIncident?: (incidentId: string) => void;
  onRefresh?: () => void;
  isBackendHealthy?: boolean;
}

export const HazardsView: React.FC<HazardsViewProps> = ({
  hazards,
  hazardConfig: _hazardConfig,
  cameras = [],
  onNavigate,
  onSelectIncident,
  onRefresh,
  isBackendHealthy = true,
}) => {
  const [analyzedHazards, setAnalyzedHazards] = useState<HazardEventDetail[]>(hazards);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [sceneState, setSceneState] = useState<string | null>(null);
  const [relationship, setRelationship] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleHazardFrameUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAnalyzing(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('camera_id', cameras[0]?.camera_id || 'camera_01');
    formData.append('zone_id', cameras[0]?.zone || 'production_floor');

    try {
      const response = await fetch(`${API_BASE_URL}/api/hazards/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Inference returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setSceneState(data.scene_hazard_state);
      setRelationship(data.relationship);
      setAnalyzedHazards(data.hazards || []);
      if (data.annotated_image_base64) {
        setAnnotatedImage(`data:image/jpeg;base64,${data.annotated_image_base64}`);
      }
    } catch (err: any) {
      setErrorMsg(`Hazard analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const activeHazardsList = analyzedHazards.length > 0 ? analyzedHazards : hazards;

  const confirmedHazards = activeHazardsList.filter(
    (h) => h.state === 'CONFIRMED' || h.state === 'ACTIVE'
  );
  const candidateHazards = activeHazardsList.filter(
    (h) => h.state === 'CANDIDATE' || h.state === 'DETECTING'
  );

  const confirmedFire = confirmedHazards.find((h) => h.hazard_type?.toLowerCase() === 'fire');
  const confirmedSmoke = confirmedHazards.find((h) => h.hazard_type?.toLowerCase() === 'smoke');

  const topEmergency = confirmedFire || confirmedSmoke;
  const hasConfirmedHazard = confirmedHazards.length > 0;

  // Active emergencies count (real count only)
  const activeEmergenciesCount = confirmedHazards.length;

  // Monitored cameras count (real count only)
  const monitoredCamerasCount = cameras.length > 0 ? cameras.length : 0;

  const getStateBadge = (state: string, hazardType?: string) => {
    switch (state.toUpperCase()) {
      case 'ACTIVE':
      case 'CONFIRMED':
      case 'DETECTED':
        return hazardType === 'fire'
          ? 'text-[#FF5A36] bg-[#FF5A36]/15 border-[#FF5A36]/50'
          : 'text-[#F59E0B] bg-[#F59E0B]/15 border-[#F59E0B]/50';
      case 'DETECTING':
      case 'CANDIDATE':
      case 'EVALUATING':
        return 'text-[#F5B942] bg-amber-500/15 border-amber-500/40 animate-pulse';
      case 'CLEARING':
        return 'text-slate-400 bg-slate-800 border-slate-700';
      case 'CLEAR':
      default:
        return 'text-[#22C55E] bg-emerald-500/15 border-emerald-500/30';
    }
  };

  // Find camera location helper
  const getCameraLocation = (camId?: string) => {
    if (!camId) return 'Industrial Plant Zone';
    const match = cameras.find((c) => c.camera_id === camId || c.id === camId);
    return match?.location || match?.zone || 'Production Zone';
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#07111F] text-[#E8F0F7] select-none">
      {/* ─── Header: Fire & Smoke Title & AI Frame Test ─────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#20344A]">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#FF5A36]/15 border border-[#FF5A36]/30 text-[#FF5A36]">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-black text-white tracking-tight">
                  FIRE &amp; SMOKE
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-semibold">
                  Dual-Thermal Active
                </span>
                {!isBackendHealthy && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-400 font-bold">
                    Backend Disconnected
                  </span>
                )}
              </div>
              <p className="text-xs text-[#8FA3B8] mt-0.5">
                Emergency hazard monitoring across connected cameras.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-3 py-1.5 rounded-lg bg-[#0D1B2A] border border-[#20344A] text-xs font-semibold text-[#8FA3B8] hover:text-white transition flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5 text-[#2388FF]" />
              <span>Refresh</span>
            </button>
          )}

          {/* Test Inference Frame Upload */}
          <label className="px-3.5 py-1.5 rounded-lg bg-[#2388FF] hover:bg-[#2388FF]/90 text-white text-xs font-semibold flex items-center gap-2 transition cursor-pointer shadow-sm">
            <Upload className="w-3.5 h-3.5" />
            <span>{isAnalyzing ? 'Analyzing Frame...' : 'Test AI Inference on Frame'}</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleHazardFrameUpload}
              disabled={isAnalyzing}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      {/* ─── Backend Offline Warning Banner (Section 39 & 40) ────────────────── */}
      {!isBackendHealthy && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            <div>
              <span className="font-bold">SafeSync monitoring backend unavailable.</span> Live emergency status cannot be confirmed.
            </div>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* ─── Top Summary Ribbon (Section 6, 7, 8) ───────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* 1. Fire Status Card */}
        <div className={`p-4 rounded-xl border transition-all ${
          confirmedFire
            ? 'bg-[#FF5A36]/15 border-[#FF5A36]/60 shadow-lg shadow-[#FF5A36]/20'
            : 'bg-[#0D1B2A] border-[#20344A]'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8FA3B8]">
              FIRE
            </span>
            <Flame className={`w-4 h-4 ${confirmedFire ? 'text-[#FF5A36] animate-pulse' : 'text-[#8FA3B8]'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-xl font-black font-mono tracking-tight ${
              confirmedFire ? 'text-[#FF5A36]' : 'text-[#22C55E]'
            }`}>
              {confirmedFire ? 'DETECTED' : 'CLEAR'}
            </span>
          </div>
          <p className="text-[10px] text-[#8FA3B8] mt-1">
            {confirmedFire
              ? `Thermal anomaly confirmed on ${confirmedFire.camera_id}`
              : 'Zero combustion signatures detected'}
          </p>
        </div>

        {/* 2. Smoke Status Card */}
        <div className={`p-4 rounded-xl border transition-all ${
          confirmedSmoke
            ? 'bg-[#F59E0B]/15 border-[#F59E0B]/60 shadow-lg shadow-[#F59E0B]/20'
            : 'bg-[#0D1B2A] border-[#20344A]'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8FA3B8]">
              SMOKE
            </span>
            <CloudRain className={`w-4 h-4 ${confirmedSmoke ? 'text-[#F59E0B] animate-pulse' : 'text-[#8FA3B8]'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-xl font-black font-mono tracking-tight ${
              confirmedSmoke ? 'text-[#F59E0B]' : 'text-[#22C55E]'
            }`}>
              {confirmedSmoke ? 'DETECTED' : 'CLEAR'}
            </span>
          </div>
          <p className="text-[10px] text-[#8FA3B8] mt-1">
            {confirmedSmoke
              ? `Atmospheric plume confirmed on ${confirmedSmoke.camera_id}`
              : 'Atmospheric density nominal'}
          </p>
        </div>

        {/* 3. Active Emergencies (Real count only) */}
        <div className={`p-4 rounded-xl border ${
          activeEmergenciesCount > 0
            ? 'bg-rose-500/10 border-rose-500/40'
            : 'bg-[#0D1B2A] border-[#20344A]'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8FA3B8]">
              ACTIVE EMERGENCIES
            </span>
            <Radio className={`w-4 h-4 ${activeEmergenciesCount > 0 ? 'text-[#FF5A36] animate-pulse' : 'text-[#8FA3B8]'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-black font-mono ${
              activeEmergenciesCount > 0 ? 'text-[#FF5A36]' : 'text-white'
            }`}>
              {activeEmergenciesCount}
            </span>
            <span className="text-[11px] text-[#8FA3B8]">
              {activeEmergenciesCount === 1 ? 'Incident' : 'Incidents'}
            </span>
          </div>
          <p className="text-[10px] text-[#8FA3B8] mt-1">
            P0 fire &amp; smoke events requiring containment
          </p>
        </div>

        {/* 4. Monitored Cameras (Real count only) */}
        <div className="p-4 rounded-xl bg-[#0D1B2A] border border-[#20344A]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8FA3B8]">
              MONITORED CAMERAS
            </span>
            <Video className="w-4 h-4 text-[#2388FF]" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black font-mono text-white">
              {monitoredCamerasCount}
            </span>
            <span className="text-[11px] text-[#8FA3B8]">Connected</span>
          </div>
          <p className="text-[10px] text-[#8FA3B8] mt-1">
            Active real-time dual-thermal ingestion feeds
          </p>
        </div>
      </div>

      {/* ─── Prominent Emergency Banner (Section 9) ─────────────────────────── */}
      {hasConfirmedHazard && topEmergency && (
        <div className="p-4 sm:p-5 rounded-2xl bg-[#FF5A36]/20 border-2 border-[#FF5A36] text-white flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl shadow-[#FF5A36]/20">
          <div className="flex items-start sm:items-center gap-3.5">
            <div className="p-3 rounded-xl bg-[#FF5A36] text-white shadow-lg shrink-0">
              <Flame className="w-6 h-6 animate-bounce" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-black uppercase tracking-wider text-white bg-[#FF5A36] px-2 py-0.5 rounded-full">
                  ⚠ FIRE/SMOKE EMERGENCY
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-black/40 border border-white/20 text-[#FF5A36] font-bold">
                  Priority: P0
                </span>
              </div>
              <h3 className="text-base font-black text-white mt-1">
                {topEmergency.hazard_type?.toUpperCase()} DETECTED — {topEmergency.camera_id?.toUpperCase()}
              </h3>
              <p className="text-xs text-slate-200 mt-0.5">
                Camera: <strong className="font-mono text-white">{topEmergency.camera_id}</strong>
                {' • '}
                Location: <strong className="text-white">{getCameraLocation(topEmergency.camera_id)}</strong>
                {' • '}
                Detected: <strong className="text-[#FF5A36]">{topEmergency.hazard_type?.toUpperCase()}</strong>
                {' • '}
                Confidence: <strong>{(topEmergency.confidence * 100).toFixed(1)}%</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
            {onNavigate && (
              <button
                onClick={() => onNavigate('live-monitor')}
                className="px-4 py-2 rounded-xl bg-white hover:bg-slate-200 text-slate-950 font-black text-xs transition shadow-md cursor-pointer flex items-center gap-1.5"
              >
                <Video className="w-3.5 h-3.5 text-[#FF5A36]" />
                OPEN LIVE VIEW
              </button>
            )}

            {onSelectIncident && topEmergency.event_id && (
              <button
                onClick={() => onSelectIncident(topEmergency.event_id!)}
                className="px-4 py-2 rounded-xl bg-black/50 hover:bg-black/75 border border-white/30 text-white font-bold text-xs transition cursor-pointer flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                VIEW INCIDENT
              </button>
            )}
          </div>
        </div>
      )}

      {/* Evaluating Candidate Notice */}
      {!hasConfirmedHazard && candidateHazards.length > 0 && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2.5">
            <Activity className="w-4 h-4 text-[#F59E0B] animate-pulse" />
            <span>
              <strong>Evaluating Potential Hazard:</strong> {candidateHazards.length} candidate signature(s) undergoing multi-frame temporal confirmation.
            </span>
          </div>
          <span className="text-[10px] font-mono text-amber-400 font-semibold">
            Temporal Validation Filter Active
          </span>
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Spatial Relationship Banner (from test inference) */}
      {relationship && (
        <div className="p-3.5 rounded-xl bg-[#0D1B2A] border border-[#20344A] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <Activity className="w-4 h-4 text-[#2388FF]" />
            <span>Scene State: <strong className="text-white font-mono">{sceneState}</strong></span>
          </div>
          <div className="text-[#8FA3B8]">
            Spatial Interaction: <strong className="text-amber-400">{relationship}</strong>
          </div>
        </div>
      )}

      {/* Annotated Frame Viewer (from test inference) */}
      {annotatedImage && (
        <div className="p-4 rounded-2xl bg-[#0D1B2A] border border-[#20344A] space-y-2">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#2388FF]" />
            Annotated Inference Frame Result
          </h3>
          <div className="aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center max-h-[400px]">
            <img src={annotatedImage} alt="Hazard Inference Result" className="w-full h-full object-contain" />
          </div>
        </div>
      )}

      {/* ─── Monitored Cameras Grid (Section 10) ────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Video className="w-4 h-4 text-[#2388FF]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Monitored Camera Sensor Feeds
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[#8FA3B8]">
            {cameras.length} Active Ingestion Feeds
          </span>
        </div>

        {cameras.length === 0 ? (
          <div className="p-8 rounded-2xl bg-[#0D1B2A] border border-[#20344A] text-center text-[#8FA3B8]">
            <Video className="w-8 h-8 text-[#8FA3B8]/60 mx-auto mb-2" />
            <p className="text-xs font-semibold text-white">No Connected Cameras Configured</p>
            <p className="text-[11px] text-[#8FA3B8] mt-1">
              Add a camera in the Cameras view to enable automated fire and smoke detection.
            </p>
            {onNavigate && (
              <button
                onClick={() => onNavigate('cameras')}
                className="mt-3 px-3 py-1.5 rounded-lg bg-[#2388FF] text-white text-xs font-bold hover:bg-[#2388FF]/90 transition"
              >
                Go to Cameras
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {cameras.map((cam) => {
              const camId = cam.camera_id || cam.id;
              const camName = cam.name || camId;
              const camLocation = cam.location || cam.zone || 'Industrial Floor';

              // Filter hazards specifically matching this camera
              const camHazards = activeHazardsList.filter(
                (h) => (h.camera_id && h.camera_id.toLowerCase() === camId?.toLowerCase())
              );

              const fireHazard = camHazards.find((h) => h.hazard_type?.toLowerCase() === 'fire');
              const smokeHazard = camHazards.find((h) => h.hazard_type?.toLowerCase() === 'smoke');

              const fireState = fireHazard
                ? (fireHazard.state === 'CONFIRMED' || fireHazard.state === 'ACTIVE' ? 'DETECTED' : fireHazard.state === 'CANDIDATE' || fireHazard.state === 'DETECTING' ? 'EVALUATING' : fireHazard.state)
                : 'CLEAR';

              const smokeState = smokeHazard
                ? (smokeHazard.state === 'CONFIRMED' || smokeHazard.state === 'ACTIVE' ? 'DETECTED' : smokeHazard.state === 'CANDIDATE' || smokeHazard.state === 'DETECTING' ? 'EVALUATING' : smokeHazard.state)
                : 'CLEAR';

              const isEmergency = fireState === 'DETECTED' || smokeState === 'DETECTED';

              return (
                <div
                  key={camId}
                  className={`p-4 rounded-xl border transition-all ${
                    isEmergency
                      ? 'bg-[#FF5A36]/10 border-[#FF5A36]/60 shadow-md'
                      : 'bg-[#0D1B2A] border-[#20344A] hover:border-[#2388FF]/50'
                  }`}
                >
                  <div className="flex items-start justify-between pb-2.5 border-b border-[#20344A]">
                    <div>
                      <h4 className="text-xs font-bold text-white truncate max-w-[180px]">{camName}</h4>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <MapPin className="w-3 h-3 text-[#2388FF]" />
                        <span className="text-[10px] text-[#8FA3B8] font-mono">{camLocation}</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      {camId}
                    </span>
                  </div>

                  {/* Decoupled States */}
                  <div className="space-y-2 mt-3">
                    {/* Fire State Tile */}
                    <div className="p-2.5 rounded-lg bg-[#07111F] border border-[#20344A] flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <Flame className={`w-3.5 h-3.5 ${fireState === 'DETECTED' ? 'text-[#FF5A36]' : 'text-[#8FA3B8]'}`} />
                        <span className="text-slate-300 font-medium text-[11px]">Combustion</span>
                      </div>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getStateBadge(fireState, 'fire')}`}>
                        {fireState}
                      </span>
                    </div>

                    {/* Smoke State Tile */}
                    <div className="p-2.5 rounded-lg bg-[#07111F] border border-[#20344A] flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <CloudRain className={`w-3.5 h-3.5 ${smokeState === 'DETECTED' ? 'text-[#F59E0B]' : 'text-[#8FA3B8]'}`} />
                        <span className="text-slate-300 font-medium text-[11px]">Smoke Plume</span>
                      </div>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getStateBadge(smokeState, 'smoke')}`}>
                        {smokeState}
                      </span>
                    </div>
                  </div>

                  {/* Action Link */}
                  {onNavigate && (
                    <button
                      onClick={() => onNavigate('live-monitor')}
                      className="w-full mt-3 py-1.5 rounded-lg bg-[#12263A] hover:bg-[#20344A] text-slate-300 hover:text-white text-[11px] font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Video className="w-3 h-3 text-[#2388FF]" />
                      <span>Open Live View</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ─── Real Fire/Smoke Event Timeline / History (Section 11) ──────────── */}
      <div className="rounded-2xl bg-[#0D1B2A] border border-[#20344A] overflow-hidden">
        <div className="px-5 py-3.5 bg-[#12263A] border-b border-[#20344A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#FF5A36]" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Real Fire &amp; Smoke Event Timeline
            </h3>
          </div>
          <span className="text-[11px] text-[#8FA3B8] font-mono">
            {activeHazardsList.length} Events Logged
          </span>
        </div>

        {activeHazardsList.length === 0 ? (
          <div className="p-8 text-center text-[#8FA3B8]">
            <CheckCircle2 className="w-8 h-8 text-emerald-500/70 mx-auto mb-2" />
            <p className="text-xs font-bold text-white">No Fire/Smoke events recorded.</p>
            <p className="text-[11px] text-[#8FA3B8] mt-1">
              All monitored zones and connected cameras report clear thermal and atmospheric signatures.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#20344A] text-xs">
            {activeHazardsList.map((hazard, idx) => {
              const isFire = hazard.hazard_type?.toLowerCase() === 'fire';
              const isConfirmed = hazard.state === 'CONFIRMED' || hazard.state === 'ACTIVE';

              return (
                <div key={hazard.hazard_id || hazard.event_id || idx} className="p-4 flex items-center justify-between hover:bg-[#12263A]/50 transition">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${
                      isFire
                        ? 'bg-[#FF5A36]/10 text-[#FF5A36] border-[#FF5A36]/30'
                        : 'bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30'
                    }`}>
                      {isFire ? <Flame className="w-4 h-4" /> : <CloudRain className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white uppercase tracking-wide">
                          {isFire ? 'Fire detected' : 'Smoke detected'}
                        </span>
                        <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[#FF5A36]/20 text-[#FF5A36] border border-[#FF5A36]/30">
                          P0
                        </span>
                        <span className="text-[10px] font-mono text-[#8FA3B8]">
                          Camera: {hazard.camera_id} • Zone: {hazard.zone_id || getCameraLocation(hazard.camera_id)}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#8FA3B8] mt-0.5">
                        Confidence: {(hazard.confidence * 100).toFixed(1)}% • State: {hazard.state} • Persistence: {hazard.active_frames || 1} frames
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${getStateBadge(hazard.state, hazard.hazard_type)}`}>
                      {isConfirmed ? 'CONFIRMED' : hazard.state}
                    </span>

                    {onNavigate && (
                      <button
                        onClick={() => onNavigate('live-monitor')}
                        className="px-2.5 py-1 rounded bg-[#12263A] hover:bg-[#20344A] text-slate-200 text-[11px] font-semibold transition"
                      >
                        View Live
                      </button>
                    )}

                    {onSelectIncident && hazard.event_id && (
                      <button
                        onClick={() => onSelectIncident(hazard.event_id!)}
                        className="p-1 rounded bg-[#12263A] hover:bg-[#20344A] text-[#8FA3B8] hover:text-white transition"
                        title="View Incident Details"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default HazardsView;
