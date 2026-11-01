// ============================================================
// Type definitions for the Smart Agriculture frontend
// ============================================================

// ---- Auth ----
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface User {
  id: string;
  full_name: string;
  email: string;
  mobile_number: string;
  role: string;
  farm_name?: string | null;
  location?: string | null;
  avatar_url?: string | null;
  created_at?: string;
  is_active?: boolean;
  activity_count?: number;
}

export interface RegisterData {
  full_name: string;
  email: string;
  mobile_number: string;
  password: string;
  confirm_password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface ForgotPasswordResponse {
  message: string;
  reset_link?: string;
  reset_token?: string;
}

// ---- Disease Detection ----
export interface DiseasePrediction {
  disease_name: string;
  confidence: number;
  is_healthy: boolean;
  crop_type: string;
  symptoms: string[];
  causes: string[];
  treatment: string[];
  prevention: string[];
  prediction_id: string;
  is_demo_mode: boolean;
  /** Only present when production mode fell back to demo */
  _fallback_reason?: string;
  created_at: string;
}

export interface DiseaseModelInfo {
  mode: 'production' | 'demo';
  model_loaded: boolean;
  model_path: string;
  num_classes: number;
  input_size: number;
  error_message: string | null;
}

export interface DiseaseHistoryItem {
  id: string;
  crop_type: string;
  disease_name: string;
  confidence: number;
  is_healthy: boolean;
  is_demo_mode: boolean;
  created_at: string;
}

export interface HistoryResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// ---- Crop Recommendation ----
export interface CropRecommendationRequest {
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  soil_type: string;
  location: string;
}

export interface CropRecommendationItem {
  crop: string;
  confidence: number;
  suitability: string;
  description: string;
  farming_tips: string[];
  fertilizer_suggestions: string[];
}

export interface CropRecommendationResponse {
  recommendations: CropRecommendationItem[];
  top_recommendation: string;
  soil_info: SoilInfo;
  prediction_id: string;
  created_at: string;
}

export interface SoilInfo {
  description: string;
  ph_range: string;
  characteristics: string[];
}

export interface CropHistoryItem {
  id: string;
  top_recommendation: string;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  created_at: string;
}

// ---- Yield Prediction ----
export interface YieldPredictionRequest {
  crop_type: string;
  state: string;
  season: string;
  area: number;
  rainfall: number;
  temperature: number;
  soil_type: string;
  fertilizer_usage: number;
}

export interface YieldPredictionResponse {
  crop_type: string;
  predicted_yield: number;
  predicted_production: number;
  yield_unit: string;
  confidence: number;
  suitability: string;
  conditions_summary: string;
  improvement_suggestions: string[];
  prediction_id: string;
  created_at: string;
  is_estimate: boolean;
}

export interface YieldHistoryItem {
  id: string;
  crop_type: string;
  state: string;
  season: string;
  area: number;
  predicted_yield: number;
  created_at: string;
}

export interface YieldOptions {
  crops: string[];
  seasons: string[];
  states: string[];
  soil_types: string[];
}

// ---- Weather ----
export interface CurrentWeather {
  temperature: number;
  apparent_temperature: number;
  humidity: number;
  wind_speed: number;
  precipitation: number;
  weather_code: number;
  weather_description: string;
  cloud_cover: number;
  location_name: string;
  farming_advice: string;
}

export interface ForecastDay {
  date: string;
  temp_max: number;
  temp_min: number;
  precipitation: number;
  weather_code: number;
  weather_description: string;
  wind_speed_max: number;
}

export interface WeatherForecast {
  location_name: string;
  current: CurrentWeather;
  forecast: ForecastDay[];
  farming_advice: string;
}

export interface GeocodeResult {
  latitude: number;
  longitude: number;
  name: string;
  country: string;
  admin1: string;
}

// ---- Admin ----
export interface AdminDashboard {
  stats: {
    total_users: number;
    total_admins: number;
    total_disease_detections: number;
    total_crop_recommendations: number;
    total_yield_predictions: number;
    total_activities: number;
  };
  disease_by_crop: { crop: string; count: number }[];
  recent_users: User[];
  recent_activities: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  user_name: string;
  activity_type: string;
  description: string;
  created_at: string;
}
