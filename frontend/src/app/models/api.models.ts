export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}

export interface UserProfile {
  username: string;
  role: string;
}

export interface Camera {
  camera_id: string;
  name: string;
  rtsp_url?: string;
  status: string;
  source_type?: string;
  enabled?: boolean;
}

export interface CameraConfig {
  camera_id: string;
  zones: Record<string, unknown>;
  lines: Record<string, number[][]>;
  direction_map: Record<string, string>;
  thresholds: Record<string, number>;
}

export interface Session {
  session_id: string;
  camera_id: string;
  status: string;
  direction?: string;
  loading_count?: number;
  unloading_count?: number;
  started_at?: string;
  ended_at?: string;
}

export interface CountSummary {
  total_loading: number;
  total_unloading: number;
  total: number;
  active_cameras: number;
  active_sessions: number;
  active_sessions_detail?: Session[];
}

export interface CountEvent {
  camera_id: string;
  session_id: string;
  track_id: number;
  direction: string;
  product_class: string;
  confidence: number;
  timestamp: string;
}

export interface ActivityEvent {
  camera_id: string;
  session_id?: string;
  event_type: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface CameraMetrics {
  camera_id: string;
  today_loading: number;
  today_unloading: number;
  today_total: number;
}

export interface PlantMetrics {
  total_loading: number;
  total_unloading: number;
  total: number;
  active_cameras: number;
  active_sessions: number;
}

export interface SystemLog {
  category: string;
  severity: string;
  message: string;
  camera_id?: string;
  timestamp: string;
  details?: Record<string, unknown>;
}
