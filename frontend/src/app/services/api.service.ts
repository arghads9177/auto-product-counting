import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  Camera,
  CameraConfig,
  CountSummary,
  CameraMetrics,
  PlantMetrics,
  Session,
  CountEvent,
  ActivityEvent,
  SystemLog,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  listCameras(): Observable<Camera[]> {
    return this.http.get<{ cameras: Camera[] }>(`${this.base}/cameras`).pipe(map(r => r.cameras));
  }

  addCamera(camera_id: string, name: string, rtsp_url: string) {
    return this.http.post<Camera>(`${this.base}/cameras`, { camera_id, name, rtsp_url });
  }

  getCameraConfig(cameraId: string): Observable<CameraConfig> {
    return this.http.get<CameraConfig>(`${this.base}/cameras/${cameraId}/config`);
  }

  updateCameraConfig(cameraId: string, config: Partial<CameraConfig>) {
    return this.http.put(`${this.base}/cameras/${cameraId}/config`, config);
  }

  startCamera(cameraId: string) {
    return this.http.post(`${this.base}/cameras/${cameraId}/start`, {});
  }

  stopCamera(cameraId: string) {
    return this.http.post(`${this.base}/cameras/${cameraId}/stop`, {});
  }

  getCountsSummary(): Observable<CountSummary> {
    return this.http.get<CountSummary>(`${this.base}/counts/summary`);
  }

  getCameraCounts(cameraId: string) {
    return this.http.get<CameraMetrics & { active_session: Session | null }>(
      `${this.base}/counts/camera/${cameraId}`
    );
  }

  getCountEvents(cameraId?: string, sessionId?: string, limit = 100): Observable<CountEvent[]> {
    let params = new HttpParams().set('limit', limit);
    if (cameraId) params = params.set('camera_id', cameraId);
    if (sessionId) params = params.set('session_id', sessionId);
    return this.http.get<{ events: CountEvent[] }>(`${this.base}/counts/events`, { params }).pipe(
      map(r => r.events)
    );
  }

  getSessions(status?: string, cameraId?: string, limit = 50): Observable<Session[]> {
    let params = new HttpParams().set('limit', limit);
    if (status) params = params.set('status', status);
    if (cameraId) params = params.set('camera_id', cameraId);
    return this.http.get<{ sessions: Session[] }>(`${this.base}/sessions`, { params }).pipe(
      map(r => r.sessions)
    );
  }

  getSessionDetails(sessionId: string) {
    return this.http.get<Session & { count_events: CountEvent[]; activity_events: ActivityEvent[] }>(
      `${this.base}/sessions/${sessionId}`
    );
  }

  getCameraMetrics(cameraId: string): Observable<CameraMetrics> {
    return this.http.get<CameraMetrics>(`${this.base}/metrics/camera/${cameraId}`);
  }

  getPlantMetrics(): Observable<PlantMetrics> {
    return this.http.get<PlantMetrics>(`${this.base}/metrics/plant`);
  }

  getLogs(limit = 100, category?: string, severity?: string, cameraId?: string): Observable<SystemLog[]> {
    let params = new HttpParams().set('limit', limit);
    if (category) params = params.set('category', category);
    if (severity) params = params.set('severity', severity);
    if (cameraId) params = params.set('camera_id', cameraId);
    return this.http.get<{ logs: SystemLog[] }>(`${this.base}/logs`, { params }).pipe(map(r => r.logs));
  }

  getEventTimeline(limit = 50, cameraId?: string, sessionId?: string): Observable<ActivityEvent[]> {
    let params = new HttpParams().set('limit', limit);
    if (cameraId) params = params.set('camera_id', cameraId);
    if (sessionId) params = params.set('session_id', sessionId);
    return this.http.get<{ events: ActivityEvent[] }>(`${this.base}/events/timeline`, { params }).pipe(
      map(r => r.events)
    );
  }

  downloadReport(format: string, startDate?: string, endDate?: string, cameraId?: string) {
    let params = new HttpParams().set('format', format);
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    if (cameraId) params = params.set('camera_id', cameraId);
    return this.http.get(`${this.base}/reports`, { params, responseType: 'blob' });
  }

  getStreamUrl(cameraId: string): string {
    const base = environment.streamUrl || window.location.origin;
    return `${base}/stream/${cameraId}.mjpeg`;
  }
}
