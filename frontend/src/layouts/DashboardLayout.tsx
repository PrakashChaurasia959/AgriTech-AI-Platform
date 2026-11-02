import { useState } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Leaf, Sprout, TrendingUp, CloudSun,
  History, User, Settings, LogOut, Menu, X, Moon, Sun,
  Shield, Cpu, Activity, ChevronRight, Bell, Zap,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { cn } from "../utils";

const navItems = [
  { to: "/app",                    label: "Dashboard",         icon: LayoutDashboard, end: true,  color: "text-primary-500" },
  { to: "/app/disease-detection",  label: "Disease Detection", icon: Leaf,            end: false, color: "text-red-400"     },
  { to: "/app/crop-recommendation",label: "Crop Recommendation",icon: Sprout,         end: false, color: "text-emerald-500" },
  { to: "/app/yield-prediction",   label: "Yield Prediction",  icon: TrendingUp,      end: false, color: "text-blue-400"    },
  { to: "/app/weather",            label: "Weather",           icon: CloudSun,        end: false, color: "text-amber-400"   },
  { to: "/app/history",            label: "My History",        icon: History,         end: false, color: "text-violet-400"  },
  { to: "/app/profile",            label: "My Profile",        icon: User,            end: false, color: "text-cyan-400"    },
  { to: "/app/settings",           label: "Settings",          icon: Settings,        end: false, color: "text-gray-400"    },
];

export function DashboardLayout() {
  const { user, logout, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => { logout(); navigate("/"); };

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.startsWith("/admin")) return "Admin Panel";
    const sorted = [...navItems].sort((a, b) => b.to.length - a.to.length);
    return sorted.find(n => n.end ? path === n.to : path.startsWith(n.to))?.label || "Dashboard";
  };

  const initials = user?.full_name?.split(" ").map(w => w[0]).slice(0,2).join("").toUpperCase() || "U";

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-gray-100 dark:border-gray-700/50">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-glow-sm">
            <Sprout className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white dark:border-gray-800 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-base text-gray-900 dark:text-white leading-none">SmartAgri</h1>
            <p className="text-[11px] text-primary-600 dark:text-primary-400 font-medium mt-0.5">AI Agriculture Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto scrollbar-none">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
          Main Menu
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to} to={item.to} end={item.end}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              cn("nav-link group", isActive && "nav-link-active")
            }
          >
            {({ isActive }) => (
              <>
                <div className={cn(
                  "w-7 h-7 rounded-lg flex items-center justify-center transition-all",
                  isActive ? "bg-white/20" : `bg-gray-100 dark:bg-gray-700/60 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30`
                )}>
                  <item.icon className={cn("w-3.5 h-3.5", isActive ? "text-white" : item.color)} />
                </div>
                <span className="flex-1 text-[13px]">{item.label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 opacity-70" />}
              </>
            )}
          </NavLink>
        ))}

        {isAdmin && (
          <>
            <div className="divider my-3" />
            <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
              Admin
            </p>
            <NavLink
              to="/admin" onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => cn("nav-link group", isActive && "nav-link-active")}
            >
              {({ isActive }) => (
                <>
                  <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center",
                    isActive ? "bg-white/20" : "bg-purple-100 dark:bg-purple-900/30")}>
                    <Shield className={cn("w-3.5 h-3.5", isActive ? "text-white" : "text-purple-500")} />
                  </div>
                  <span className="flex-1 text-[13px]">Admin Panel</span>
                </>
              )}
            </NavLink>
          </>
        )}
      </nav>

      {/* User card */}
      <div className="p-3 border-t border-gray-100 dark:border-gray-700/50">
        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-gray-900 dark:text-white truncate">{user?.full_name}</p>
            <p className="text-[10px] text-gray-400 truncate">{user?.email}</p>
          </div>
          <div className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" />
        </div>
        <button onClick={handleLogout}
          className="flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-[13px] font-medium">
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F0F4F8] dark:bg-gray-950 flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-64 flex-col bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 sticky top-0 h-screen shadow-sm z-20">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
            <motion.aside initial={{x:-280}} animate={{x:0}} exit={{x:-280}}
              transition={{type:"spring",damping:28,stiffness:300}}
              className="lg:hidden fixed left-0 top-0 bottom-0 w-64 bg-white dark:bg-gray-900 z-50 shadow-2xl">
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-30 h-14 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200/60 dark:border-gray-800 px-4 lg:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)}
              className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-[15px] font-bold text-gray-900 dark:text-white leading-none">{getPageTitle()}</h2>
              <p className="text-[11px] text-gray-400 mt-0.5 hidden sm:block">SmartAgri AI Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary-50 dark:bg-primary-900/30 border border-primary-200 dark:border-primary-800">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
              <span className="text-[11px] font-semibold text-primary-700 dark:text-primary-300">AI Active</span>
            </div>
            <button onClick={toggleTheme}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              {theme === "light"
                ? <Moon className="w-4 h-4 text-gray-600" />
                : <Sun className="w-4 h-4 text-amber-400" />}
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {initials}
            </div>
          </div>
        </header>

        {/* Page */}
        <main className="flex-1 p-4 lg:p-6 overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
