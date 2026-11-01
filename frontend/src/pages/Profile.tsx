import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Phone, MapPin, Loader2, Save, Sprout } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { userService } from '../services/user.service';
import { formatDate } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

export default function Profile() {
  usePageTitle('My Profile');
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    mobile_number: user?.mobile_number || '',
    farm_name: user?.farm_name || '',
    location: user?.location || '',
  });

  useEffect(() => {
    if (user) {
      setForm({
        full_name: user.full_name || '',
        mobile_number: user.mobile_number || '',
        farm_name: user.farm_name || '',
        location: user.location || '',
      });
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await userService.updateProfile(form);
      await refreshUser();
      toast.success('Profile updated successfully!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">My Profile</h1>
        <p className="text-gray-500 mt-1">Manage your account information</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Profile card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card text-center">
          <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-4xl font-bold mb-4">
            {user?.full_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">{user?.full_name}</h2>
          <p className="text-sm text-gray-500">{user?.email}</p>
          <span className={`inline-block mt-2 text-xs font-medium px-3 py-1 rounded-full ${
            user?.role === 'admin'
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
              : 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
          }`}>
            {user?.role === 'admin' ? 'Administrator' : 'Farmer'}
          </span>

          <div className="mt-6 space-y-3 text-left">
            <div className="flex items-center gap-3 text-sm">
              <Mail className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600 dark:text-gray-300">{user?.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Phone className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600 dark:text-gray-300">{user?.mobile_number || 'Not set'}</span>
            </div>
            {user?.location && (
              <div className="flex items-center gap-3 text-sm">
                <MapPin className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600 dark:text-gray-300">{user.location}</span>
              </div>
            )}
            <div className="flex items-center gap-3 text-sm">
              <Sprout className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600 dark:text-gray-300">
                {user?.farm_name || 'No farm name set'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <User className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">Member since {formatDate(user?.created_at)}</span>
            </div>
          </div>
        </motion.div>

        {/* Edit form */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="lg:col-span-2 card">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Edit Profile</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="input-field pl-11"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Mobile Number</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="tel"
                  value={form.mobile_number}
                  onChange={(e) => setForm({ ...form, mobile_number: e.target.value })}
                  className="input-field pl-11"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Farm Name (optional)</label>
              <div className="relative">
                <Sprout className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={form.farm_name}
                  onChange={(e) => setForm({ ...form, farm_name: e.target.value })}
                  className="input-field pl-11"
                  placeholder="e.g., Green Valley Farm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Location (optional)</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="input-field pl-11"
                  placeholder="e.g., Punjab, India"
                />
              </div>
            </div>

            <button onClick={handleSave} disabled={loading} className="btn-primary disabled:opacity-60">
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Saving...</>
              ) : (
                <><Save className="w-5 h-5 mr-2" /> Save Changes</>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
