import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, Loader2, Download, Info, MapPin, Wheat,
  CloudRain, Thermometer, FlaskConical, CheckCircle2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { yieldService } from '../services/yield.service';
import type { YieldPredictionResponse, YieldOptions } from '../types';
import { downloadBlob } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

export default function YieldPrediction() {
  usePageTitle('Yield Prediction');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<YieldPredictionResponse | null>(null);
  const [options, setOptions] = useState<YieldOptions | null>(null);
  const [form, setForm] = useState({
    crop_type: 'Rice', state: 'Punjab', season: 'Kharif',
    area: 1.0, rainfall: 1000, temperature: 25, soil_type: 'Loamy', fertilizer_usage: 100,
  });

  useEffect(() => {
    yieldService.getOptions().then(setOptions).catch(() => {});
  }, []);

  const handlePredict = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await yieldService.predict(form);
      setResult(res);
      toast.success('Yield predicted!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!result) return;
    try {
      const blob = await yieldService.downloadReport(result.prediction_id);
      downloadBlob(blob, `yield_report_${result.prediction_id}.pdf`);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Failed to download report');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <TrendingUp className="w-7 h-7 text-primary-600" /> AI Yield Prediction
        </h1>
        <p className="text-gray-500 mt-1">Predict crop yields based on farming parameters using machine learning</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="card">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Farming Parameters</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Crop Type</label>
              <select
                value={form.crop_type}
                onChange={(e) => setForm({ ...form, crop_type: e.target.value })}
                className="input-field"
              >
                {(options?.crops || ['Rice', 'Wheat', 'Maize', 'Cotton', 'Sugarcane', 'Potato', 'Tomato', 'Soybean']).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">State / Region</label>
                <select value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} className="input-field">
                  {(options?.states || ['Punjab', 'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'West Bengal']).map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Season</label>
                <select value={form.season} onChange={(e) => setForm({ ...form, season: e.target.value })} className="input-field">
                  {(options?.seasons || ['Kharif', 'Rabi', 'Summer', 'Whole Year']).map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                <span>Area (hectares)</span>
                <span className="text-primary-600 font-bold">{form.area} ha</span>
              </label>
              <input type="range" min="0.5" max="100" step="0.5" value={form.area}
                onChange={(e) => setForm({ ...form, area: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none cursor-pointer accent-primary" />
            </div>

            <div>
              <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                <span>🌧️ Rainfall (mm)</span>
                <span className="text-primary-600 font-bold">{form.rainfall} mm</span>
              </label>
              <input type="range" min="0" max="3000" step="50" value={form.rainfall}
                onChange={(e) => setForm({ ...form, rainfall: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none cursor-pointer accent-primary" />
            </div>

            <div>
              <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                <span>🌡️ Temperature (°C)</span>
                <span className="text-primary-600 font-bold">{form.temperature}°C</span>
              </label>
              <input type="range" min="0" max="45" step="0.5" value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none cursor-pointer accent-primary" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Soil Type</label>
              <select value={form.soil_type} onChange={(e) => setForm({ ...form, soil_type: e.target.value })} className="input-field">
                {(options?.soil_types || ['Loamy', 'Sandy', 'Clayey', 'Black', 'Red', 'Alluvial', 'Laterite']).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                <span>🧪 Fertilizer Usage (kg/ha)</span>
                <span className="text-primary-600 font-bold">{form.fertilizer_usage}</span>
              </label>
              <input type="range" min="0" max="300" step="10" value={form.fertilizer_usage}
                onChange={(e) => setForm({ ...form, fertilizer_usage: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full appearance-none cursor-pointer accent-primary" />
            </div>

            <button onClick={handlePredict} disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Predicting...</>
              ) : (
                <><TrendingUp className="w-5 h-5 mr-2" /> Predict Yield</>
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        <div>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {/* Main result */}
                <div className="card bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-2 border-primary-200 dark:border-primary-800">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Predicted Yield</div>
                      <div className="text-3xl font-bold text-primary-700 dark:text-primary-300">
                        {result.predicted_yield.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-500">{result.yield_unit}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Production</div>
                      <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                        {(result.predicted_production / 1000).toFixed(1)}k
                      </div>
                      <div className="text-sm text-gray-500">kg (est.)</div>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-center gap-2">
                    <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
                      result.suitability === 'Excellent' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      result.suitability === 'Good' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                      result.suitability === 'Fair' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                      'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    }`}>
                      {result.suitability} suitability
                    </span>
                  </div>
                </div>

                {/* Conditions */}
                <div className="card">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Conditions Summary</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">{result.conditions_summary}</p>
                </div>

                {/* Improvement suggestions */}
                <div className="card">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Info className="w-5 h-5 text-blue-500" /> Improvement Suggestions
                  </h3>
                  <ul className="space-y-2">
                    {result.improvement_suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                        <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Estimate disclaimer */}
                <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
                  <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-700 dark:text-amber-400">
                    This is an AI-generated estimate based on historical data and current parameters.
                    Actual yields may vary due to weather, pest pressure, and management practices.
                  </p>
                </div>

                <button onClick={handleDownload} className="btn-primary w-full">
                  <Download className="w-5 h-5 mr-2" /> Download PDF Report
                </button>
              </motion.div>
            ) : (
              <motion.div key="placeholder" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="card h-full flex flex-col items-center justify-center text-center min-h-[300px]">
                <Wheat className="w-16 h-16 text-gray-300 mb-4" />
                <p className="text-gray-400">
                  Set your farming parameters and click "Predict Yield" to get an AI-powered estimate
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
