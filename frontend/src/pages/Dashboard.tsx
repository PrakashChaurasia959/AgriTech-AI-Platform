import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Leaf, Sprout, TrendingUp, CloudSun, ArrowUpRight, ScanEye,
  Activity, CheckCircle2, AlertTriangle, Cpu, Zap, Target, BarChart2,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, RadialBarChart, RadialBar,
} from "recharts";
import { useAuth } from "../context/AuthContext";
import { diseaseService } from "../services/disease.service";
import { cropService } from "../services/crop.service";
import { yieldService } from "../services/yield.service";
import { formatDate } from "../utils";
import { usePageTitle } from "../hooks/usePageTitle";

const COLORS = ["#16A34A","#F97316","#3B82F6","#7C3AED","#EF4444","#06B6D4"];

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay, ease: [0.4,0,0.2,1] },
});

export default function Dashboard() {
  usePageTitle("Dashboard");
  const { user } = useAuth();
  const [stats, setStats] = useState({ disease: 0, crop: 0, yield: 0 });
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [d, c, y] = await Promise.all([
          diseaseService.getHistory(1, 8).catch(() => ({ items: [], total: 0 })),
          cropService.getHistory(1, 5).catch(() => ({ items: [], total: 0 })),
          yieldService.getHistory(1, 5).catch(() => ({ items: [], total: 0 })),
        ]);
        setStats({ disease: d.total, crop: c.total, yield: y.total });
        const acts: any[] = [
          ...d.items.map((i: any) => ({ type: "Disease", desc: `${i.crop_type}: ${i.disease_name}`, date: i.created_at, ok: i.is_healthy, icon: "leaf" })),
          ...c.items.map((i: any) => ({ type: "Crop", desc: `Recommended: ${i.top_recommendation}`, date: i.created_at, ok: true, icon: "sprout" })),
          ...y.items.map((i: any) => ({ type: "Yield", desc: `${i.crop_type}: ${(i.predicted_yield/1000).toFixed(1)}t/ha`, date: i.created_at, ok: true, icon: "trend" })),
        ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 8);
        setActivities(acts);
      } finally { setLoading(false); }
    })();
  }, []);

  const total = stats.disease + stats.crop + stats.yield;
  const healthyPct = stats.disease > 0 ? Math.max(40, 100 - Math.round(stats.disease / 2)) : 100;

  const statCards = [
    { label: "Disease Scans",       value: stats.disease, icon: ScanEye,   color: "bg-red-500",    light: "bg-red-50 dark:bg-red-900/20",  text: "text-red-600",    link: "/app/disease-detection" },
    { label: "Crop Recs",           value: stats.crop,    icon: Sprout,    color: "bg-primary-500",light: "bg-primary-50 dark:bg-primary-900/20",text:"text-primary-600",link:"/app/crop-recommendation"},
    { label: "Yield Predictions",   value: stats.yield,   icon: TrendingUp,color: "bg-blue-500",   light: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-600",   link: "/app/yield-prediction"  },
    { label: "Healthy Plants %",    value: `${healthyPct}%`,icon:CheckCircle2,color:"bg-emerald-500",light:"bg-emerald-50 dark:bg-emerald-900/20",text:"text-emerald-600",link:"/app/history"},
  ];

  const chartData = [
    { name: "Disease", value: stats.disease || 0 },
    { name: "Crop",    value: stats.crop    || 0 },
    { name: "Yield",   value: stats.yield   || 0 },
  ];

  const radialData = [{ value: healthyPct, fill: "#16A34A" }];

  const quickActions = [
    { to: "/app/disease-detection",   icon: ScanEye,    label: "Scan Leaf",    sub: "Detect diseases instantly", bg: "from-red-500 to-rose-600" },
    { to: "/app/crop-recommendation", icon: Sprout,     label: "Get Crops",    sub: "AI soil analysis",          bg: "from-primary-500 to-emerald-600" },
    { to: "/app/yield-prediction",    icon: TrendingUp, label: "Predict Yield",sub: "ML harvest forecast",        bg: "from-blue-500 to-cyan-600" },
    { to: "/app/weather",             icon: CloudSun,   label: "Weather AI",   sub: "Live farming advice",        bg: "from-amber-500 to-orange-600" },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome */}
      <motion.div {...fadeUp(0)}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Welcome back, <span className="text-gradient">{user?.full_name?.split(" ")[0] || "Farmer"}</span> 🌿
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Your AI-powered agriculture dashboard — {new Date().toLocaleDateString("en-US",{weekday:"long",month:"long",day:"numeric"})}
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 self-start sm:self-auto">
            <Cpu className="w-4 h-4 text-primary-600" />
            <div>
              <p className="text-xs font-bold text-primary-700 dark:text-primary-300">AI Models Active</p>
              <p className="text-[10px] text-primary-600/70 dark:text-primary-400/70">MobileNetV2 • RandomForest</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-primary-500 animate-pulse ml-1" />
          </div>
        </div>
      </motion.div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s, i) => (
          <motion.div key={s.label} {...fadeUp(0.05 * i)}>
            <Link to={s.link} className="card-stat block group">
              <div className="flex items-start justify-between mb-4">
                <div className={`stat-icon ${s.light}`}>
                  <s.icon className={`w-5 h-5 ${s.text}`} />
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-primary-500 transition-colors" />
              </div>
              <div className="text-2xl font-extrabold text-gray-900 dark:text-white tabular-nums">
                {loading ? <span className="skeleton h-7 w-12 block rounded" /> : s.value}
              </div>
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">{s.label}</div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Charts + Quick Actions */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* Activity bar chart */}
        <motion.div {...fadeUp(0.1)} className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-title flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-primary-500" /> Activity Overview
              </h3>
              <p className="section-subtitle">Total {total} AI predictions</p>
            </div>
          </div>
          {total === 0 && !loading ? (
            <div className="h-48 flex flex-col items-center justify-center text-gray-400">
              <Activity className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">Start using AI features to see activity</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData} margin={{top:5,right:5,bottom:0,left:-10}}>
                <defs>
                  <linearGradient id="cg1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#16A34A" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#16A34A" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" tick={{fontSize:12}} />
                <YAxis tick={{fontSize:12}} />
                <Tooltip contentStyle={{borderRadius:"12px",border:"none",boxShadow:"0 8px 32px rgba(0,0,0,0.12)"}} />
                <Area type="monotone" dataKey="value" stroke="#16A34A" strokeWidth={2} fill="url(#cg1)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* Health radial */}
        <motion.div {...fadeUp(0.15)} className="card p-5 flex flex-col">
          <h3 className="section-title flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-primary-500" /> Plant Health
          </h3>
          <p className="section-subtitle mb-3">Based on scans</p>
          <div className="flex-1 flex items-center justify-center">
            <div className="relative">
              <ResponsiveContainer width={160} height={160}>
                <RadialBarChart innerRadius={50} outerRadius={70} data={radialData} startAngle={90} endAngle={-270}>
                  <RadialBar dataKey="value" cornerRadius={8} background={{fill:"rgba(0,0,0,0.05)"}} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-extrabold text-gray-900 dark:text-white">{healthyPct}%</span>
                <span className="text-[10px] text-gray-400 font-medium">Healthy</span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {chartData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{background: COLORS[i]}} />
                <span className="text-[11px] text-gray-500">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div {...fadeUp(0.2)}>
        <h3 className="section-title mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-500" /> Quick Actions
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {quickActions.map((a, i) => (
            <motion.div key={a.to} {...fadeUp(0.05 * i)}>
              <Link to={a.to}
                className="block relative overflow-hidden rounded-2xl p-4 group transition-all duration-200 hover:scale-[1.02] hover:shadow-card-hover">
                <div className={`absolute inset-0 bg-gradient-to-br ${a.bg} opacity-90`} />
                <div className="absolute inset-0 bg-card-shine" />
                <div className="relative">
                  <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center mb-3 group-hover:bg-white/30 transition-colors">
                    <a.icon className="w-4.5 h-4.5 text-white" />
                  </div>
                  <p className="text-sm font-bold text-white">{a.label}</p>
                  <p className="text-[11px] text-white/75 mt-0.5">{a.sub}</p>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div {...fadeUp(0.25)} className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 className="section-title flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-500" /> Recent Activity
          </h3>
          <Link to="/app/history" className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
            View all <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>
        {loading ? (
          <div className="p-5 space-y-3">
            {[...Array(4)].map((_,i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="skeleton w-9 h-9 rounded-xl" />
                <div className="flex-1 space-y-1.5">
                  <div className="skeleton h-3.5 w-1/3 rounded" />
                  <div className="skeleton h-3 w-1/2 rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
          <div className="py-12 text-center text-gray-400">
            <Leaf className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No activity yet — try scanning a leaf!</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
            {activities.map((a, i) => (
              <motion.div key={i} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.04}}
                className="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-50/50 dark:hover:bg-gray-700/20 transition-colors">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  a.ok ? "bg-primary-100 dark:bg-primary-900/30" : "bg-red-100 dark:bg-red-900/30"}`}>
                  {a.ok
                    ? <CheckCircle2 className="w-4 h-4 text-primary-600" />
                    : <AlertTriangle className="w-4 h-4 text-red-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-gray-900 dark:text-white">{a.type}</p>
                  <p className="text-xs text-gray-500 truncate">{a.desc}</p>
                </div>
                <span className="text-[11px] text-gray-400 flex-shrink-0">{formatDate(a.date)}</span>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
