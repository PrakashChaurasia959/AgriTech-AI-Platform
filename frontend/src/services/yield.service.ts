import api from './api';
import type { YieldPredictionRequest, YieldPredictionResponse, YieldHistoryItem, HistoryResponse, YieldOptions } from '../types';

export const yieldService = {
  async predict(data: YieldPredictionRequest): Promise<YieldPredictionResponse> {
    const res = await api.post<YieldPredictionResponse>('/yield/predict', data);
    return res.data;
  },

  async getHistory(page = 1, perPage = 10): Promise<HistoryResponse<YieldHistoryItem>> {
    const res = await api.get<HistoryResponse<YieldHistoryItem>>('/yield/history', {
      params: { page, per_page: perPage },
    });
    return res.data;
  },

  async deleteHistory(id: string): Promise<void> {
    await api.delete(`/yield/history/${id}`);
  },

  async downloadReport(id: string): Promise<Blob> {
    const res = await api.get(`/yield/report/${id}`, { responseType: 'blob' });
    return res.data;
  },

  async getOptions(): Promise<YieldOptions> {
    const res = await api.get<YieldOptions>('/yield/options');
    return res.data;
  },
};
