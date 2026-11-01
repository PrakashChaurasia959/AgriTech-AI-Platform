import api from './api';
import type { WeatherForecast, CurrentWeather, GeocodeResult } from '../types';

export const weatherService = {
  async getForecast(lat: number, lon: number, location = ''): Promise<WeatherForecast> {
    const res = await api.get<WeatherForecast>('/weather/forecast', {
      params: { lat, lon, location },
    });
    return res.data;
  },

  async getCurrent(lat: number, lon: number, location = ''): Promise<CurrentWeather> {
    const res = await api.get<CurrentWeather>('/weather/current', {
      params: { lat, lon, location },
    });
    return res.data;
  },

  async geocode(query: string): Promise<GeocodeResult> {
    const res = await api.get<GeocodeResult>('/weather/geocode', { params: { q: query } });
    return res.data;
  },
};
