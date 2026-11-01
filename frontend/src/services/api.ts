import axios from 'axios';

// Base API URL - uses Vite proxy in dev, can be overridden
const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('smartagri_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('smartagri_token');
      localStorage.removeItem('smartagri_user');
      // Only redirect if not already on an auth page
      const path = window.location.pathname;
      if (!path.includes('/login') && !path.includes('/register') && !path.includes('/reset-password') && !path.includes('/forgot-password')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
