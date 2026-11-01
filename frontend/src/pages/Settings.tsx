import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Moon, Sun, Lock, Loader2, Save, Bell } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTheme } from '../context/ThemeContext';
import { userService } from '../services/user.service';
import { usePageTitle } from '../hooks/usePageTitle';

export default function Settings() {
  usePageTitle('Settings');
  const { theme, toggleTheme } = useTheme();
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '' });
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async () => {
    if (!passwordForm.current_password || !passwordForm.new_password) {
      toast.error('Please fill in all fields');
      return;
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('New password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      await userService.changePassword(passwordForm.current_password, passwordForm.new_password);
      toast.success('Password changed successfully!');
      setPasswordForm({ current_password: '', new_password: '' });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Password change failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <SettingsIcon className="w-7 h-7 text-primary-600" /> Settings
        </h1>
        <p className="text-gray-500 mt-1">Manage your preferences and security</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Appearance */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Sun className="w-5 h-5 text-amber-500" /> Appearance
          </h2>
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
            <div className="flex items-center gap-3">
              {theme === 'light' ? <Sun className="w-6 h-6 text-amber-500" /> : <Moon className="w-6 h-6 text-blue-400" />}
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
                </div>
                <div className="text-sm text-gray-500">
                  Toggle between light and dark themes
                </div>
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative w-12 h-7 rounded-full transition-colors ${theme === 'dark' ? 'bg-primary' : 'bg-gray-300'}`}
            >
              <div className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${theme === 'dark' ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        </motion.div>

        {/* Change Password */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5 text-red-500" /> Change Password
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Current Password</label>
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                className="input-field"
                placeholder="Enter current password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">New Password</label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="input-field"
                placeholder="Enter new password"
              />
            </div>
            <button onClick={handlePasswordChange} disabled={loading} className="btn-primary disabled:opacity-60">
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Updating...</>
              ) : (
                <><Save className="w-5 h-5 mr-2" /> Update Password</>
              )}
            </button>
          </div>
        </motion.div>

        {/* Notifications (visual only) */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-500" /> Notifications
          </h2>
          <div className="space-y-3">
            <label className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl cursor-pointer">
              <div>
                <div className="font-medium text-gray-900 dark:text-white text-sm">Email Notifications</div>
                <div className="text-xs text-gray-500">Receive updates about your account</div>
              </div>
              <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary" />
            </label>
            <label className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl cursor-pointer">
              <div>
                <div className="font-medium text-gray-900 dark:text-white text-sm">Weather Alerts</div>
                <div className="text-xs text-gray-500">Get notified about severe weather</div>
              </div>
              <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary" />
            </label>
            <label className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl cursor-pointer">
              <div>
                <div className="font-medium text-gray-900 dark:text-white text-sm">Disease Warnings</div>
                <div className="text-xs text-gray-500">Alerts about crop disease risks</div>
              </div>
              <input type="checkbox" className="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary" />
            </label>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
