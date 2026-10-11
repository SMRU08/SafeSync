/**
 * DemoVideoPlayer.tsx — SafeSync Industrial SOC
 * Section 16 & 17 Demo Mode Video Playback Component.
 *
 * Rules:
 * - Uses real video file if present in frontend/public/demo/.
 * - If video does NOT exist: Shows explicit empty-state:
 *     "DEMO VIDEOS NOT FOUND"
 *     Expected location: frontend/public/demo/...
 *     Button: [ Refresh Demo Library ]
 *   Zero fake video playback, zero pretend playback.
 * - If video exists:
 *     Visible badge: DEMO
 *     Scenario info: Scenario: ..., Camera: Demo Camera 01, Status: PLAYING / PAUSED
 *     Full Controls: Play/Pause, Restart, Mute, Timeline scrubber
 * - Clear banner: "DEMO VIDEO PLAYBACK • AI ANALYSIS NOT CONNECTED"
 *   Never draws fake real-time AI bounding boxes over static demo video.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  AlertTriangle,
  RefreshCw,
  VideoOff,
  Tv,
} from 'lucide-react';

interface DemoVideoPlayerProps {
  scenarioId: string;
  scenarioTitle: string;
  videoSrc?: string;
  expectedVideoPath: string;
  onRefreshLibrary?: () => void;
}

export const DemoVideoPlayer: React.FC<DemoVideoPlayerProps> = ({
  scenarioId: _scenarioId,
  scenarioTitle,
  videoSrc,
  expectedVideoPath,
  onRefreshLibrary,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [isMuted, setIsMuted] = useState<boolean>(true);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [hasError, setHasError] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  useEffect(() => {
    setHasError(false);
    setIsPlaying(true);
    setCurrentTime(0);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {
        setIsPlaying(false);
      });
    }
  }, [videoSrc]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    }
  };

  const handleRestart = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = 0;
    videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setCurrentTime(val);
    if (videoRef.current) {
      videoRef.current.currentTime = val;
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setHasError(false);
    if (onRefreshLibrary) {
      onRefreshLibrary();
    }
    setTimeout(() => {
      setIsRefreshing(false);
    }, 800);
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-[#0c1a2e] rounded-xl border border-amber-500/30 shadow-xl overflow-hidden flex flex-col">
      {/* ─── Video Container Header ────────────────────────────────────────── */}
      <div className="px-4 py-2.5 border-b border-[#20344A] bg-[#111f35] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
          <div className="flex items-center gap-2">
            <span className="font-bold text-white text-xs tracking-tight">
              Demo Camera 01 &mdash; {scenarioTitle}
            </span>
            <span className="text-[10px] font-mono font-black uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              DEMO
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Status:</span>
          <span className={hasError ? 'text-rose-400 font-bold' : isPlaying ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
            {hasError ? 'NO ASSET' : isPlaying ? 'PLAYING' : 'PAUSED'}
          </span>
        </div>
      </div>

      {/* ─── Viewport Area: Video Player or Empty State ─────────────────────── */}
      <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
        {hasError || !videoSrc ? (
          /* Section 16 Required Empty-State when video does not exist */
          <div className="flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto space-y-3">
            <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <VideoOff className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-sm font-black uppercase tracking-wider text-white">
                DEMO VIDEOS NOT FOUND
              </h3>
              <p className="text-xs text-slate-300 mt-1">
                No pre-recorded video file was found for this scenario.
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-left w-full space-y-1">
              <div className="text-slate-400">Expected location:</div>
              <div className="text-sky-300 font-semibold break-all">{expectedVideoPath}</div>
              <div className="text-slate-500 text-[10px] pt-1">
                or <code className="text-slate-400">data/demo_videos/</code>
              </div>
            </div>
            <p className="text-[11px] text-amber-300/80 italic">
              SafeSync does not synthesize fake video feeds or fabricate artificial video playback. Verified benchmark telemetry for this scenario is shown in the audit panel below.
            </p>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="mt-2 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh Demo Library</span>
            </button>
          </div>
        ) : (
          /* Actual Video Player */
          <>
            <video
              ref={videoRef}
              src={videoSrc}
              loop
              muted={isMuted}
              autoPlay
              playsInline
              onTimeUpdate={() => {
                if (videoRef.current) {
                  setCurrentTime(videoRef.current.currentTime);
                }
              }}
              onLoadedMetadata={() => {
                if (videoRef.current) {
                  setDuration(videoRef.current.duration);
                }
              }}
              onError={() => {
                setHasError(true);
              }}
              className="w-full h-full object-contain bg-black"
            />

            {/* Top-Left Visible Overlay Badges (Section 16) */}
            <div className="absolute top-3 left-3 z-20 flex flex-col gap-1.5 pointer-events-none">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-black uppercase font-mono tracking-wider bg-amber-500 text-slate-950 shadow-md">
                  DEMO
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-black/70 backdrop-blur-xs text-white border border-white/20">
                  Scenario: {scenarioTitle}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-slate-300">
                <span className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-xs border border-white/10">
                  Camera: Demo Camera 01
                </span>
                <span className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-xs border border-white/10">
                  Status: {isPlaying ? 'PLAYING' : 'PAUSED'}
                </span>
              </div>
            </div>

            {/* Top-Right Timecode */}
            <div className="absolute top-3 right-3 z-20 bg-black/75 backdrop-blur-xs px-2.5 py-1 rounded text-[10px] text-white font-mono border border-white/10">
              {formatTime(currentTime)} / {formatTime(duration)}
            </div>
          </>
        )}
      </div>

      {/* ─── Video Controls Bar (Section 16: Play, Pause, Restart, Mute, Timeline) ── */}
      {!hasError && videoSrc && (
        <div className="px-4 py-2 bg-[#0D1B2A] border-t border-[#20344A] flex flex-col gap-2">
          {/* Timeline Range Scrubber */}
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-slate-400 w-10 text-right">
              {formatTime(currentTime)}
            </span>
            <input
              type="range"
              min={0}
              max={duration || 100}
              step={0.1}
              value={currentTime}
              onChange={handleSeek}
              className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <span className="text-[10px] font-mono text-slate-400 w-10">
              {formatTime(duration)}
            </span>
          </div>

          {/* Buttons: Play/Pause, Restart, Mute */}
          <div className="flex items-center justify-between pt-0.5">
            <div className="flex items-center gap-2">
              <button
                onClick={togglePlay}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition cursor-pointer border border-slate-700"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 text-emerald-400" />}
              </button>

              <button
                onClick={handleRestart}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition cursor-pointer border border-slate-700"
                title="Restart Video"
              >
                <RotateCcw className="w-4 h-4 text-sky-400" />
              </button>

              <button
                onClick={toggleMute}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition cursor-pointer border border-slate-700"
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX className="w-4 h-4 text-slate-400" /> : <Volume2 className="w-4 h-4 text-emerald-400" />}
              </button>

              <span className="text-[11px] text-slate-400 ml-2 hidden sm:inline">
                Loop Playback Active
              </span>
            </div>

            <div className="text-[10px] font-mono text-amber-300/90 flex items-center gap-1.5">
              <Tv className="w-3.5 h-3.5 text-amber-400" />
              <span>Offline Pre-Recorded Stream</span>
            </div>
          </div>
        </div>
      )}

      {/* ─── Section 17 Required Banner: NO FAKE REAL-TIME AI ───────────────── */}
      <div className="px-4 py-2 bg-gradient-to-r from-amber-500/15 via-[#0D1B2A] to-amber-500/15 border-t border-amber-500/30 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-amber-200">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="font-bold tracking-tight">
            DEMO VIDEO PLAYBACK &bull; AI ANALYSIS NOT CONNECTED
          </span>
        </div>
        <span className="text-[11px] text-slate-300 font-medium hidden md:inline">
          Showing verified benchmark detection state for this scenario
        </span>
      </div>
    </div>
  );
};

export default DemoVideoPlayer;
