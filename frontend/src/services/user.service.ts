import api from './api';
import type { User } from '../types';

export const userService = {
  async getProfile(): Promise<User> {
    const res = await api.get<User>('/users/profile');
    return res.data;
  },

  async updateProfile(data: Partial<User>): Promise<User & { message: string }> {
    const res = await api.put<User & { message: string }>('/users/profile', data);
    return res.data;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const res = await api.put('/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return res.data;
  },
};
