/**
 * CropRecommendation page — production version
 *
 * New features vs the previous demo version:
 *  1. "Detect My Location" button uses the browser Geolocation API to get
 *     the user's real latitude / longitude.
 *  2. After geolocation succeeds the page calls GET /api/crop/live-weather,
 *     which calls OpenWeatherMap on the backend, and auto-fills the
 *     Temperature, Humidity, and Rainfall sliders with live values.
 *  3. The city name returned by OpenWeatherMap is placed into the Location field.
 *  4. If the backend has no OWM API key configured (501) the page shows a
 *     friendly notice and leaves sliders in manual mode — nothing breaks.
 *  5. All manual slider edits still work normally after auto-fill.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sprout, Brain, Loader2, Download, CheckCircle2, TrendingUp,
  Beaker, MapPin, Leaf, Navigation, Thermometer, Droplets,
  CloudRain, AlertCircle, Wifi, WifiOff,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cropService } from '../services/crop.service';
import type { CropRecommendationResponse } from '../types';
import { downloadBlob } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

const SOIL_TYPES = ['Loamy', 'Sandy', 'Clayey', 'Black', 'Red', 'Alluvial', 'Laterite'];

interface CropForm {
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  soil_type: string;
  location: string;
}

const DEFAULT_FORM: CropForm = {
  nitrogen: 80, phosphorus: 45, potassium: 40,
  temperature: 25, humidity: 70, ph: 6.5, rainfall: 120,
  soil_type: 'Loamy', location: '',
};

export default function CropRecommendation() {
  usePageTitle('Crop Recommendation');

  const [form, setForm]           = useState<CropForm>(DEFAULT_FORM);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState<CropRecommendationResponse | null>(null);

  // Geolocation + live weather state
  const [locating, setLocating]   = useState(false);      // browser geo lookup running
  const [weatherFetching, setWeatherFetching] = useState(false); // OWM call running
  const [liveWeatherOk, setLiveWeatherOk]     = useState<boolean | null>(null);
  // null = not tried, true = success, false = no OWM key / error

  /** ------------------------------------------------------------------
   *  Step 1: Ask the browser for the user's GPS coordinates.
   *  Step 2: Send lat/lon to the backend live-weather endpoint.
   *  Step 3: Auto-fill temperature, humidity, rainfall, city name.
   * ------------------------------------------------------------------ */
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser.');
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        setLocating(false);
        const { latitude, longitude } = pos.coords;

        toast.success(`Location detected: ${latitude.toFixed(3)}, ${longitude.toFixed(3)}`);
        setWeatherFetching(true);

        try {
          const weather = await cropService.getLiveWeather(latitude, longitude);
          setWeatherFetching(false);

          if (weather === null) {
            // 501 — OWM key not configured
            setLiveWeatherOk(false);
            toast(
              'Live weather auto-fill is not configured.\n' +
              'Set OPENWEATHER_API_KEY in backend .env to enable it.\n' +
              'You can adjust sliders manually.',
              { icon: '⚙️', duration: 6000 }
            );
          } else {
            setLiveWeatherOk(true);
            setForm((prev) => ({
              ...prev,
              temperature: weather.temperature,
              humidity:    weather.humidity,
              rainfall:    Math.min(weather.rainfall * 30, 500), // 1-hour rain → monthly est.
              location:    weather.city,
            }));
            toast.success(
              `Weather fetched for ${weather.city}: ` +
              `${weather.temperature}°C, ${weather.humidity}% RH — sliders updated!`,
              { duration: 5000 }
            );
          }
        } catch (err: any) {
          setWeatherFetching(false);
          setLiveWeatherOk(false);
          toast.error('Could not fetch weather data. Please set sliders manually.');
        }
      },
      (err) => {
        setLocating(false);
        if (err.code === err.PERMISSION_DENIED) {
          toast.error('Location permission denied. Please allow location access and try again.');
        } else {
          toast.error(`Geolocation error: ${err.message}`);
        }
      },
      { enableHighAccuracy: false, timeout: 10_000 }
    );
  };

  const handlePredict = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await cropService.recommend(form);
      setResult(res);
      toast.success(`Recommended: ${res.top_recommendation}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Recommendation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!result) return;
    try {
      const blob = await cropService.downloadReport(result.prediction_id);
      downloadBlob(blob, `crop_report_${result.prediction_id}.pdf`);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Failed to download report');
    }
  };

  // Slider definitions
  const sliders = [
    { key: 'nitrogen',    label: 'Nitrogen (N)',    unit: 'kg/ha', min: 0,   max: 200, step: 1,   icon: '🌱', color: 'accent-green-600' },
    { key: 'phosphorus',  label: 'Phosphorus (P)',  unit: 'kg/ha', min: 0,   max: 200, step: 1,   icon: '🧪', color: 'accent-orange-500' },
    { key: 'potassium',   label: 'Potassium (K)',   unit: 'kg/ha', min: 0,   max: 200, step: 1,   icon: '⚗️', color: 'accent-purple-500' },
    { key: 'temperature', label: 'Temperature',     unit: '°C',    min: -20, max: 60,  step: 0.5, icon: '🌡️', color: 'accent-red-500',
      liveIcon: <Thermometer className="w-3.5 h-3.5 text-orange-500" /> },
    { key: 'humidity',    label: 'Humidity',        unit: '%',     min: 0,   max: 100, step: 1,   icon: '💧', color: 'accent-blue-500',
      liveIcon: <Droplets className="w-3.5 h-3.5 text-blue-500" /> },
    { key: 'ph',          label: 'Soil pH',         unit: '',      min: 0,   max: 14,  step: 0.1, icon: '📊', color: 'accent-amber-500' },
    { key: 'rainfall',    label: 'Rainfall',        unit: 'mm',    min: 0,   max: 500, step: 1,   icon: '🌧️', color: 'accent-cyan-500',
      liveIcon: <CloudRain className="w-3.5 h-3.5 text-cyan-500" /> },
  ] as const;

  const isLocatingOrFetching = locating || weatherFetching;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Brain className="w-7 h-7 text-primary-600" /> AI Crop Recommendation
        </h1>
        <p className="text-gray-500 mt-1">
          Get AI-powered crop suggestions based on your soil parameters and live climate data
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* ── Input form ─────────────────────────────────────────────────── */}
        <div className="card space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-white">Soil &amp; Climate Parameters</h2>

            {/* Live weather status badge */}
            {liveWeatherOk === true && (
              <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                <Wifi className="w-3 h-3" /> Live weather applied
              </span>
            )}
            {liveWeatherOk === false && (
              <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                <WifiOff className="w-3 h-3" /> Manual mode
              </span>
            )}
          </div>

          {/* ── Location + detect button ─── */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Location
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="input-field pl-11"
                  placeholder="Type a city, or click Detect →"
                />
              </div>
              {/* Detect my location */}
              <button
                onClick={handleDetectLocation}
                disabled={isLocatingOrFetching}
                title="Detect my location and fetch live weather"
                className={`inline-flex items-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all disabled:opacity-60 ${
                  isLocatingOrFetching
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 cursor-not-allowed'
                    : 'bg-primary text-white hover:bg-primary-700 shadow hover:shadow-lg'
                }`}
              >
                {isLocatingOrFetching ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Navigation className="w-4 h-4" />
                )}
                {locating ? 'Locating…' : weatherFetching ? 'Fetching…' : 'Detect'}
              </button>
            </div>

            {/* Informational note about live weather */}
            <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              Click <strong>Detect</strong> to auto-fill Temperature, Humidity &amp; Rainfall with live data
              {liveWeatherOk === false && ' — add OPENWEATHER_API_KEY in .env to enable'}.
            </p>
          </div>

          {/* ── Parameter sliders ─── */}
          {sliders.map((field) => {
            const val = form[field.key as keyof CropForm] as number;
            const isLiveFilled = liveWeatherOk === true &&
              ['temperature', 'humidity', 'rainfall'].includes(field.key);
            return (
              <div key={field.key}>
                <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  <span className="flex items-center gap-1.5">
                    <span>{field.icon}</span>
                    <span>{field.label}</span>
                    {/* Live data indicator badge */}
                    {isLiveFilled && (
                      <span className="inline-flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        {(field as any).liveIcon}
                        live
                      </span>
                    )}
                  </span>
                  <span className="text-primary-600 font-bold tabular-nums">
                    {val.toFixed(field.key === 'ph' ? 1 : 0)}
                    {field.unit && ` ${field.unit}`}
                  </span>
                </label>
                <input
                  type="range"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={val}
                  onChange={(e) =>
                    setForm({ ...form, [field.key]: parseFloat(e.target.value) })
                  }
                  className={`w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none cursor-pointer ${
                    isLiveFilled ? 'accent-blue-500' : 'accent-primary'
                  }`}
                />
              </div>
            );
          })}

          {/* ── Soil type ─── */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Soil Type
            </label>
            <div className="flex flex-wrap gap-2">
              {SOIL_TYPES.map((soil) => (
                <button
                  key={soil}
                  onClick={() => setForm({ ...form, soil_type: soil })}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    form.soil_type === soil
                      ? 'bg-primary text-white shadow-md'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  {soil}
                </button>
              ))}
            </div>
          </div>

          {/* ── Submit ─── */}
          <button
            onClick={handlePredict}
            disabled={loading}
            className="btn-primary w-full disabled:opacity-60"
          >
            {loading ? (
              <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Analysing…</>
            ) : (
              <><Brain className="w-5 h-5 mr-2" /> Get Recommendations</>
            )}
          </button>
        </div>

        {/* ── Results panel ──────────────────────────────────────────────── */}
        <div>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Top recommendation hero card */}
                <div className="card bg-gradient-to-br from-primary-50 to-green-50 dark:from-primary-900/20 dark:to-green-900/20 border-2 border-primary-200 dark:border-primary-800">
                  <div className="text-center">
                    <div className="text-4xl mb-2">🏆</div>
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      Top Recommendation
                    </div>
                    <div className="text-2xl font-bold text-primary-700 dark:text-primary-300">
                      {result.top_recommendation}
                    </div>
                    {form.location && (
                      <div className="text-sm text-gray-500 mt-1 flex items-center justify-center gap-1">
                        <MapPin className="w-3.5 h-3.5" /> {form.location}
                      </div>
                    )}
                  </div>
                </div>

                {/* Individual crop cards */}
                {result.recommendations.map((rec, idx) => (
                  <motion.div
                    key={rec.crop}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.08 }}
                    className="card"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          idx === 0 ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-gray-100 dark:bg-gray-700'
                        }`}>
                          <Sprout className={`w-5 h-5 ${idx === 0 ? 'text-amber-600' : 'text-gray-500'}`} />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-900 dark:text-white">{rec.crop}</h3>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            rec.suitability === 'Excellent'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : rec.suitability === 'Good'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                              : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                          }`}>
                            {rec.suitability}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-primary-600">
                          {(rec.confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-400">confidence</div>
                      </div>
                    </div>

                    <p className="text-sm text-gray-500 mb-3">{rec.description}</p>

                    <div className="grid sm:grid-cols-2 gap-3">
                      <div>
                        <div className="flex items-center gap-1 text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          <TrendingUp className="w-3 h-3" /> Farming Tips
                        </div>
                        <ul className="text-xs text-gray-500 space-y-0.5">
                          {rec.farming_tips.slice(0, 3).map((tip, i) => (
                            <li key={i}>• {tip}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="flex items-center gap-1 text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          <Beaker className="w-3 h-3" /> Fertiliser Dosage
                        </div>
                        <ul className="text-xs text-gray-500 space-y-0.5">
                          {rec.fertilizer_suggestions.map((f, i) => (
                            <li key={i}>• {f}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Soil information */}
                <div className="card">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Leaf className="w-5 h-5 text-primary-500" /> Soil Information
                  </h3>
                  <p className="text-sm text-gray-500 mb-2">{result.soil_info.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {result.soil_info.characteristics.map((c: string, i: number) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>

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
                <Sprout className="w-16 h-16 text-gray-300" />
                <div>
                  <p className="text-gray-500 font-medium">No recommendation yet</p>
                  <p className="text-gray-400 text-sm mt-1">
                    Optionally click <strong>Detect</strong> to auto-fill live weather, then
                    adjust sliders and click <strong>Get Recommendations</strong>.
                  </p>
                </div>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                  <div className="flex items-center gap-1.5">
                    <Navigation className="w-4 h-4 text-primary-400" />
                    <span>GPS detection</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Thermometer className="w-4 h-4 text-orange-400" />
                    <span>Live weather</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-4 h-4 text-primary-400" />
                    <span>ML model</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
