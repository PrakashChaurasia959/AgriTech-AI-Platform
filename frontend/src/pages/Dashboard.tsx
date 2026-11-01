import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Leaf, Sprout, TrendingUp, CloudSun, ArrowRight,
  ScanEye, Brain, BarChart3, CheckCircle2, Activity,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { diseaseService } from '../services/disease.service';
import { cropService } from '../services/crop.service';
import { yieldService } from '../services/yield.service';
import { formatDate } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

export default function Dashboard() {
  usePageTitle('Dashboard');
  const { user } = useAuth();
  const [stats, setStats] = useState({ disease: 0, crop: 0, yield: 0 });
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [diseaseHist, cropHist, yieldHist] = await Promise.all([
          diseaseService.getHistory(1, 5).catch(() => ({ items: [], total: 0 })),
          cropService.getHistory(1, 5).catch(() => ({ items: [], total: 0 })),
          yieldService.getHistory(1, 5).catch(() => ({ items: [], total: 0 })),
        ]);
        setStats({ disease: diseaseHist.total, crop: cropHist.total, yield: yieldHist.total });

        // Build activities from history
        const activities: any[] = [];
        diseaseHist.items.forEach((item: any) => {
          activities.push({
            type: 'Disease Detection',
            description: `${item.crop_type}: ${item.disease_name} (${(item.confidence * 100).toFixed(0)}%)`,
            date: item.created_at,
            status: item.is_healthy ? 'healthy' : 'diseased',
          });
        });
        cropHist.items.forEach((item: any) => {
          activities.push({
            type: 'Crop Recommendation',
            description: `Recommended: ${item.top_recommendation}`,
            date: item.created_at,
            status: 'recommendation',
          });
        });
        yieldHist.items.forEach((item: any) => {
          activities.push({
            type: 'Yield Prediction',
            description: `${item.crop_type}: ${item.predicted_yield.toFixed(0)} kg/ha`,
            date: item.created_at,
            status: 'prediction',
          });
        });
        activities.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        setRecentActivities(activities.slice(0, 6));
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const healthyCount = recentActivities.filter(a => a.status === 'healthy').length;
  const totalDisease = stats.disease;
  const healthyPct = totalDisease > 0 ? Math.round((healthyCount / Math.max(totalDisease, 1)) * 100) : 100;

  const chartData = [
    { name: 'Disease', value: stats.disease, color: '#16A34A' },
    { name: 'Crop', value: stats.crop, color: '#F97316' },
    { name: 'Yield', value: stats.yield, color: '#3B82F6' },
  ];

  const pieData = [
    { name: 'Healthy', value: healthyPct, color: '#16A34A' },
    { name: 'Diseased', value: 100 - healthyPct, color: '#EF4444' },
  ];

  const quickActions = [
    { to: '/app/disease-detection', icon: ScanEye, title: 'Disease Detection', desc: 'Scan a leaf image', color: 'from-green-500 to-emerald-600' },
    { to: '/app/crop-recommendation', icon: Brain, title: 'Crop Recommendation', desc: 'Get AI suggestions', color: 'from-amber-500 to-orange-600' },
    { to: '/app/yield-prediction', icon: TrendingUp, title: 'Yield Prediction', desc: 'Estimate your harvest', color: 'from-blue-500 to-cyan-600' },
    { to: '/app/weather', icon: CloudSun, title: 'Weather Forecast', desc: 'Check conditions', color: 'from-purple-500 to-indigo-600' },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.full_name?.split(' ')[0] || 'Farmer'}! 🌱
        </h1>
        <p className="text-gray-500 mt-1">Here's an overview of your agricultural activities</p>
      </motion.div>

      {/* Stats cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Disease Scans', value: stats.disease, icon: ScanEye, color: 'bg-green-500' },
          { label: 'Healthy Plant %', value: `${healthyPct}%`, icon: CheckCircle2, color: 'bg-emerald-500' },
          { label: 'Crop Recommendations', value: stats.crop, icon: Sprout, color: 'bg-orange-500' },
          { label: 'Yield Predictions', value: stats.yield, icon: TrendingUp, color: 'bg-blue-500' },
        ].map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
            <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, idx) => (
            <motion.div
              key={action.to}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
            >
              <Link to={action.to} className="card block group hover:-translate-y-1 transition-all">
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <action.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-white mb-1">{action.title}</h3>
                <p className="text-sm text-gray-500">{action.desc}</p>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Activity Overview</h3>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-200 border-t-primary" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {chartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Plant Health Pie */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Plant Health Distribution</h3>
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-200 border-t-primary" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                    {pieData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Activities */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" /> Recent Activities
          </h3>
          <Link to="/app/history" className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            View All <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        {recentActivities.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Leaf className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No activities yet. Start by detecting a crop disease!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentActivities.map((activity, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  activity.status === 'healthy' ? 'bg-green-100 dark:bg-green-900/30' :
                  activity.status === 'diseased' ? 'bg-red-100 dark:bg-red-900/30' :
                  activity.status === 'recommendation' ? 'bg-amber-100 dark:bg-amber-900/30' :
                  'bg-blue-100 dark:bg-blue-900/30'
                }`}>
                  {activity.status === 'healthy' ? <CheckCircle2 className="w-5 h-5 text-green-600" /> :
                   activity.status === 'diseased' ? <Leaf className="w-5 h-5 text-red-600" /> :
                   activity.status === 'recommendation' ? <Sprout className="w-5 h-5 text-amber-600" /> :
                   <TrendingUp className="w-5 h-5 text-blue-600" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{activity.type}</span>
                    <span className="text-xs text-gray-400">{formatDate(activity.date)}</span>
                  </div>
                  <p className="text-sm text-gray-500 truncate">{activity.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
