import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User, LoginData, RegisterData } from '../types';
import { authService } from '../services/auth.service';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('smartagri_token');
    const savedUser = localStorage.getItem('smartagri_user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('smartagri_token');
        localStorage.removeItem('smartagri_user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (data: LoginData) => {
    const res = await authService.login(data);
    localStorage.setItem('smartagri_token', res.access_token);
    const userData: User = {
      id: res.user_id,
      full_name: res.full_name,
      email: res.email,
      mobile_number: '',
      role: res.role,
    };
    localStorage.setItem('smartagri_user', JSON.stringify(userData));
    setUser(userData);
    // Fetch full profile
    try {
      const profile = await authService.getMe();
      const fullUser: User = {
        ...profile,
        id: res.user_id,
      };
      setUser(fullUser);
      localStorage.setItem('smartagri_user', JSON.stringify(fullUser));
    } catch {
      // Profile fetch failed, keep basic user
    }
  };

  const register = async (data: RegisterData) => {
    const res = await authService.register(data);
    localStorage.setItem('smartagri_token', res.access_token);
    const userData: User = {
      id: res.user_id,
      full_name: res.full_name,
      email: res.email,
      mobile_number: '',
      role: res.role,
    };
    localStorage.setItem('smartagri_user', JSON.stringify(userData));
    setUser(userData);
    try {
      const profile = await authService.getMe();
      setUser({ ...profile, id: res.user_id });
      localStorage.setItem('smartagri_user', JSON.stringify({ ...profile, id: res.user_id }));
    } catch {
      // keep basic
    }
  };

  const logout = () => {
    localStorage.removeItem('smartagri_token');
    localStorage.removeItem('smartagri_user');
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const profile = await authService.getMe();
      setUser(profile);
      localStorage.setItem('smartagri_user', JSON.stringify(profile));
    } catch {
      // ignore
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
