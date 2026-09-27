/**
 * HazardsView.tsx — SafeSync Professional SOC
 * Fire & Smoke Thermal & Atmospheric Hazard Analysis (Phase 11 & 12).
 * Monitors temporal hazard states: CLEAR, CANDIDATE, DETECTING, CONFIRMED, ACTIVE, CLEARING, CLEARED.
 * Includes interactive single-frame testing, spatial relationship indicators, and zone status matrix.
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
} from 'lucide-react';
import { HazardEventDetail } from '../types';
import { API_BASE_URL } from '../utils/constants';

interface HazardsViewProps {
  hazards: HazardEventDetail[];
  hazardConfig?: any;
}

export const HazardsView: React.FC<HazardsViewProps> = ({ hazards, hazardConfig: _hazardConfig }) => {
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
    formData.append('camera_id', 'camera_01');
    formData.append('zone_id', 'production_floor');

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

  const getStateBadge = (state: string) => {
    switch (state.toUpperCase()) {
      case 'ACTIVE':
      case 'CONFIRMED':
        return 'text-rose-400 bg-rose-500/15 border-rose-500/30';
      case 'DETECTING':
        return 'text-amber-400 bg-amber-500/15 border-amber-500/30 animate-pulse';
      case 'CANDIDATE':
        return 'text-sky-400 bg-sky-500/15 border-sky-500/30';
      case 'CLEARING':
        return 'text-slate-400 bg-slate-800 border-slate-700';
      default:
        return 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5 bg-[#070b14] text-slate-100 select-none">
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
                Fire &amp; Smoke Hazard Monitoring
                <span className="text-[11px] font-mono px-2 py-0.2 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-medium">
                  Dual-Thermal Active
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Decoupled flame combustion and smoke plume tracking with multi-frame temporal validation
              </p>
            </div>
          </div>
        </div>

        {/* Inference Test Upload */}
        <div>
          <label className="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-2 transition cursor-pointer shadow-sm">
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

      {errorMsg && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Spatial Relationship Banner */}
      {relationship && (
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>Scene State: <strong className="text-white font-mono">{sceneState}</strong></span>
          </div>
          <div className="text-slate-400">
            Spatial Interaction: <strong className="text-amber-400">{relationship}</strong>
          </div>
        </div>
      )}

      {/* Annotated Frame Viewer */}
      {annotatedImage && (
        <div className="glass-card rounded-2xl p-4 border border-slate-800 space-y-2">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            Annotated Inference Frame Result
          </h3>
          <div className="aspect-video bg-black rounded-xl overflow-hidden flex items-center justify-center max-h-[400px]">
            <img src={annotatedImage} alt="Hazard Inference Result" className="w-full h-full object-contain" />
          </div>
        </div>
      )}

      {/* Monitored Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { zone: 'Production Floor South', id: 'production_floor', cam: 'CAM-01', fireState: 'CLEAR', smokeState: 'CLEAR' },
          { zone: 'Raw Material Storage', id: 'storage_area', cam: 'CAM-02', fireState: 'CLEAR', smokeState: 'CLEAR' },
          { zone: 'High Voltage Room', id: 'electrical_room', cam: 'CAM-03', fireState: 'CLEAR', smokeState: 'CLEAR' },
          { zone: 'Loading Dock Outer', id: 'loading_dock', cam: 'CAM-04', fireState: 'CLEAR', smokeState: 'CLEAR' },
        ].map((item) => {
          const zoneHazards = activeHazardsList.filter((h) => h.zone_id === item.id);
          const fireHazard = zoneHazards.find((h) => h.hazard_type === 'fire');
          const smokeHazard = zoneHazards.find((h) => h.hazard_type === 'smoke');

          const currentFireState = fireHazard?.state || item.fireState;
          const currentSmokeState = smokeHazard?.state || item.smokeState;

          return (
            <div key={item.id} className="glass-card p-4 rounded-xl border border-slate-800 space-y-3 hover:border-slate-700 transition">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <div>
                  <h4 className="text-xs font-bold text-white">{item.zone}</h4>
                  <span className="text-[10px] text-slate-400 font-mono">{item.cam}</span>
                </div>
                <MapPin className="w-4 h-4 text-sky-400" />
              </div>

              {/* Fire State Tile */}
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-rose-400" />
                  <span className="text-slate-300 font-medium">Combustion</span>
                </div>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getStateBadge(currentFireState)}`}>
                  {currentFireState}
                </span>
              </div>

              {/* Smoke State Tile */}
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CloudRain className="w-4 h-4 text-amber-400" />
                  <span className="text-slate-300 font-medium">Smoke Plume</span>
                </div>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getStateBadge(currentSmokeState)}`}>
                  {currentSmokeState}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Hazards Table / Log */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="px-5 py-3.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Active Hazard Event Log
            </h3>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {activeHazardsList.length} Recorded
          </span>
        </div>

        {activeHazardsList.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-300">All Industrial Zones Clear</p>
            <p className="text-[11px] text-slate-500 mt-1">No active flame combustion or smoke plumes detected.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 text-xs">
            {activeHazardsList.map((hazard, idx) => (
              <div key={idx} className="p-4 flex items-center justify-between hover:bg-slate-900/40 transition">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <Flame className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white uppercase tracking-wide">
                        {hazard.hazard_type}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Camera: {hazard.camera_id} • Zone: {hazard.zone_id}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Confidence: {(hazard.confidence * 100).toFixed(1)}% • Frames Tracked: {hazard.active_frames || 1}
                    </p>
                  </div>
                </div>

                <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${getStateBadge(hazard.state)}`}>
                  {hazard.state}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HazardsView;
