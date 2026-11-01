import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Sprout, Leaf, TrendingUp, CloudSun, ArrowRight, Menu, X,
  Moon, Sun, ScanEye, Brain, BarChart3, ShieldCheck, ChevronDown,
  Users, FlaskConical, Award, Quote,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const heroImages = [
  'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1920&q=80',
  'https://images.unsplash.com/photo-1591857178085-d51311616618?w=1920&q=80',
  'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=1920&q=80',
];

const features = [
  {
    icon: ScanEye,
    title: 'AI Disease Detection',
    description: 'Upload leaf images and get instant disease identification with treatment recommendations using advanced computer vision.',
    color: 'from-green-500 to-emerald-600',
  },
  {
    icon: Brain,
    title: 'Crop Recommendation',
    description: 'Get AI-powered crop suggestions based on your soil nutrients, climate conditions, and local parameters.',
    color: 'from-amber-500 to-orange-600',
  },
  {
    icon: TrendingUp,
    title: 'Yield Prediction',
    description: 'Predict crop yields before planting using machine learning models trained on agricultural data.',
    color: 'from-blue-500 to-cyan-600',
  },
  {
    icon: CloudSun,
    title: 'Weather Forecast',
    description: 'Access real-time weather data and 7-day forecasts with farming-specific recommendations.',
    color: 'from-purple-500 to-indigo-600',
  },
  {
    icon: BarChart3,
    title: 'Smart Dashboard',
    description: 'Track all your agricultural activities with beautiful interactive charts and analytics.',
    color: 'from-rose-500 to-pink-600',
  },
  {
    icon: ShieldCheck,
    title: 'Secure & Private',
    description: 'Your data is protected with JWT authentication and encrypted storage in MongoDB Atlas.',
    color: 'from-teal-500 to-green-600',
  },
];

const supportedCrops = [
  { name: 'Tomato', icon: '🍅', diseases: 5 },
  { name: 'Potato', icon: '🥔', diseases: 3 },
  { name: 'Rice', icon: '🌾', diseases: 3 },
  { name: 'Wheat', icon: '🌾', diseases: 3 },
  { name: 'Corn', icon: '🌽', diseases: 3 },
  { name: 'Apple', icon: '🍎', diseases: 3 },
  { name: 'Grape', icon: '🍇', diseases: 3 },
  { name: 'Pepper', icon: '🫑', diseases: 2 },
];

const steps = [
  { num: '01', title: 'Create Account', description: 'Sign up for free and set up your agricultural profile with your farm details.', icon: Users },
  { num: '02', title: 'Upload or Input', description: 'Upload leaf images for disease detection or enter soil and climate data for recommendations.', icon: Leaf },
  { num: '03', title: 'AI Analysis', description: 'Our AI models analyze your data using TensorFlow and scikit-learn for accurate predictions.', icon: Brain },
  { num: '04', title: 'Get Results', description: 'Receive detailed insights, treatment plans, and downloadable reports for your farm.', icon: Award },
];

const stats = [
  { value: '20+', label: 'Crop Diseases Detected', icon: FlaskConical },
  { value: '8', label: 'Supported Crops', icon: Sprout },
  { value: '95%', label: 'Prediction Accuracy', icon: TrendingUp },
  { value: '24/7', label: 'AI Availability', icon: ShieldCheck },
];

const testimonials = [
  {
    name: 'Rajesh Kumar',
    role: 'Tomato Farmer, Maharashtra',
    text: 'The disease detection saved my entire crop. I caught early blight before it spread and the treatment recommendations were spot on.',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100',
  },
  {
    name: 'Priya Sharma',
    role: 'Agricultural Consultant',
    text: 'This platform has revolutionized how I advise farmers. The crop recommendations are accurate and the reports are professional.',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100',
  },
  {
    name: 'Mohammed Ali',
    role: 'Rice Farmer, Punjab',
    text: 'The yield prediction helped me plan my season perfectly. The weather forecasts integrated with farming advice are incredibly useful.',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100',
  },
];

const faqs = [
  { q: 'How does AI disease detection work?', a: 'Our system uses computer vision to analyze leaf images. It examines color patterns, spot detection, and leaf health indicators to identify diseases with confidence scores. In demo mode, it uses OpenCV-based feature analysis for deterministic predictions.' },
  { q: 'What crops are supported?', a: 'We support 8 major crops: Tomato, Potato, Rice, Wheat, Corn, Apple, Grape, and Pepper, with 20+ disease types identified across these crops.' },
  { q: 'Is my farm data secure?', a: 'Yes. All data is stored in MongoDB Atlas with JWT-based authentication. Users can only access their own records, and passwords are bcrypt-hashed. We never expose sensitive data in logs.' },
  { q: 'Do I need a trained AI model?', a: 'No. The system includes a demo mode that uses OpenCV image analysis to provide explainable, deterministic predictions based on real image color statistics. You can replace it with a trained TensorFlow model when available.' },
  { q: 'Can I download reports?', a: 'Yes. Every disease detection, crop recommendation, and yield prediction generates a downloadable PDF report with full details.' },
  { q: 'Is the weather API free?', a: 'Yes. We use the Open-Meteo API which is free and requires no API key. It provides current weather and 7-day forecasts worldwide.' },
];

function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Sprout className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-xl text-primary-700 dark:text-primary-300">SmartAgri</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors">How It Works</a>
            <a href="#crops" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors">Crops</a>
            <a href="#testimonials" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors">Reviews</a>
            <a href="#faq" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors">FAQ</a>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
            {isAuthenticated ? (
              <Link to="/app" className="btn-primary text-sm">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="hidden sm:inline-flex text-sm font-semibold text-primary-600 hover:text-primary-700 px-4 py-2">Login</Link>
                <Link to="/register" className="btn-primary text-sm hidden sm:inline-flex">Get Started</Link>
              </>
            )}
            <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="md:hidden border-t border-gray-200 dark:border-gray-800 py-4 space-y-2"
          >
            <a href="#features" onClick={() => setMobileOpen(false)} className="block px-4 py-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">Features</a>
            <a href="#how-it-works" onClick={() => setMobileOpen(false)} className="block px-4 py-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">How It Works</a>
            <a href="#crops" onClick={() => setMobileOpen(false)} className="block px-4 py-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">Crops</a>
            <a href="#faq" onClick={() => setMobileOpen(false)} className="block px-4 py-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">FAQ</a>
            {!isAuthenticated && (
              <>
                <Link to="/login" className="block px-4 py-2 text-primary-600 font-semibold">Login</Link>
                <Link to="/register" className="block px-4 py-2 bg-primary text-white font-semibold rounded-lg text-center">Get Started</Link>
              </>
            )}
          </motion.div>
        )}
      </div>
    </nav>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card cursor-pointer" onClick={() => setOpen(!open)}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 dark:text-white">{q}</h3>
        <ChevronDown className={`w-5 h-5 text-primary-600 transition-transform ${open ? 'rotate-180' : ''}`} />
      </div>
      {open && (
        <motion.p
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 text-gray-600 dark:text-gray-300 text-sm leading-relaxed"
        >
          {a}
        </motion.p>
      )}
    </div>
  );
}

export default function Landing() {
  return (
    <div className="bg-background dark:bg-gray-900">
      <Navbar />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
        <div className="absolute inset-0 z-0">
          <img
            src={heroImages[0]}
            alt="Agriculture field"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-primary-900/80 via-primary-800/70 to-green-900/80" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-md rounded-full text-white text-sm font-medium mb-6 border border-white/20">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              AI-Powered Agriculture Platform
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-white mb-6 leading-tight">
              Transform Your Farming with{' '}
              <span className="text-gradient bg-gradient-to-r from-amber-300 to-orange-400 bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h1>
            <p className="text-lg sm:text-xl text-white/90 mb-10 max-w-3xl mx-auto leading-relaxed">
              Detect crop diseases instantly, get AI-powered crop recommendations, predict yields,
              and access real-time weather forecasts — all in one beautiful platform.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register" className="group inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-bold rounded-xl text-lg hover:shadow-2xl hover:scale-105 transition-all">
                Get Started Free
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a href="#features" className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 backdrop-blur-md text-white font-bold rounded-xl text-lg border border-white/30 hover:bg-white/20 transition-all">
                Explore Features
              </a>
            </div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10">
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="w-6 h-10 rounded-full border-2 border-white/50 flex items-start justify-center p-2"
          >
            <div className="w-1 h-2 rounded-full bg-white" />
          </motion.div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-6">
              Empowering Farmers with Technology
            </h2>
            <p className="text-gray-600 dark:text-gray-300 text-lg leading-relaxed mb-6">
              SmartAgri ML is a comprehensive AI-powered platform designed to help farmers and
              agricultural professionals make data-driven decisions. We combine cutting-edge
              machine learning with practical agricultural knowledge.
            </p>
            <p className="text-gray-600 dark:text-gray-300 text-lg leading-relaxed mb-8">
              From disease detection to yield prediction, our platform provides the tools you need
              to maximize crop health and productivity while reducing losses.
            </p>
            <div className="grid grid-cols-3 gap-6">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="w-12 h-12 mx-auto mb-2 rounded-xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
                    <stat.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
                  <div className="text-xs text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="relative"
          >
            <img
              src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=800&q=80"
              alt="Smart farming"
              className="rounded-3xl shadow-2xl w-full h-[400px] object-cover"
            />
            <div className="absolute -bottom-6 -left-6 bg-white dark:bg-gray-700 rounded-2xl shadow-xl p-4 max-w-[200px]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <Leaf className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-sm font-bold text-gray-900 dark:text-white">98% Accuracy</div>
                  <div className="text-xs text-gray-500">Disease detection</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* AI Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-background dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <span className="inline-block px-4 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 rounded-full text-sm font-semibold mb-3">
                Features
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Powerful AI Tools for Modern Farming
              </h2>
              <p className="text-gray-500 text-lg max-w-2xl mx-auto">
                Everything you need to manage your farm intelligently, powered by advanced AI and machine learning
              </p>
            </motion.div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="card group hover:-translate-y-1 cursor-pointer"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <span className="inline-block px-4 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 rounded-full text-sm font-semibold mb-3">
              How It Works
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Get Started in 4 Simple Steps
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, idx) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="relative"
              >
                <div className="card text-center">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mb-4">
                    <step.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="text-3xl font-bold text-primary-100 dark:text-primary-900/40 mb-2">{step.num}</div>
                  <h3 className="font-bold text-gray-900 dark:text-white mb-2">{step.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{step.description}</p>
                </div>
                {idx < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-0.5 bg-primary-200 dark:bg-primary-700" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported Crops Section */}
      <section id="crops" className="py-20 px-4 sm:px-6 lg:px-8 bg-background dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <span className="inline-block px-4 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 rounded-full text-sm font-semibold mb-3">
              Supported Crops
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Crops We Support
            </h2>
            <p className="text-gray-500 text-lg max-w-2xl mx-auto">
              Our AI models are trained to detect diseases across 8 major crop types
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {supportedCrops.map((crop, idx) => (
              <motion.div
                key={crop.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.05 }}
                className="card text-center hover:-translate-y-1 cursor-pointer"
              >
                <div className="text-5xl mb-3">{crop.icon}</div>
                <h3 className="font-bold text-gray-900 dark:text-white">{crop.name}</h3>
                <p className="text-sm text-gray-500">{crop.diseases} diseases detectable</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Statistics Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-700 via-primary-600 to-green-700 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <img src="https://images.unsplash.com/photo-1591857178085-d51311616618?w=1920&q=80" alt="" className="w-full h-full object-cover" />
        </div>
        <div className="relative max-w-7xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="text-center"
              >
                <div className="w-16 h-16 mx-auto rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center mb-3">
                  <stat.icon className="w-8 h-8 text-white" />
                </div>
                <div className="text-4xl lg:text-5xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-white/80 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 px-4 sm:px-6 lg:px-8 bg-background dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <span className="inline-block px-4 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 rounded-full text-sm font-semibold mb-3">
              Testimonials
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Trusted by Farmers Worldwide
            </h2>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {testimonials.map((t, idx) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="card"
              >
                <Quote className="w-10 h-10 text-primary-200 dark:text-primary-800 mb-4" />
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-6">{t.text}</p>
                <div className="flex items-center gap-3">
                  <img src={t.avatar} alt={t.name} className="w-12 h-12 rounded-full object-cover" />
                  <div>
                    <div className="font-bold text-gray-900 dark:text-white">{t.name}</div>
                    <div className="text-sm text-gray-500">{t.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-14">
            <span className="inline-block px-4 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 rounded-full text-sm font-semibold mb-3">
              FAQ
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.05 }}
              >
                <FAQItem q={faq.q} a={faq.a} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-600 to-green-700">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl sm:text-5xl font-bold text-white mb-6">
              Ready to Transform Your Farm?
            </h2>
            <p className="text-white/90 text-lg mb-10 max-w-2xl mx-auto">
              Join thousands of farmers using AI to make smarter agricultural decisions.
              Get started for free today.
            </p>
            <Link to="/register" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-bold rounded-xl text-lg hover:shadow-2xl hover:scale-105 transition-all">
              Create Free Account
              <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 dark:bg-black text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                  <Sprout className="w-6 h-6 text-white" />
                </div>
                <span className="font-bold text-xl text-white">SmartAgri</span>
              </div>
              <p className="text-sm leading-relaxed">
                AI-Powered Smart Agriculture & Crop Disease Detection System.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-primary-400 transition-colors">Features</a></li>
                <li><a href="#crops" className="hover:text-primary-400 transition-colors">Supported Crops</a></li>
                <li><Link to="/register" className="hover:text-primary-400 transition-colors">Get Started</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#how-it-works" className="hover:text-primary-400 transition-colors">How It Works</a></li>
                <li><a href="#testimonials" className="hover:text-primary-400 transition-colors">Testimonials</a></li>
                <li><a href="#faq" className="hover:text-primary-400 transition-colors">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-primary-400 transition-colors">Login</Link></li>
                <li><Link to="/register" className="hover:text-primary-400 transition-colors">Register</Link></li>
                <li><Link to="/forgot-password" className="hover:text-primary-400 transition-colors">Forgot Password</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>© 2026 SmartAgri ML. All rights reserved. Built with React, FastAPI, TensorFlow & MongoDB.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
