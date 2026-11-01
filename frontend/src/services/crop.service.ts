import api from './api';
import type { CropRecommendationRequest, CropRecommendationResponse, CropHistoryItem, HistoryResponse } from '../types';

/** Shape returned by GET /api/crop/live-weather */
export interface LiveWeather {
  temperature: number;
  humidity: number;
  rainfall: number;
  description: string;
  city: string;
}

export const cropService = {
  async recommend(data: CropRecommendationRequest): Promise<CropRecommendationResponse> {
    const res = await api.post<CropRecommendationResponse>('/crop/recommend', data);
    return res.data;
  },

  /**
   * Fetch live weather from the backend (which calls OpenWeatherMap).
   * Returns null when the API key is not configured (501) — callers
   * must handle the null case gracefully.
   */
  async getLiveWeather(lat: number, lon: number): Promise<LiveWeather | null> {
    try {
      const res = await api.get<LiveWeather>('/crop/live-weather', {
        params: { lat, lon },
      });
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 501) {
        // OpenWeatherMap key not configured — this is expected in dev
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
