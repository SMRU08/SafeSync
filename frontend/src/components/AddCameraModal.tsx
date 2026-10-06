/**
 * AddCameraModal.tsx — SafeSync Professional SOC
 * Modal dialog for registering a new surveillance camera with pre-flight connection testing.
 */

import React, { useState, useEffect } from 'react';
import { X, Camera, CheckCircle2, AlertTriangle, RefreshCw, Smartphone } from 'lucide-react';
import { createCamera, testCameraSource } from '../services/api';
import { CameraConfig } from '../types';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCameraAdded: () => void;
  editCamera?: CameraConfig | null;
}

export const AddCameraModal: React.FC<AddCameraModalProps> = ({
  isOpen,
  onClose,
  onCameraAdded,
  editCamera = null,
}) => {
  const [name, setName] = useState('');
  const [cameraId, setCameraId] = useState('');
  const [sourceType, setSourceType] = useState<'usb' | 'rtsp' | 'http' | 'synthetic'>('usb');
  const [source, setSource] = useState('0');
  const [httpHost, setHttpHost] = useState('');
  const [httpPort, setHttpPort] = useState('8080');
  const [httpPath, setHttpPath] = useState('/video');
  const [location, setLocation] = useState('');
  const [selectedZone, setSelectedZone] = useState('production_floor');
  const [customZone, setCustomZone] = useState('');
  const [fpsTarget, setFpsTarget] = useState(30);
  const [resolution, setResolution] = useState('1280x720');

  const isCustomZone = selectedZone === 'custom';
  const isEditMode = Boolean(editCamera);

  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (editCamera) {
      setName(editCamera.name || '');
      setCameraId(editCamera.camera_id || '');
      const st = ((editCamera.source_type || 'http') as any);
      setSourceType(st);
      const src = editCamera.source || editCamera.safe_source || '';
      setSource(src);
      setLocation(editCamera.location || '');
      setSelectedZone(editCamera.zone_id || 'production_floor');
      setFpsTarget(editCamera.fps || 30);
      setResolution(editCamera.resolution || '1280x720');

      if (src.startsWith('http://') || src.startsWith('https://')) {
        try {
          const u = new URL(src);
          setHttpHost(u.hostname || '');
          setHttpPort(u.port || '8080');
          setHttpPath(u.pathname || '/video');
        } catch {
          // ignore parsing error
        }
      }
    } else {
      setName('');
      setCameraId('');
      setSourceType('usb');
      setSource('0');
      setHttpHost('');
      setHttpPort('8080');
      setHttpPath('/video');
      setLocation('');
      setSelectedZone('production_floor');
      setCustomZone('');
      setFpsTarget(30);
      setResolution('1280x720');
    }
    setTestResult(null);
    setSubmitError(null);
  }, [editCamera, isOpen]);

  const updateHttpUrl = (host: string, port: string, path: string) => {
    const cleanHost = host.trim();
    if (!cleanHost) {
      setSource('');
      return;
    }
    const cleanPort = port.trim() || '8080';
    const cleanPath = path.startsWith('/') ? path.trim() : `/${path.trim() || 'video'}`;
    const assembled = `http://${cleanHost}:${cleanPort}${cleanPath}`;
    setSource(assembled);
  };

  if (!isOpen) return null;

  const handleNameChange = (val: string) => {
    setName(val);
    if (!cameraId || cameraId.startsWith('camera_')) {
      const generated = 'camera_' + val.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').slice(0, 20);
      setCameraId(generated);
    }
  };

  const handleTestConnection = async () => {
    if (sourceType === 'http' && !httpHost.trim()) {
      setTestResult({
        success: false,
        message: 'Enter the phone IP address before testing.',
      });
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testCameraSource(source, sourceType);
      if (res && res.reachable) {
        setTestResult({
          success: true,
          message: res.details || `Reachable at ${res.resolution || 'configured stream'}`,
        });
      } else {
        setTestResult({
          success: false,
          message: res.error || 'Unable to connect to camera source.',
        });
      }
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || 'Connection test failed.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sourceType === 'http' && !httpHost.trim()) {
      setSubmitError('Enter the phone IP address.');
      return;
    }
    if (!name.trim() || !cameraId.trim() || !source.trim()) {
      setSubmitError('Please fill in Camera Name, ID, and Source.');
      return;
    }

    const finalZone = isCustomZone ? customZone.trim() : selectedZone.trim();
    if (isCustomZone && !customZone.trim()) {
      setSubmitError('Please enter a custom Facility Zone name.');
      return;
    }

    if (!finalZone) {
      setSubmitError('Please select or specify a Facility Zone.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    const payload = {
      id: cameraId.trim(),
      name: name.trim(),
      location: location.trim(),
      zone_id: finalZone,
      source: source.trim(),
      source_type: sourceType,
      enabled: true,
      fps_target: Number(fpsTarget),
      resolution: resolution,
      timeout_seconds: 5.0,
    };

    try {
      await createCamera(payload);
      onCameraAdded();
      onClose();
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to add camera.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white text-slate-900 rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">
                {isEditMode ? `Configure Camera (${cameraId})` : 'Add Live Camera'}
              </h2>
              <p className="text-[11px] text-slate-500">
                {isEditMode ? 'Update network stream endpoint, phone IP, or zone' : 'Configure real RTSP, USB webcam, or HTTP camera stream'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {submitError && (
            <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-[11px] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{submitError}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Camera Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g. Entrance Camera"
                required
                className="w-full px-3 py-1.5 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Camera ID</label>
              <input
                type="text"
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                placeholder="e.g. camera_02"
                required
                disabled={isEditMode}
                className="w-full px-3 py-1.5 rounded-md border border-slate-300 font-mono bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Source Type</label>
              <select
                value={sourceType}
                onChange={(e) => {
                  const st = e.target.value as any;
                  setSourceType(st);
                  if (st === 'usb') setSource('0');
                  else if (st === 'rtsp') setSource('rtsp://admin:password@192.168.1.100:554/stream1');
                  else if (st === 'http') {
                    updateHttpUrl(httpHost, httpPort, httpPath);
                  } else if (st === 'synthetic') setSource('synthetic://demo');
                }}
                className="w-full px-3 py-1.5 rounded-md border border-slate-300 bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="usb" className="bg-white text-slate-900">USB Webcam / Local Device</option>
                <option value="rtsp" className="bg-white text-slate-900">RTSP IP Camera Stream</option>
                <option value="http" className="bg-white text-slate-900">HTTP / MJPEG Stream (IP Webcam)</option>
                <option value="synthetic" className="bg-white text-slate-900">Synthetic Test Stream</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-slate-700 font-semibold">Facility Zone</label>
                {isCustomZone && (
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedZone('production_floor');
                      setCustomZone('');
                    }}
                    className="text-[10px] text-sky-600 hover:text-sky-700 font-medium underline cursor-pointer"
                  >
                    Choose preset
                  </button>
                )}
              </div>
              <select
                value={selectedZone}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedZone(val);
                  if (val !== 'custom') setCustomZone('');
                }}
                className="w-full px-3 py-1.5 rounded-md border border-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500 bg-white text-slate-900"
              >
                <option value="entry_gate" className="bg-white text-slate-900">Entry Gate (Main Entry)</option>
                <option value="production_floor" className="bg-white text-slate-900">Production Floor</option>
                <option value="storage_area" className="bg-white text-slate-900">Storage Area</option>
                <option value="loading_dock" className="bg-white text-slate-900">Loading Dock</option>
                <option value="electrical_room" className="bg-white text-slate-900">Electrical Room</option>
                <option value="custom" className="bg-white text-slate-900">Other (Custom)...</option>
              </select>

              {isCustomZone && (
                <div className="mt-2 animate-in fade-in slide-in-from-top-1 duration-150">
                  <input
                    type="text"
                    value={customZone}
                    onChange={(e) => setCustomZone(e.target.value)}
                    placeholder="e.g. West Staging Bay or Enter custom zone"
                    required={isCustomZone}
                    autoFocus
                    className="w-full px-3 py-1.5 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500 text-xs font-medium"
                  />
                </div>
              )}
            </div>
          </div>

          {sourceType === 'http' && (
            <div className="p-3 bg-sky-50/70 rounded-lg border border-sky-200/80 space-y-2">
              <div className="flex items-center gap-1.5 text-sky-900 font-bold text-[11px]">
                <Smartphone className="w-3.5 h-3.5 text-sky-600" />
                <span>Android Phone / IP Webcam Helper</span>
              </div>
              <p className="text-[10px] text-slate-600 leading-relaxed">
                If using the <strong>IP Webcam</strong> app, check the IPv4 address shown on your phone's screen and enter it below:
              </p>
              <div className="grid grid-cols-12 gap-2">
                <div className="col-span-6">
                  <label className="block text-[10px] text-slate-600 font-semibold mb-0.5">Phone IP Address</label>
                  <input
                    type="text"
                    value={httpHost}
                    onChange={(e) => {
                      setHttpHost(e.target.value);
                      updateHttpUrl(e.target.value, httpPort, httpPath);
                    }}
                    placeholder="Enter phone IPv4 address"
                    className="w-full px-2 py-1 rounded border border-slate-300 font-mono text-xs bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  />
                  {!httpHost.trim() && (
                    <span className="block text-[10px] text-amber-600 font-medium mt-0.5">
                      Enter the phone IP address.
                    </span>
                  )}
                </div>
                <div className="col-span-3">
                  <label className="block text-[10px] text-slate-600 font-semibold mb-0.5">Port</label>
                  <input
                    type="text"
                    value={httpPort}
                    onChange={(e) => {
                      setHttpPort(e.target.value);
                      updateHttpUrl(httpHost, e.target.value, httpPath);
                    }}
                    placeholder="8080"
                    className="w-full px-2 py-1 rounded border border-slate-300 font-mono text-xs bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  />
                </div>
                <div className="col-span-3">
                  <label className="block text-[10px] text-slate-600 font-semibold mb-0.5">Path</label>
                  <input
                    type="text"
                    value={httpPath}
                    onChange={(e) => {
                      setHttpPath(e.target.value);
                      updateHttpUrl(httpHost, httpPort, e.target.value);
                    }}
                    placeholder="/video"
                    className="w-full px-2 py-1 rounded border border-slate-300 font-mono text-xs bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              Stream Source / Connection URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="0 or rtsp://... or http://..."
                required
                className="flex-1 px-3 py-1.5 rounded-md border border-slate-300 font-mono text-xs bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={isTesting}
                className="px-3 py-1.5 bg-slate-100 border border-slate-300 hover:bg-slate-200 text-slate-700 rounded-md font-semibold shrink-0 transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {isTesting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Test Feed'}
              </button>
            </div>

            {testResult && (
              <div
                className={`mt-2 p-2 rounded-md text-[11px] flex items-center gap-1.5 ${
                  testResult.success
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Location Label</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. West Staging Bay"
                className="w-full px-3 py-1.5 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Target FPS</label>
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={fpsTarget}
                  onChange={(e) => setFpsTarget(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-md border border-slate-300 font-mono bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Resolution</label>
                <select
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="w-full px-2 py-1.5 rounded-md border border-slate-300 text-[11px] bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                >
                  <option value="1280x720" className="bg-white text-slate-900">720p</option>
                  <option value="1920x1080" className="bg-white text-slate-900">1080p</option>
                  <option value="640x480" className="bg-white text-slate-900">480p</option>
                </select>
              </div>
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded-md border border-slate-300 text-slate-700 font-medium hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-bold transition disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
            >
              {isSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              {isEditMode ? 'Update Camera' : 'Add Camera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
