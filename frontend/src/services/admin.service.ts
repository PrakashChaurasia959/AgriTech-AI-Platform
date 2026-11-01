import api from './api';
import type { AdminDashboard, User, HistoryResponse } from '../types';

export const adminService = {
  async getDashboard(): Promise<AdminDashboard> {
    const res = await api.get<AdminDashboard>('/admin/dashboard');
    return res.data;
  },

  async getUsers(page = 1, perPage = 10, search = ''): Promise<HistoryResponse<User>> {
    const res = await api.get<HistoryResponse<User>>('/admin/users', {
      params: { page, per_page: perPage, search },
    });
    return res.data;
  },

  async toggleUserStatus(userId: string): Promise<{ message: string; is_active: boolean }> {
    const res = await api.put(`/admin/users/${userId}/status`);
    return res.data;
  },
};
