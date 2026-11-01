import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudSun, Search, Loader2, Wind, Droplets, Cloud, CloudRain,
  Sun, Thermometer, MapPin, Sprout, CloudSnow,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { weatherService } from '../services/weather.service';
import type { WeatherForecast as WeatherForecastType, GeocodeResult } from '../types';
import { usePageTitle } from '../hooks/usePageTitle';

const weatherIcons: Record<number, typeof Sun> = {
  0: Sun, 1: Sun, 2: Cloud, 3: Cloud,
  45: Cloud, 48: Cloud, 51: CloudRain, 53: CloudRain, 55: CloudRain,
  61: CloudRain, 63: CloudRain, 65: CloudRain, 80: CloudRain, 81: CloudRain,
  71: CloudSnow, 73: CloudSnow, 75: CloudSnow,
  95: CloudRain, 96: CloudRain, 99: CloudRain,
};

function getWeatherIcon(code: number) {
  return weatherIcons[code] || Cloud;
}

export default function WeatherPage() {
  usePageTitle('Weather Forecast');
  const [loading, setLoading] = useState(false);
  const [forecast, setForecast] = useState<WeatherForecastType | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [coords, setCoords] = useState<{ lat: number; lon: number; name: string }>({
    lat: 28.6139, lon: 77.209, name: 'New Delhi',
  });

  const loadWeather = async (lat: number, lon: number, name: string) => {
    setLoading(true);
    try {
      const res = await weatherService.getForecast(lat, lon, name);
      setForecast(res);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to fetch weather');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWeather(coords.lat, coords.lon, coords.name);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const result = await weatherService.geocode(searchQuery);
      setCoords({ lat: result.latitude, lon: result.longitude, name: result.name });
      await loadWeather(result.latitude, result.longitude, result.name);
      setSearchQuery('');
    } catch {
      toast.error('Location not found');
    } finally {
      setLoading(false);
    }
  };

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation not available');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setCoords({ lat: latitude, lon: longitude, name: 'My Location' });
        loadWeather(latitude, longitude, 'My Location');
      },
      () => toast.error('Could not get your location')
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <CloudSun className="w-7 h-7 text-primary-600" /> Weather Forecast
        </h1>
        <p className="text-gray-500 mt-1">Real-time weather data and 7-day forecast with farming advice</p>
      </div>

      {/* Search bar */}
      <div className="card">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="input-field pl-11"
              placeholder="Search city or location..."
            />
          </div>
          <button onClick={handleSearch} disabled={loading} className="btn-primary disabled:opacity-60">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
          </button>
          <button onClick={handleUseMyLocation} className="btn-secondary" title="Use my location">
            <MapPin className="w-5 h-5" />
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="card flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </motion.div>
        ) : forecast ? (
          <motion.div key="weather" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* Current weather */}
            <div className="card bg-gradient-to-br from-primary-500 to-blue-600 text-white border-0">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 text-white/80 text-sm">
                    <MapPin className="w-4 h-4" /> {forecast.location_name}
                  </div>
                  <div className="text-5xl font-bold mt-2">{forecast.current.temperature.toFixed(1)}°C</div>
                  <div className="text-white/80">{forecast.current.weather_description}</div>
                </div>
                <div className="text-right">
                  {(() => {
                    const Icon = getWeatherIcon(forecast.current.weather_code);
                    return <Icon className="w-20 h-20 text-white/90" />;
                  })()}
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { icon: Thermometer, label: 'Feels Like', value: `${forecast.current.apparent_temperature.toFixed(1)}°C` },
                  { icon: Droplets, label: 'Humidity', value: `${forecast.current.humidity}%` },
                  { icon: Wind, label: 'Wind', value: `${forecast.current.wind_speed} km/h` },
                  { icon: CloudRain, label: 'Precip.', value: `${forecast.current.precipitation} mm` },
                ].map((item) => (
                  <div key={item.label} className="bg-white/10 backdrop-blur-md rounded-xl p-3">
                    <div className="flex items-center gap-1 text-white/70 text-xs mb-1">
                      <item.icon className="w-3 h-3" /> {item.label}
                    </div>
                    <div className="font-bold">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Farming advice */}
            <div className="card border-2 border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-900/20">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-primary-600" /> Farming Advice
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">{forecast.farming_advice}</p>
            </div>

            {/* 7-day forecast */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">7-Day Forecast</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                {forecast.forecast.map((day, idx) => {
                  const Icon = getWeatherIcon(day.weather_code);
                  return (
                    <motion.div
                      key={day.date}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="card text-center"
                    >
                      <div className="text-xs text-gray-500 mb-1">
                        {idx === 0 ? 'Today' : new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                      </div>
                      <div className="text-xs text-gray-400 mb-2">
                        {new Date(day.date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                      </div>
                      <Icon className="w-8 h-8 mx-auto text-primary-500 mb-2" />
                      <div className="text-sm font-bold text-gray-900 dark:text-white">
                        {day.temp_max.toFixed(0)}° / {day.temp_min.toFixed(0)}°
                      </div>
                      <div className="text-xs text-gray-400 mt-1">{day.weather_description}</div>
                      <div className="text-xs text-blue-500 mt-1">{day.precipitation.toFixed(1)}mm</div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="card text-center py-12 text-gray-400">
            <CloudSun className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No weather data. Search for a location to get started.</p>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
