import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users, ScanEye, Sprout, TrendingUp, Activity, Search,
  Power, Shield, BarChart3, UserCircle,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import toast from 'react-hot-toast';
import { adminService } from '../services/admin.service';
import type { AdminDashboard as AdminData, User } from '../types';
import { formatDate } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

export default function AdminDashboard() {
  usePageTitle('Admin Dashboard');
  const [data, setData] = useState<AdminData | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [view, setView] = useState<'overview' | 'users'>('overview');

  const loadData = async () => {
    setLoading(true);
    try {
      const dash = await adminService.getDashboard();
      setData(dash);
      const usersRes = await adminService.getUsers(1, 50, search);
      setUsers(usersRes.items);
    } catch {
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      adminService.getUsers(1, 50, search).then(res => setUsers(res.items)).catch(() => {});
    }, 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const handleToggle = async (userId: string) => {
    try {
      await adminService.toggleUserStatus(userId);
      toast.success('User status updated');
      loadData();
    } catch {
      toast.error('Failed to update user status');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary" />
      </div>
    );
  }

  const stats = [
    { label: 'Total Users', value: data?.stats.total_users || 0, icon: Users, color: 'bg-blue-500' },
    { label: 'Disease Detections', value: data?.stats.total_disease_detections || 0, icon: ScanEye, color: 'bg-green-500' },
    { label: 'Crop Recommendations', value: data?.stats.total_crop_recommendations || 0, icon: Sprout, color: 'bg-amber-500' },
    { label: 'Yield Predictions', value: data?.stats.total_yield_predictions || 0, icon: TrendingUp, color: 'bg-purple-500' },
  ];

  const chartData = (data?.disease_by_crop || []).map(d => ({ name: d.crop, count: d.count }));
  const chartColors = ['#16A34A', '#F97316', '#3B82F6', '#A855F7', '#EF4444', '#14B8A6', '#EAB308', '#EC4899'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Shield className="w-7 h-7 text-purple-600" /> Admin Dashboard
          </h1>
          <p className="text-gray-500 mt-1">System overview and user management</p>
        </div>
      </div>

      {/* View toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setView('overview')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
            view === 'overview' ? 'bg-primary text-white' : 'bg-white dark:bg-gray-800 text-gray-600'
          }`}
        >
          <BarChart3 className="w-5 h-5" /> Overview
        </button>
        <button
          onClick={() => setView('users')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
            view === 'users' ? 'bg-primary text-white' : 'bg-white dark:bg-gray-800 text-gray-600'
          }`}
        >
          <Users className="w-5 h-5" /> User Management
        </button>
      </div>

      {view === 'overview' ? (
        <>
          {/* Stats */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="card"
              >
                <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center mb-3`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
                <div className="text-sm text-gray-500">{stat.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Chart */}
          <div className="card">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Disease Detections by Crop</h3>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    {chartData.map((_, idx) => (
                      <Cell key={idx} fill={chartColors[idx % chartColors.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-400 py-8">No disease detection data yet</p>
            )}
          </div>

          {/* Recent activities */}
          <div className="card">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" /> Recent Activities
            </h3>
            <div className="space-y-2">
              {data?.recent_activities && data.recent_activities.length > 0 ? data.recent_activities.map((act) => (
                <div key={act.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <div className="w-10 h-10 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">{act.user_name}</div>
                    <div className="text-sm text-gray-500 truncate">{act.description}</div>
                  </div>
                  <div className="text-xs text-gray-400">{formatDate(act.created_at)}</div>
                </div>
              )) : (
                <p className="text-center text-gray-400 py-8">No recent activities</p>
              )}
            </div>
          </div>
        </>
      ) : (
        <>
          {/* User search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-11"
              placeholder="Search users by name or email..."
            />
          </div>

          {/* Users table */}
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">User</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Mobile</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Activities</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Joined</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold text-sm">
                            {u.full_name?.[0]?.toUpperCase()}
                          </div>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">{u.full_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{u.email}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{u.mobile_number}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{u.activity_count || 0}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{formatDate(u.created_at)}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                          u.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleToggle(u.id)}
                          className={`p-2 rounded-lg ${
                            u.is_active
                              ? 'hover:bg-red-50 dark:hover:bg-red-900/30 text-red-500'
                              : 'hover:bg-green-50 dark:hover:bg-green-900/30 text-green-500'
                          }`}
                          title={u.is_active ? 'Deactivate' : 'Activate'}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {users.length === 0 && (
              <p className="text-center text-gray-400 py-8">No users found</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
