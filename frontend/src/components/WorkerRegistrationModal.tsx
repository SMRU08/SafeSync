/**
 * WorkerRegistrationModal.tsx — RAKSHYA VISION
 * Worker facial biometric enrollment modal.
 * Supports:
 * 1. Live Webcam (with helpful permission recovery & retry)
 * 2. Upload Photo File (drag & drop or browse from local disk)
 * 3. Capture from System Live Camera (CAM-01, etc.)
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
  UploadCloud,
  Video,
  Info,
} from 'lucide-react';
import { API_BASE_URL } from '../utils/constants';

interface WorkerRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  cameras?: { camera_id: string; name: string }[];
  onSuccess?: (workerId: string, name: string) => void;
}

type CaptureSource = 'webcam' | 'upload' | 'camera_stream';

export const WorkerRegistrationModal: React.FC<WorkerRegistrationModalProps> = ({
  isOpen,
  onClose,
  cameras = [],
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [origin, setOrigin] = useState('');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<CaptureSource>('webcam');

  // Webcam state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // System camera stream state
  const [selectedCamId, setSelectedCamId] = useState<string>(cameras[0]?.camera_id || 'camera_01');
  const [isFetchingSnapshot, setIsFetchingSnapshot] = useState(false);

  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [frStatus, setFrStatus] = useState<{ available: boolean; engine?: string; message: string } | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Update selected camera if cameras change
  useEffect(() => {
    if (cameras.length > 0 && !selectedCamId) {
      setSelectedCamId(cameras[0].camera_id);
    }
  }, [cameras, selectedCamId]);

  // Fetch biometric engine status
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
      setCameraError('Camera access denied or webcam not available.');
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

  // Control camera when active source changes
  useEffect(() => {
    if (isOpen && activeSource === 'webcam' && !capturedImage) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, activeSource, capturedImage, startCamera, stopCamera]);

  // Capture photo from webcam video element
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

  // Handle local file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, WEBP).');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      setCapturedImage(result);
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  // Drag and drop handler
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, WEBP).');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      setCapturedImage(result);
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  // Capture frame from active system camera stream
  const captureFromSystemCamera = async () => {
    if (!selectedCamId) return;
    setIsFetchingSnapshot(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/cameras/${selectedCamId}/snapshot?t=${Date.now()}`);
      if (!res.ok) {
        throw new Error('Unable to capture frame from selected camera.');
      }
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onloadend = () => {
        setCapturedImage(reader.result as string);
        setIsFetchingSnapshot(false);
      };
      reader.readAsDataURL(blob);
    } catch (err: any) {
      setError(err.message || 'Failed to capture frame from system camera.');
      setIsFetchingSnapshot(false);
    }
  };

  // Retake photo
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
    setError(null);
    if (activeSource === 'webcam') {
      startCamera();
    }
  }, [activeSource, startCamera]);

  // Submit registration
  const handleSubmit = async () => {
    if (!name.trim()) return setError('Worker name is required.');
    if (!jobRole.trim()) return setError('Job role is required.');
    if (!origin.trim()) return setError('Origin / location is required.');
    if (!capturedImage) return setError('Please capture or upload a face photo first.');

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
      setTimeout(() => {
        setName('');
        setJobRole('');
        setOrigin('');
        setCapturedImage(null);
        setSuccessMsg(null);
        onClose();
      }, 1800);
    } catch (err: any) {
      setError('Network error. Ensure the backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-[#0c1a2e] border border-slate-700 rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#111f35] border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center">
              <UserPlus className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white">Worker Biometric Enrollment</h2>
                {frStatus?.available && (
                  <span className="bg-emerald-950/80 border border-emerald-600/60 text-emerald-400 text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Biometric AI Ready
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-400">Capture or upload face photo + profile details</p>
            </div>
          </div>
          <button
            onClick={() => {
              stopCamera();
              onClose();
            }}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Input Source Mode Selector Tabs */}
        {!capturedImage && (
          <div className="flex items-center gap-1.5 px-5 pt-3.5 bg-[#0c1a2e]">
            <button
              onClick={() => {
                setActiveSource('webcam');
                setError(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeSource === 'webcam'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Camera className="w-3.5 h-3.5" />
              Live Webcam
            </button>
            <button
              onClick={() => {
                setActiveSource('upload');
                stopCamera();
                setError(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeSource === 'upload'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <UploadCloud className="w-3.5 h-3.5" />
              Upload Photo File
            </button>
            <button
              onClick={() => {
                setActiveSource('camera_stream');
                stopCamera();
                setError(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeSource === 'camera_stream'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              System Camera Stream
            </button>
          </div>
        )}

        <div className="flex flex-col md:flex-row gap-4 p-5">
          {/* Photo Preview / Capture Area */}
          <div className="flex-shrink-0 flex flex-col items-center gap-3 w-full md:w-64">
            <div className="relative w-full aspect-[4/3] bg-slate-900 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center">
              {capturedImage ? (
                <img src={capturedImage} alt="Captured face" className="w-full h-full object-cover" />
              ) : activeSource === 'webcam' ? (
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
                        <p className="text-[10px] text-slate-400 leading-tight">
                          Browser blocked webcam access. Click below to upload a photo file instead:
                        </p>
                        <button
                          onClick={() => setActiveSource('upload')}
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
              ) : activeSource === 'upload' ? (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center w-full h-full p-4 border-2 border-dashed border-slate-600 hover:border-sky-500 rounded-xl cursor-pointer text-center group transition"
                >
                  <UploadCloud className="w-9 h-9 text-sky-400 group-hover:scale-110 transition" />
                  <p className="text-xs font-bold text-white mt-2">Click to Browse Photo</p>
                  <p className="text-[10px] text-slate-400 mt-1">or drag &amp; drop file here</p>
                  <span className="mt-2 text-[9px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                    JPG, PNG, WEBP
                  </span>
                </div>
              ) : (
                /* System Camera Stream */
                <div className="flex flex-col items-center justify-center w-full h-full p-3 text-center gap-2">
                  <Video className="w-8 h-8 text-sky-400" />
                  <p className="text-xs font-bold text-white">System Camera Feed</p>
                  <p className="text-[10px] text-slate-400">Select a camera to grab the current frame</p>
                </div>
              )}

              {/* Live indicator on webcam */}
              {isCameraActive && !capturedImage && activeSource === 'webcam' && (
                <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/60 px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" />
                  <span className="text-[9px] text-white font-bold">WEBCAM</span>
                </div>
              )}

              {/* Green checkmark on captured */}
              {capturedImage && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                  <Check className="w-3.5 h-3.5 text-white" />
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

            {/* Action buttons based on source */}
            {capturedImage ? (
              <button
                onClick={retakePhoto}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retake / Change Photo
              </button>
            ) : activeSource === 'webcam' ? (
              <div className="w-full flex flex-col gap-2">
                <button
                  onClick={capturePhoto}
                  disabled={!isCameraActive}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-bold rounded-lg transition shadow"
                >
                  <Camera className="w-4 h-4" />
                  Capture Photo
                </button>
                {cameraError && (
                  <button
                    onClick={startCamera}
                    className="w-full py-1 text-[10px] text-slate-400 hover:text-white underline"
                  >
                    Retry Camera Permission
                  </button>
                )}
              </div>
            ) : activeSource === 'upload' ? (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-lg transition shadow"
              >
                <UploadCloud className="w-4 h-4" />
                Browse Local File
              </button>
            ) : (
              <div className="w-full flex flex-col gap-2">
                <select
                  value={selectedCamId}
                  onChange={(e) => setSelectedCamId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none"
                >
                  {cameras.length > 0 ? (
                    cameras.map((c) => (
                      <option key={c.camera_id} value={c.camera_id}>
                        {c.name} ({c.camera_id})
                      </option>
                    ))
                  ) : (
                    <option value="camera_01">CAM-01 — Production Floor South</option>
                  )}
                </select>
                <button
                  onClick={captureFromSystemCamera}
                  disabled={isFetchingSnapshot}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition shadow"
                >
                  {isFetchingSnapshot ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Camera className="w-3.5 h-3.5" />
                  )}
                  Grab Frame from Stream
                </button>
              </div>
            )}
          </div>

          {/* Form Fields */}
          <div className="flex-1 flex flex-col gap-3">
            {/* Name */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <User className="w-3 h-3 inline mr-1 text-sky-400" /> Full Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Rajesh Kumar"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Job Role */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <Briefcase className="w-3 h-3 inline mr-1 text-sky-400" /> Job Role / Designation *
              </label>
              <input
                type="text"
                value={jobRole}
                onChange={(e) => setJobRole(e.target.value)}
                placeholder="e.g., Floor Supervisor, Welder, Electrician"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Origin / Location */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <MapPin className="w-3 h-3 inline mr-1 text-sky-400" /> Origin / Location *
              </label>
              <input
                type="text"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g., Bihar, Rajasthan, Unit-2 Staging"
                className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder:text-slate-500"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2 px-3 py-2 bg-rose-900/40 border border-rose-600/50 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] text-rose-300 leading-tight">{error}</p>
              </div>
            )}

            {/* Success Message */}
            {successMsg && (
              <div className="flex items-center gap-2 px-3 py-2 bg-emerald-900/40 border border-emerald-600/50 rounded-lg">
                <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <p className="text-[11px] text-emerald-300 font-semibold">{successMsg}</p>
              </div>
            )}

            {/* Biometric Tip */}
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
              <Info className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
              <span>Face embeddings are extracted &amp; encrypted directly into the database.</span>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !capturedImage || !name || !jobRole || !origin}
              className="mt-auto w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-bold rounded-xl shadow-lg transition"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Generating Biometric Embeddings...
                </>
              ) : (
                <>
                  <UserPlus className="w-3.5 h-3.5" />
                  Complete Enrollment
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
