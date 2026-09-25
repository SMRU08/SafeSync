/**
 * WorkerRegistrationModal.tsx — RAKSHYA VISION
 * Worker facial biometric enrollment modal.
 * Captures a live photo from the webcam and registers the worker profile.
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  X,
  Camera,
  UserPlus,
  Check,
  AlertTriangle,
  RefreshCw,
  User,
  Briefcase,
  MapPin,
} from 'lucide-react';
import { API_BASE_URL } from '../utils/constants';

interface WorkerRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (workerId: string, name: string) => void;
}

export const WorkerRegistrationModal: React.FC<WorkerRegistrationModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [origin, setOrigin] = useState('');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [frStatus, setFrStatus] = useState<{ available: boolean; message: string } | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Fetch face recognition status
  useEffect(() => {
    if (isOpen) {
      fetch(`${API_BASE_URL}/api/workers/face-recognition/status`)
        .then((r) => r.json())
        .then((d) => setFrStatus(d))
        .catch(() => {});
    }
  }, [isOpen]);

  // Start webcam
  const startCamera = useCallback(async () => {
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
        setIsCameraActive(true);
      }
    } catch (err: any) {
      setCameraError('Camera access denied. Please allow camera permissions.');
      setIsCameraActive(false);
    }
  }, []);

  // Stop webcam
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  }, []);

  // Auto-start camera when modal opens
  useEffect(() => {
    if (isOpen) {
      startCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, startCamera, stopCamera]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  // Capture photo from video feed
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setCapturedImage(dataUrl);
    stopCamera();
    setError(null);
  }, [stopCamera]);

  // Retake photo
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
    setError(null);
    startCamera();
  }, [startCamera]);

  // Submit registration
  const handleSubmit = async () => {
    if (!name.trim()) return setError('Worker name is required.');
    if (!jobRole.trim()) return setError('Job role is required.');
    if (!origin.trim()) return setError('Origin / location is required.');
    if (!capturedImage) return setError('Please capture a face photo first.');

    setIsSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/workers/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          job_role: jobRole.trim(),
          origin: origin.trim(),
          face_image_b64: capturedImage,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Registration failed. Please try again.');
        return;
      }
      setSuccessMsg(`✅ ${data.message || `Worker ${name} enrolled as ${data.worker_id}`}`);
      onSuccess?.(data.worker_id, name);
      // Reset after 2s
      setTimeout(() => {
        setName('');
        setJobRole('');
        setOrigin('');
        setCapturedImage(null);
        setSuccessMsg(null);
        onClose();
      }, 2000);
    } catch (err: any) {
      setError('Network error. Ensure the backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#0c1a2e] border border-slate-700 rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 bg-[#111f35] border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center">
              <UserPlus className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Worker Biometric Enrollment</h2>
              <p className="text-[10px] text-slate-400">Capture face + enter details to register</p>
            </div>
          </div>
          <button
            onClick={() => { stopCamera(); onClose(); }}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* FR Status banner */}
        {frStatus && !frStatus.available && (
          <div className="mx-5 mt-4 px-3 py-2 bg-amber-900/40 border border-amber-600/50 rounded-lg flex items-center gap-2 text-[10px] text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{frStatus.message} — Enrollment works but live matching uses placeholder mode.</span>
          </div>
        )}

        <div className="flex flex-col md:flex-row gap-4 p-5">
          {/* Camera / Photo Area */}
          <div className="flex-shrink-0 flex flex-col items-center gap-3 w-full md:w-64">
            <div className="relative w-full aspect-[4/3] bg-slate-900 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center">
              {capturedImage ? (
                <img src={capturedImage} alt="Captured face" className="w-full h-full object-cover" />
              ) : isCameraActive ? (
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover scale-x-[-1]"
                  muted
                  playsInline
                  autoPlay
                />
              ) : (
                <div className="flex flex-col items-center gap-2 text-slate-500 p-4 text-center">
                  <Camera className="w-10 h-10" />
                  {cameraError ? (
                    <p className="text-[10px] text-rose-400">{cameraError}</p>
                  ) : (
                    <p className="text-[10px]">Starting camera...</p>
                  )}
                </div>
              )}

              {/* Live indicator */}
              {isCameraActive && !capturedImage && (
                <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/60 px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
                  <span className="text-[9px] text-white font-bold">LIVE</span>
                </div>
              )}

              {/* Green checkmark on captured */}
              {capturedImage && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                  <Check className="w-3.5 h-3.5 text-white" />
                </div>
              )}
            </div>

            {/* Hidden canvas for capture */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Capture / Retake buttons */}
            {!capturedImage ? (
              <button
                onClick={capturePhoto}
                disabled={!isCameraActive}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-xs font-bold rounded-lg transition"
              >
                <Camera className="w-4 h-4" />
                Capture Face Photo
              </button>
            ) : (
              <button
                onClick={retakePhoto}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg transition"
              >
                <RefreshCw className="w-4 h-4" />
                Retake Photo
              </button>
            )}
          </div>

          {/* Form Fields */}
          <div className="flex-1 flex flex-col gap-3">
            {/* Name */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                <User className="w-3 h-3 inline mr-1" /> Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Rajesh Kumar"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Job Role */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                <Briefcase className="w-3 h-3 inline mr-1" /> Job Role / Designation
              </label>
              <input
                type="text"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="e.g., Floor Supervisor, Welder, Electrician"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Origin / Location */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                <MapPin className="w-3 h-3 inline mr-1" /> Origin / Home Location
              </label>
              <input
                type="text"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g., Bihar, Rajasthan, Mumbai"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 bg-rose-900/40 border border-rose-600/50 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] text-rose-300">{error}</p>
              </div>
            )}

            {/* Success */}
            {successMsg && (
              <div className="flex items-center gap-2 px-3 py-2.5 bg-emerald-900/40 border border-emerald-600/50 rounded-lg">
                <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <p className="text-[11px] text-emerald-300 font-semibold">{successMsg}</p>
              </div>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !capturedImage || !name || !jobRole || !origin}
              className="mt-auto w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-bold rounded-xl shadow-lg transition"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Enrolling Worker...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Enroll Worker
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkerRegistrationModal;
