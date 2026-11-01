/**
 * DiseaseDetection page — production version
 *
 * Changes vs demo version:
 *  1. On mount, calls GET /api/disease/model-info to discover whether
 *     the backend has a real CNN loaded or is in demo mode.
 *  2. The amber "Demo mode" warning box is ONLY shown when the backend
 *     returns `is_demo_mode: true` in the prediction response AND the
 *     model is genuinely not loaded (not just a style choice).
 *  3. When a real CNN is active the UI shows a "AI Model Active" green badge
 *     instead of the demo warning.
 *  4. If production mode is active but fell back to demo (model file missing /
 *     TF not installed) the response includes `_fallback_reason` — that is
 *     shown as a specific warning, never as a generic "demo mode" badge.
 *  5. Invalid file types (e.g. .pdf) are rejected with a toast before upload.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Leaf, ScanEye, Loader2, CheckCircle2, AlertTriangle,
  Download, FileImage, X, Info, TrendingUp, Shield, FlaskConical,
  Cpu, Zap,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { diseaseService } from '../services/disease.service';
import type { DiseasePrediction, DiseaseModelInfo } from '../types';
import { downloadBlob } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

const SUPPORTED_CROPS = [
  { value: '',           label: 'Auto-detect', icon: '🔍' },
  { value: 'Tomato',     label: 'Tomato',      icon: '🍅' },
  { value: 'Potato',     label: 'Potato',      icon: '🥔' },
  { value: 'Corn',       label: 'Corn',        icon: '🌽' },
  { value: 'Apple',      label: 'Apple',       icon: '🍎' },
  { value: 'Grape',      label: 'Grape',       icon: '🍇' },
  { value: 'Pepper',     label: 'Pepper',      icon: '🫑' },
  { value: 'Peach',      label: 'Peach',       icon: '🍑' },
  { value: 'Cherry',     label: 'Cherry',      icon: '🍒' },
  { value: 'Strawberry', label: 'Strawberry',  icon: '🍓' },
  { value: 'Squash',     label: 'Squash',      icon: '🎃' },
];

const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
const ALLOWED_EXTS  = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];

export default function DiseaseDetection() {
  usePageTitle('Disease Detection');

  const [file, setFile]       = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [cropType, setCropType] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<DiseasePrediction | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Model info fetched once on mount
  const [modelInfo, setModelInfo] = useState<DiseaseModelInfo | null>(null);

  useEffect(() => {
    diseaseService.getModelInfo()
      .then(setModelInfo)
      .catch(() => setModelInfo(null)); // non-critical — silently ignore
  }, []);

  // ── File handling ────────────────────────────────────────────────────────
  const handleFile = useCallback((f: File) => {
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf('.'));
    if (!ALLOWED_TYPES.includes(f.type) || !ALLOWED_EXTS.includes(ext)) {
      toast.error(`Invalid file "${ext}".  Only JPG, PNG, or WEBP images are accepted.`);
      if (inputRef.current) inputRef.current.value = '';
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 10 MB.');
      return;
    }
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
    setResult(null);
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
  };

  const removeFile = () => {
    setFile(null);
    setPreview('');
    setResult(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  // ── Prediction ───────────────────────────────────────────────────────────
  const handlePredict = async () => {
    if (!file) { toast.error('Please upload a leaf image first'); return; }
    setLoading(true);
    setResult(null);
    try {
      const res = await diseaseService.predict(file, cropType);
      setResult(res);
      toast.success(
        res.is_healthy ? '✅ Plant is healthy!' : `⚠ Disease detected: ${res.disease_name}`
      );
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Prediction failed — please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!result) return;
    try {
      const blob = await diseaseService.downloadReport(result.prediction_id);
      downloadBlob(blob, `disease_report_${result.prediction_id}.pdf`);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Failed to download report');
    }
  };

  // ── Helpers ──────────────────────────────────────────────────────────────
  /** Returns the correct banner/badge to show about the prediction mode. */
  const renderModeNotice = (r: DiseasePrediction) => {
    // Case 1: real CNN was used
    if (!r.is_demo_mode) {
      return (
        <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-xl">
          <Cpu className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-green-700 dark:text-green-400">
            <strong>Real AI inference</strong> — prediction made by a trained Convolutional Neural Network
            ({modelInfo?.num_classes ?? '38'}-class PlantVillage model,
            input size {modelInfo?.input_size ?? 224}×{modelInfo?.input_size ?? 224}px).
          </p>
        </div>
      );
    }

    // Case 2: production mode was requested but fell back (model file missing / TF absent)
    if (r._fallback_reason) {
      return (
        <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-red-700 dark:text-red-400">
              Production mode requested but model unavailable
            </p>
            <p className="text-xs text-red-600 dark:text-red-300 mt-0.5">
              {r._fallback_reason}
            </p>
            <p className="text-xs text-red-500 mt-1">
              Falling back to colour-statistics demo. See <code>ml_models/README.md</code>.
            </p>
          </div>
        </div>
      );
    }

    // Case 3: normal demo mode (DISEASE_MODEL_MODE=demo in .env)
    return (
      <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
        <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400">
            Demo mode active
          </p>
          <p className="text-xs text-amber-600 dark:text-amber-300 mt-0.5">
            Using OpenCV colour-statistics analysis. To enable real CNN inference:
            place a trained model at <code>ml_models/plant_disease_model.keras</code> and
            set <code>DISEASE_MODEL_MODE=production</code> in <code>.env</code>.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page header + model status badge */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ScanEye className="w-7 h-7 text-primary-600" /> AI Disease Detection
          </h1>
          <p className="text-gray-500 mt-1">Upload a plant leaf image to detect diseases with AI</p>
        </div>

        {/* Dynamic model status badge */}
        {modelInfo && (
          modelInfo.model_loaded ? (
            <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <Cpu className="w-4 h-4 text-green-600" />
              <div>
                <div className="text-xs font-semibold text-green-700 dark:text-green-400">
                  CNN Model Active
                </div>
                <div className="text-xs text-green-600 dark:text-green-500">
                  {modelInfo.num_classes} classes · {modelInfo.input_size}px input
                </div>
              </div>
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <Zap className="w-4 h-4 text-amber-600" />
              <div>
                <div className="text-xs font-semibold text-amber-700 dark:text-amber-400">
                  Demo Mode
                </div>
                <div className="text-xs text-amber-600 dark:text-amber-500">
                  Colour analysis · no trained model
                </div>
              </div>
            </div>
          )
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* ── Upload panel ───────────────────────────────────────────────── */}
        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-900 dark:text-white">Upload Leaf Image</h2>

          {/* Crop type selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Crop Type <span className="text-gray-400">(optional — improves accuracy)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {SUPPORTED_CROPS.map((crop) => (
                <button
                  key={crop.value}
                  onClick={() => setCropType(crop.value)}
                  className={`px-3 py-1.5 rounded-xl text-sm font-medium transition-all ${
                    cropType === crop.value
                      ? 'bg-primary text-white shadow-md'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-1">{crop.icon}</span>
                  {crop.label}
                </button>
              ))}
            </div>
          </div>

          {/* Drag-and-drop / file picker */}
          {!preview ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                dragging
                  ? 'border-primary bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary hover:bg-primary-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <Upload className="w-12 h-12 mx-auto text-primary-500 mb-3" />
              <p className="font-semibold text-gray-700 dark:text-gray-300">
                Drag &amp; drop a leaf image here
              </p>
              <p className="text-sm text-gray-400 mt-1">or click to browse</p>
              <p className="text-xs text-gray-400 mt-2">JPG · PNG · WEBP · Max 10 MB</p>
            </div>
          ) : (
            <div className="relative rounded-2xl overflow-hidden">
              <img
                src={preview}
                alt="Leaf preview"
                className="w-full h-64 object-contain bg-gray-50 dark:bg-gray-700"
              />
              <button
                onClick={removeFile}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded-lg backdrop-blur-sm">
                {file?.name}
              </div>
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />

          {preview && (
            <button
              onClick={handlePredict}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60"
            >
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Analysing image…</>
              ) : (
                <><ScanEye className="w-5 h-5 mr-2" /> Detect Disease</>
              )}
            </button>
          )}

          {loading && (
            <div className="p-4 bg-primary-50 dark:bg-primary-900/20 rounded-xl text-center">
              <div className="flex items-center justify-center gap-2 text-primary-600">
                <FlaskConical className="w-5 h-5" />
                <span className="text-sm font-medium">
                  {modelInfo?.model_loaded
                    ? 'CNN is running inference…'
                    : 'Analysing colour features…'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* ── Results panel ──────────────────────────────────────────────── */}
        <div>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {/* Status banner */}
                <div className={`card border-2 ${
                  result.is_healthy
                    ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
                    : 'border-orange-400 bg-orange-50 dark:bg-orange-900/20'
                }`}>
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                      result.is_healthy ? 'bg-green-500' : 'bg-orange-500'
                    }`}>
                      {result.is_healthy
                        ? <CheckCircle2 className="w-8 h-8 text-white" />
                        : <AlertTriangle className="w-8 h-8 text-white" />
                      }
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Result
                      </div>
                      <div className="text-xl font-bold text-gray-900 dark:text-white">
                        {result.is_healthy ? 'Healthy Plant' : result.disease_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {result.crop_type} · {(result.confidence * 100).toFixed(1)}% confidence
                      </div>
                    </div>
                  </div>

                  {/* Confidence bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Confidence</span>
                      <span>{(result.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${
                          result.is_healthy ? 'bg-green-500' : 'bg-orange-500'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${result.confidence * 100}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                  </div>

                  {/* Mode notice — only shown when relevant */}
                  <div className="mt-3">
                    {renderModeNotice(result)}
                  </div>
                </div>

                {/* Symptoms */}
                {!result.is_healthy && result.symptoms.length > 0 && (
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-500" /> Symptoms
                    </h3>
                    <ul className="space-y-2">
                      {result.symptoms.map((s, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-2 flex-shrink-0" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Causes */}
                {!result.is_healthy && result.causes.length > 0 && (
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Info className="w-5 h-5 text-blue-500" /> Causes
                    </h3>
                    <ul className="space-y-2">
                      {result.causes.map((c, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Treatment */}
                {!result.is_healthy && result.treatment.length > 0 && (
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <FlaskConical className="w-5 h-5 text-green-500" /> Treatment Recommendations
                    </h3>
                    <ul className="space-y-2">
                      {result.treatment.map((t, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Prevention */}
                {!result.is_healthy && result.prevention.length > 0 && (
                  <div className="card">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Shield className="w-5 h-5 text-purple-500" /> Prevention Methods
                    </h3>
                    <ul className="space-y-2">
                      {result.prevention.map((p, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <Shield className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Download */}
                <button onClick={handleDownload} className="btn-primary w-full">
                  <Download className="w-5 h-5 mr-2" /> Download PDF Report
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="card flex flex-col items-center justify-center text-center min-h-[360px] space-y-4"
              >
                <FileImage className="w-16 h-16 text-gray-300" />
                <div>
                  <p className="text-gray-500 font-medium">No prediction yet</p>
                  <p className="text-gray-400 text-sm mt-1">
                    Select a crop type, upload a leaf photo, and click{' '}
                    <strong>Detect Disease</strong>.
                  </p>
                </div>
                <div className="grid grid-cols-5 gap-3 mt-2">
                  {SUPPORTED_CROPS.slice(1, 6).map((crop) => (
                    <div key={crop.value} className="text-center">
                      <div className="text-2xl mb-1">{crop.icon}</div>
                      <div className="text-xs text-gray-400">{crop.label}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
