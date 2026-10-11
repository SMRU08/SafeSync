/**
 * RecordedVideoAnalysis.tsx — SafeSync BPUT Hackathon 2026
 * Dedicated CCTV / Industrial Safety Recorded Video Analysis Panel.
 *
 * Implements Section 30:
 * - Scans and lists all CCTV videos in D:\P0
 * - Displays real-time processing status and frame counts
 * - Plays actual generated annotated MP4 video with full controls
 * - Zero fake progress, zero fake telemetry
 */

import React, { useState, useEffect } from 'react';
import {
  Film,
  Play,
  CheckCircle2,
  Clock,
  RefreshCw,
  FileVideo,
} from 'lucide-react';

interface VideoSummary {
  video_name: string;
  duration: number;
  fps: number;
  resolution: string;
  frames_processed: number;
  output_frames_verified: number;
  persons_detected: number;
  helmet_detections: number;
  vest_detections: number;
  glove_detections: number;
  footwear_detections: number;
  fire_detections: number;
  smoke_detections: number;
  confirmed_ppe_violations: number;
  unknown_states: number;
  processing_time: number;
  effective_processing_fps: number;
  status: string;
}

interface VideoItem {
  name: string;
  size_mb: number;
  status: 'COMPLETED' | 'PROCESSING' | 'PENDING' | 'FAILED';
  has_annotated: boolean;
  annotated_name: string;
  stream_url: string | null;
  summary: VideoSummary | null;
}

interface P0StatusResponse {
  input_dir: string;
  output_dir: string;
  total_videos: number;
  completed_count: number;
  pending_count: number;
  videos: VideoItem[];
}

export const RecordedVideoAnalysis: React.FC = () => {
  const [data, setData] = useState<P0StatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/p0/status');
      if (res.ok) {
        const json: P0StatusResponse = await res.json();
        setData(json);
        // If no video is selected yet, or current selection updated, keep selected
        setSelectedVideo((prev) => {
          if (!prev && json.videos.length > 0) {
            // Pick first completed video, or first video
            const firstCompleted = json.videos.find((v) => v.status === 'COMPLETED');
            return firstCompleted || json.videos[0];
          }
          if (prev) {
            const updated = json.videos.find((v) => v.name === prev.name);
            return updated || prev;
          }
          return null;
        });
      }
    } catch (err) {
      console.error('Failed to fetch P0 video status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#0b1324] border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
                <Film className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                  Recorded Video Analysis
                  <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 font-semibold uppercase tracking-wider">
                    P0 Verification
                  </span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated offline CCTV safety audit using SafeSync Production AI Pipeline
                </p>
              </div>
            </div>
          </div>

          {/* Path & Counts */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold">Input Directory</span>
              <span className="font-mono text-sky-300">{data?.input_dir || 'D:\\P0'}</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
              <span className="text-slate-500 uppercase text-[10px] block font-semibold">Output Directory</span>
              <span className="font-mono text-emerald-300">{data?.output_dir || 'D:\\P0\\output'}</span>
            </div>
            <button
              onClick={() => {
                setIsLoading(true);
                fetchStatus();
              }}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title="Refresh status"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Operational Telemetry Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/80">
          <div className="bg-slate-900/50 rounded-lg p-2.5 border border-slate-800/60">
            <span className="text-[11px] text-slate-400 uppercase font-medium">Scanned Videos</span>
            <div className="text-lg font-bold text-white mt-0.5">{data?.total_videos || 0}</div>
          </div>
          <div className="bg-emerald-950/20 rounded-lg p-2.5 border border-emerald-900/40">
            <span className="text-[11px] text-emerald-400 uppercase font-medium">Analysis Completed</span>
            <div className="text-lg font-bold text-emerald-300 mt-0.5">{data?.completed_count || 0}</div>
          </div>
          <div className="bg-sky-950/20 rounded-lg p-2.5 border border-sky-900/40">
            <span className="text-[11px] text-sky-400 uppercase font-medium">Processing / Pending</span>
            <div className="text-lg font-bold text-sky-300 mt-0.5">{data?.pending_count || 0}</div>
          </div>
          <div className="bg-purple-950/20 rounded-lg p-2.5 border border-purple-900/40">
            <span className="text-[11px] text-purple-400 uppercase font-medium">Model Pipeline</span>
            <div className="text-sm font-semibold text-purple-300 mt-1">V3 Production (7 Classes)</div>
          </div>
        </div>
      </div>

      {/* Main Split Layout: Player on Left/Top, List on Right/Bottom */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Player & Active Video Telemetry */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#0b1324] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-3.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 overflow-hidden">
                <Play className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="text-sm font-semibold text-white truncate">
                  {selectedVideo ? selectedVideo.name : 'Select a video'}
                </span>
              </div>
              {selectedVideo?.status === 'COMPLETED' && (
                <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> ANNOTATED READY
                </span>
              )}
            </div>

            {/* Video Viewport */}
            <div className="relative bg-black flex items-center justify-center min-h-[340px] max-h-[500px]">
              {selectedVideo?.has_annotated ? (
                <video
                  key={selectedVideo.stream_url || selectedVideo.name}
                  src={selectedVideo.stream_url || `/api/p0/stream/${selectedVideo.annotated_name}`}
                  controls
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-auto max-h-[500px] object-contain"
                />
              ) : (
                <div className="text-center p-8 space-y-3">
                  <Clock className="w-12 h-12 text-sky-400/60 mx-auto animate-pulse" />
                  <p className="text-sm font-semibold text-slate-300">
                    {selectedVideo?.status === 'PROCESSING'
                      ? 'Video is currently being processed by the AI pipeline...'
                      : 'Video analysis pending in queue.'}
                  </p>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    The annotated MP4 will stream automatically with full AI detection bounding boxes once processing finishes.
                  </p>
                </div>
              )}
            </div>

            {/* Active Video Telemetry Card */}
            {selectedVideo?.summary && (
              <div className="p-4 bg-slate-900/70 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Duration: <strong className="text-white">{selectedVideo.summary.duration}s</strong></span>
                  <span>FPS: <strong className="text-white">{selectedVideo.summary.fps}</strong></span>
                  <span>Resolution: <strong className="text-white">{selectedVideo.summary.resolution}</strong></span>
                  <span>Processing Speed: <strong className="text-sky-300">{selectedVideo.summary.effective_processing_fps} FPS</strong></span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                  <div className="bg-slate-800/40 rounded p-2 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">WORKER DETECTIONS</span>
                    <span className="text-sm font-bold text-sky-400">{selectedVideo.summary.persons_detected}</span>
                  </div>
                  <div className="bg-slate-800/40 rounded p-2 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">PPE VIOLATIONS</span>
                    <span className={`text-sm font-bold ${selectedVideo.summary.confirmed_ppe_violations > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {selectedVideo.summary.confirmed_ppe_violations}
                    </span>
                  </div>
                  <div className="bg-slate-800/40 rounded p-2 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">FIRE DETECTIONS</span>
                    <span className={`text-sm font-bold ${selectedVideo.summary.fire_detections > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                      {selectedVideo.summary.fire_detections}
                    </span>
                  </div>
                  <div className="bg-slate-800/40 rounded p-2 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">SMOKE DETECTIONS</span>
                    <span className={`text-sm font-bold ${selectedVideo.summary.smoke_detections > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                      {selectedVideo.summary.smoke_detections}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Video Playlist & Inventory */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-1">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Recorded Video Inventory ({data?.videos.length || 0})
            </h2>
            <span className="text-[11px] text-slate-400">Click to inspect / play</span>
          </div>

          <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
            {data?.videos.map((vid) => {
              const isSelected = selectedVideo?.name === vid.name;
              const isCompleted = vid.status === 'COMPLETED';
              const isProcessing = vid.status === 'PROCESSING';

              return (
                <div
                  key={vid.name}
                  onClick={() => setSelectedVideo(vid)}
                  className={`p-3.5 rounded-xl border transition cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800/90 border-sky-500 shadow-md ring-1 ring-sky-500/30'
                      : 'bg-[#0b1324] border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <div className={`p-2 rounded-lg flex-shrink-0 ${
                        isCompleted ? 'bg-emerald-500/10 text-emerald-400' : isProcessing ? 'bg-sky-500/10 text-sky-400' : 'bg-slate-800 text-slate-500'
                      }`}>
                        <FileVideo className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden">
                        <h3 className="text-xs font-semibold text-white truncate" title={vid.name}>
                          {vid.name}
                        </h3>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {vid.size_mb} MB {vid.summary ? `• ${vid.summary.resolution} • ${vid.summary.duration}s` : ''}
                        </p>
                      </div>
                    </div>

                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider flex-shrink-0 ${
                      isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : isProcessing
                        ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40 animate-pulse'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {vid.status}
                    </span>
                  </div>

                  {vid.summary && (
                    <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Workers: <strong className="text-sky-300">{vid.summary.persons_detected}</strong></span>
                      <span>Violations: <strong className={vid.summary.confirmed_ppe_violations > 0 ? 'text-rose-400' : 'text-emerald-400'}>{vid.summary.confirmed_ppe_violations}</strong></span>
                      <span>Fire: <strong className={vid.summary.fire_detections > 0 ? 'text-rose-400' : 'text-slate-400'}>{vid.summary.fire_detections}</strong></span>
                      <span>Smoke: <strong className={vid.summary.smoke_detections > 0 ? 'text-amber-400' : 'text-slate-400'}>{vid.summary.smoke_detections}</strong></span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
