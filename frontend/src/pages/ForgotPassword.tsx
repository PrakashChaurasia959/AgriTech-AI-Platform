import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, Sprout, Loader2, Copy, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { authService } from '../services/auth.service';
import type { ForgotPasswordResponse } from '../types';

export default function ForgotPassword() {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [result, setResult] = useState<ForgotPasswordResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.error('Please enter your email');
      return;
    }
    setLoading(true);
    try {
      const res = await authService.forgotPassword(email);
      setResult(res);
      toast.success('Reset link generated!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const copyToken = () => {
    if (result?.reset_token) {
      navigator.clipboard.writeText(result.reset_token);
      setCopied(true);
      toast.success('Token copied!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-background to-primary-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="card">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 mb-4">
              <Sprout className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Forgot Password</h1>
            <p className="text-gray-500 mt-1">Enter your email to receive a reset link</p>
          </div>

          {!result ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field pl-11"
                    placeholder="you@example.com"
                    required
                  />
                </div>
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
                {loading ? (
                  <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Sending...</>
                ) : (
                  <>Send Reset Link <ArrowRight className="w-5 h-5 ml-2" /></>
                )}
              </button>
            </form>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-primary-50 dark:bg-primary-900/20 rounded-xl">
                <CheckCircle2 className="w-6 h-6 text-primary-600 flex-shrink-0" />
                <p className="text-sm text-gray-700 dark:text-gray-300">{result.message}</p>
              </div>

              {result.reset_link && (
                <div className="space-y-3">
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
                    <p className="text-xs text-amber-700 dark:text-amber-400 font-medium mb-2">
                      Development Mode — No email service configured
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      Use the link below to reset your password:
                    </p>
                    <div className="flex items-center gap-2">
                      <Link
                        to={result.reset_link}
                        className="text-sm text-primary-600 hover:text-primary-700 font-semibold break-all"
                      >
                        Reset Password Link
                      </Link>
                    </div>
                  </div>
                  {result.reset_token && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                        Reset Token
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          readOnly
                          value={result.reset_token}
                          className="input-field text-xs font-mono"
                        />
                        <button onClick={copyToken} className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-xl hover:bg-gray-200">
                          {copied ? <CheckCircle2 className="w-5 h-5 text-primary-600" /> : <Copy className="w-5 h-5 text-gray-500" />}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          <p className="text-center text-sm text-gray-500 mt-6">
            Remember your password?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-semibold">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
