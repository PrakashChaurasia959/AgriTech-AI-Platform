import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, ScanEye, Loader2, CheckCircle2, AlertTriangle,
  Download, X, Info, Shield, FlaskConical, Cpu, Zap, ChevronRight,
} from "lucide-react";
import toast from "react-hot-toast";
import { diseaseService } from "../services/disease.service";
import type { DiseasePrediction, DiseaseModelInfo } from "../types";
import { downloadBlob } from "../utils";
import { usePageTitle } from "../hooks/usePageTitle";

const CROPS = [
  {v:"",l:"Auto-detect",i:"🔍"},{v:"Tomato",l:"Tomato",i:"🍅"},{v:"Potato",l:"Potato",i:"🥔"},
  {v:"Corn",l:"Corn",i:"🌽"},{v:"Apple",l:"Apple",i:"🍎"},{v:"Grape",l:"Grape",i:"🍇"},
  {v:"Pepper",l:"Pepper",i:"🫑"},{v:"Peach",l:"Peach",i:"🍑"},{v:"Cherry",l:"Cherry",i:"🍒"},
  {v:"Strawberry",l:"Strawberry",i:"🍓"},{v:"Squash",l:"Squash",i:"🎃"},
];
const ALLOWED = ["image/jpeg","image/jpg","image/png","image/webp"];

export default function DiseaseDetection() {
  usePageTitle("Disease Detection");
  const [file, setFile] = useState<File|null>(null);
  const [preview, setPreview] = useState("");
  const [crop, setCrop] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiseasePrediction|null>(null);
  const [drag, setDrag] = useState(false);
  const [modelInfo, setModelInfo] = useState<DiseaseModelInfo|null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    diseaseService.getModelInfo().then(setModelInfo).catch(() => {});
  }, []);

  const handleFile = useCallback((f: File) => {
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (!ALLOWED.includes(f.type) || ![".jpg",".jpeg",".png",".webp"].includes(ext)) {
      toast.error(`Invalid file "${ext}". Use JPG, PNG or WEBP.`);
      return;
    }
    if (f.size > 10*1024*1024) { toast.error("File too large (max 10 MB)"); return; }
    setFile(f);
    const r = new FileReader();
    r.onload = e => setPreview(e.target?.result as string);
    r.readAsDataURL(f);
    setResult(null);
  }, []);

  const handlePredict = async () => {
    if (!file) { toast.error("Upload an image first"); return; }
    setLoading(true); setResult(null);
    try {
      const res = await diseaseService.predict(file, crop);
      setResult(res);
      toast.success(res.is_healthy ? "✅ Plant is healthy!" : `⚠ ${res.disease_name} detected`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Prediction failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ScanEye className="w-6 h-6 text-primary-600" /> AI Disease Detection
          </h1>
          <p className="text-sm text-gray-500 mt-1">Upload a plant leaf photo for instant AI diagnosis</p>
        </div>
        {modelInfo && (
          <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold ${
            modelInfo.model_loaded
              ? "bg-primary-50 border-primary-200 text-primary-700 dark:bg-primary-900/20 dark:border-primary-800 dark:text-primary-300"
              : "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-300"}`}>
            <Cpu className="w-3.5 h-3.5" />
            {modelInfo.model_loaded ? `CNN Active · ${modelInfo.num_classes} classes · ${modelInfo.input_size}px` : "Demo Mode"}
          </div>
        )}
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Upload */}
        <motion.div initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:0.1}} className="card p-5 space-y-4">
          <h2 className="font-bold text-gray-900 dark:text-white text-[15px]">Upload Leaf Image</h2>

          {/* Crop selector */}
          <div>
            <p className="input-label">Crop Type <span className="text-gray-400 font-normal">(optional)</span></p>
            <div className="flex flex-wrap gap-1.5">
              {CROPS.map(c => (
                <button key={c.v} onClick={() => setCrop(c.v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    crop === c.v
                      ? "bg-primary-600 text-white shadow-glow-sm"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/20"}`}>
                  {c.i} {c.l}
                </button>
              ))}
            </div>
          </div>

          {/* Drop zone */}
          {!preview ? (
            <div onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)}
              onDrop={e=>{e.preventDefault();setDrag(false);e.dataTransfer.files[0]&&handleFile(e.dataTransfer.files[0])}}
              onClick={()=>inputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed py-12 cursor-pointer transition-all duration-200 ${
                drag ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[0.99]"
                     : "border-gray-200 dark:border-gray-700 hover:border-primary-400 hover:bg-primary-50/50 dark:hover:bg-primary-900/10"}`}>
              <div className="w-14 h-14 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-3">
                <Upload className="w-6 h-6 text-primary-600" />
              </div>
              <p className="font-semibold text-gray-700 dark:text-gray-300 text-sm">Drop your leaf image here</p>
              <p className="text-xs text-gray-400 mt-1">or click to browse</p>
              <p className="text-[11px] text-gray-400 mt-3 px-4 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700">JPG · PNG · WEBP · Max 10 MB</p>
            </div>
          ) : (
            <div className="relative rounded-2xl overflow-hidden group">
              <img src={preview} alt="Preview" className="w-full h-56 object-contain bg-gray-50 dark:bg-gray-700" />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
              <button onClick={()=>{setFile(null);setPreview("");setResult(null);if(inputRef.current)inputRef.current.value="";}}
                className="absolute top-2 right-2 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg transition-colors">
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-2 left-2 right-2">
                <div className="bg-black/60 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-lg truncate">{file?.name}</div>
              </div>
            </div>
          )}

          <input ref={inputRef} type="file" accept="image/*" className="hidden"
            onChange={e=>e.target.files?.[0]&&handleFile(e.target.files[0])} />

          {preview && (
            <button onClick={handlePredict} disabled={loading}
              className="btn-primary w-full disabled:opacity-60">
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Analysing with CNN...</>
                : <><ScanEye className="w-4 h-4" /> Detect Disease</>}
            </button>
          )}

          {loading && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-primary-50 dark:bg-primary-900/20">
              <div className="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-800 flex items-center justify-center">
                <Zap className="w-4 h-4 text-primary-600 animate-pulse" />
              </div>
              <div>
                <p className="text-xs font-bold text-primary-700 dark:text-primary-300">CNN Processing...</p>
                <p className="text-[11px] text-primary-600/70">AgriVision CNN · 38 classes · 256px</p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Results */}
        <motion.div initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} transition={{delay:0.15}}>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div key="result" initial={{opacity:0,scale:0.97}} animate={{opacity:1,scale:1}} className="space-y-4">
                {/* Status card */}
                <div className={`card p-5 border-2 ${
                  result.is_healthy ? "border-primary-300 bg-gradient-to-br from-primary-50 to-emerald-50 dark:from-primary-900/20 dark:to-emerald-900/20"
                                    : "border-orange-300 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20"}`}>
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg ${
                      result.is_healthy ? "bg-gradient-to-br from-primary-400 to-primary-600" : "bg-gradient-to-br from-orange-400 to-red-500"}`}>
                      {result.is_healthy ? <CheckCircle2 className="w-7 h-7 text-white" /> : <AlertTriangle className="w-7 h-7 text-white" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Diagnosis Result</p>
                      <p className="text-xl font-extrabold text-gray-900 dark:text-white mt-0.5">
                        {result.is_healthy ? "Healthy Plant" : result.disease_name}
                      </p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className={`badge ${result.is_healthy ? "badge-green" : "badge-red"}`}>
                          {result.crop_type}
                        </span>
                        <span className="text-xs text-gray-500">{(result.confidence*100).toFixed(1)}% confidence</span>
                        {!result.is_demo_mode && <span className="badge badge-blue"><Cpu className="w-2.5 h-2.5" /> CNN</span>}
                      </div>
                    </div>
                  </div>
                  {/* Confidence bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Confidence</span><span className="font-bold">{(result.confidence*100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <motion.div initial={{width:0}} animate={{width:`${result.confidence*100}%`}} transition={{duration:0.8,ease:"easeOut"}}
                        className={`h-full rounded-full ${result.is_healthy ? "bg-primary-500" : "bg-orange-500"}`} />
                    </div>
                  </div>
                </div>

                {!result.is_healthy && (<>
                  <div className="card p-4 space-y-2">
                    <h3 className="text-[13px] font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-orange-500" /> Symptoms
                    </h3>
                    <ul className="space-y-1">
                      {result.symptoms.map((s,i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1.5 flex-shrink-0" />{s}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="card p-4 space-y-2">
                    <h3 className="text-[13px] font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <FlaskConical className="w-4 h-4 text-blue-500" /> Treatment
                    </h3>
                    <ul className="space-y-1">
                      {result.treatment.map((t,i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300">
                          <CheckCircle2 className="w-3.5 h-3.5 text-primary-500 mt-0.5 flex-shrink-0" />{t}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="card p-4 space-y-2">
                    <h3 className="text-[13px] font-bold text-gray-900 dark:text-white flex items-center gap-2">
                      <Shield className="w-4 h-4 text-purple-500" /> Prevention
                    </h3>
                    <ul className="space-y-1">
                      {result.prevention.map((p,i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300">
                          <ChevronRight className="w-3.5 h-3.5 text-purple-400 mt-0.5 flex-shrink-0" />{p}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>)}

                <button onClick={async()=>{
                  try{const b=await diseaseService.downloadReport(result.prediction_id);downloadBlob(b,`report_${result.prediction_id}.pdf`);toast.success("Report downloaded!");}
                  catch{toast.error("Download failed");}
                }} className="btn-primary w-full">
                  <Download className="w-4 h-4" /> Download PDF Report
                </button>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{opacity:0}} animate={{opacity:1}}
                className="card p-8 h-full min-h-[400px] flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary-100 to-emerald-100 dark:from-primary-900/30 dark:to-emerald-900/30 flex items-center justify-center mb-4 animate-float">
                  <ScanEye className="w-9 h-9 text-primary-500" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white text-base mb-1">Ready to Diagnose</h3>
                <p className="text-sm text-gray-400 max-w-xs">Upload a clear leaf photo and click "Detect Disease" to get an instant AI diagnosis.</p>
                <div className="mt-6 grid grid-cols-5 gap-3">
                  {CROPS.slice(1,6).map(c=>(
                    <div key={c.v} className="flex flex-col items-center gap-1">
                      <div className="text-2xl">{c.i}</div>
                      <span className="text-[10px] text-gray-400">{c.l}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}

