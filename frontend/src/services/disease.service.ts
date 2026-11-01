import api from './api';
import type { DiseasePrediction, DiseaseHistoryItem, HistoryResponse, DiseaseModelInfo } from '../types';

export const diseaseService = {
  async predict(file: File, cropType: string): Promise<DiseasePrediction> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('crop_type', cropType);
    const res = await api.post<DiseasePrediction>('/disease/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  /** Returns the current model status — production CNN or demo fallback. */
  async getModelInfo(): Promise<DiseaseModelInfo> {
    const res = await api.get<DiseaseModelInfo>('/disease/model-info');
    return res.data;
  },

  async getHistory(page = 1, perPage = 10, search = ''): Promise<HistoryResponse<DiseaseHistoryItem>> {
    const res = await api.get<HistoryResponse<DiseaseHistoryItem>>('/disease/history', {
      params: { page, per_page: perPage, search },
    });
    return res.data;
  },

  async getDetail(id: string): Promise<DiseasePrediction & { id: string }> {
    const res = await api.get(`/disease/history/${id}`);
    return res.data;
  },

  async deleteHistory(id: string): Promise<void> {
    await api.delete(`/disease/history/${id}`);
  },

  async downloadReport(id: string): Promise<Blob> {
    const res = await api.get(`/disease/report/${id}`, { responseType: 'blob' });
    return res.data;
  },

  async getCrops(): Promise<{ crops: { value: string; label: string; icon: string }[] }> {
    const res = await api.get('/disease/crops');
    return res.data;
  },
};
