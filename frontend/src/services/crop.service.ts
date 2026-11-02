import api from './api';
import type { CropRecommendationRequest, CropRecommendationResponse, CropHistoryItem, HistoryResponse } from '../types';

/** Shape returned by GET /api/crop/live-weather */
export interface LiveWeather {
  temperature: number;
  humidity: number;
  rainfall: number;
  description: string;
  city: string;
  source: 'openweathermap' | 'open-meteo';
}

export const cropService = {
  async recommend(data: CropRecommendationRequest): Promise<CropRecommendationResponse> {
    const res = await api.post<CropRecommendationResponse>('/crop/recommend', data);
    return res.data;
  },

  /**
   * Fetch live weather from the backend, which falls back to Open-Meteo
   * when OpenWeatherMap is not configured or rejects its key.
   */
  async getLiveWeather(lat: number, lon: number): Promise<LiveWeather | null> {
    try {
      const res = await api.get<LiveWeather>('/crop/live-weather', {
        params: { lat, lon },
      });
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 501) {
        // Preserve manual weather entry if the backend cannot provide data.
        return null;
      }
      throw err;
    }
  },

  async getHistory(page = 1, perPage = 10): Promise<HistoryResponse<CropHistoryItem>> {
    const res = await api.get<HistoryResponse<CropHistoryItem>>('/crop/history', {
      params: { page, per_page: perPage },
    });
    return res.data;
  },

  async deleteHistory(id: string): Promise<void> {
    await api.delete(`/crop/history/${id}`);
  },

  async downloadReport(id: string): Promise<Blob> {
    const res = await api.get(`/crop/report/${id}`, { responseType: 'blob' });
    return res.data;
  },
};
