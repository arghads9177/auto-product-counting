import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';
import {
  Camera,
  CameraConfig,
  CountSummary,
  Session,
  CountEvent,
  ActivityEvent,
  CameraMetrics,
  PlantMetrics,
  SystemLog,
} from '../models/api.models';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  // ─── Cameras ──────────────────────────────────────────────────

  describe('listCameras()', () => {
    const mockCameras: Camera[] = [
      { camera_id: 'cam01', name: 'Dock 1', status: 'STOPPED' },
      { camera_id: 'cam02', name: 'Dock 2', status: 'RUNNING' },
    ];

    it('should GET /cameras and unwrap cameras array', () => {
      service.listCameras().subscribe(cameras => {
        expect(cameras.length).toBe(2);
        expect(cameras[0].camera_id).toBe('cam01');
      });

      const req = httpMock.expectOne(`${base}/cameras`);
      expect(req.request.method).toBe('GET');
      req.flush({ cameras: mockCameras });
    });

    it('should handle empty camera list', () => {
      service.listCameras().subscribe(cameras => {
        expect(cameras).toEqual([]);
      });

      httpMock.expectOne(`${base}/cameras`).flush({ cameras: [] });
    });

    it('should propagate HTTP error', () => {
      let errorStatus = 0;
      service.listCameras().subscribe({
        error: (err) => { errorStatus = err.status; },
      });

      httpMock.expectOne(`${base}/cameras`).flush('', { status: 500, statusText: 'Server Error' });
      expect(errorStatus).toBe(500);
    });
  });

  describe('addCamera()', () => {
    it('should POST camera data to /cameras', () => {
      const mockCamera: Camera = { camera_id: 'cam03', name: 'Bay 3', status: 'STOPPED' };

      service.addCamera('cam03', 'Bay 3', 'rtsp://localhost:8554/cam03').subscribe(cam => {
        expect(cam.camera_id).toBe('cam03');
      });

      const req = httpMock.expectOne(`${base}/cameras`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        camera_id: 'cam03',
        name: 'Bay 3',
        rtsp_url: 'rtsp://localhost:8554/cam03',
      });
      req.flush(mockCamera);
    });

    it('should handle 409 conflict for duplicate camera_id', () => {
      let errorStatus = 0;
      service.addCamera('cam01', 'Dup', 'rtsp://x').subscribe({
        error: (err) => { errorStatus = err.status; },
      });

      httpMock.expectOne(`${base}/cameras`).flush(
        { detail: 'Camera already exists' },
        { status: 409, statusText: 'Conflict' }
      );
      expect(errorStatus).toBe(409);
    });
  });

  describe('getCameraConfig()', () => {
    it('should GET camera config by id', () => {
      const mockConfig: CameraConfig = {
        camera_id: 'cam01',
        zones: {},
        lines: { A: [[0, 0.3]], B: [[0, 0.7]] },
        direction_map: { 'A->B': 'loading' },
        thresholds: { min_products: 3 },
      };

      service.getCameraConfig('cam01').subscribe(config => {
        expect(config.camera_id).toBe('cam01');
      });

      const req = httpMock.expectOne(`${base}/cameras/cam01/config`);
      expect(req.request.method).toBe('GET');
      req.flush(mockConfig);
    });
  });

  describe('updateCameraConfig()', () => {
    it('should PUT partial config update', () => {
      service.updateCameraConfig('cam01', { thresholds: { min_products: 5 } }).subscribe();

      const req = httpMock.expectOne(`${base}/cameras/cam01/config`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ thresholds: { min_products: 5 } });
      req.flush({});
    });
  });

  describe('startCamera() / stopCamera()', () => {
    it('should POST to /cameras/{id}/start', () => {
      service.startCamera('cam01').subscribe();

      const req = httpMock.expectOne(`${base}/cameras/cam01/start`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});
      req.flush({});
    });

    it('should POST to /cameras/{id}/stop', () => {
      service.stopCamera('cam01').subscribe();

      const req = httpMock.expectOne(`${base}/cameras/cam01/stop`);
      expect(req.request.method).toBe('POST');
      req.flush({});
    });
  });

  // ─── Counts ───────────────────────────────────────────────────

  describe('getCountsSummary()', () => {
    it('should GET /counts/summary', () => {
      const mockSummary: CountSummary = {
        total_loading: 150,
        total_unloading: 80,
        total: 230,
        active_cameras: 2,
        active_sessions: 1,
      };

      service.getCountsSummary().subscribe(summary => {
        expect(summary.total_loading).toBe(150);
        expect(summary.total).toBe(230);
      });

      httpMock.expectOne(`${base}/counts/summary`).flush(mockSummary);
    });
  });

  describe('getCameraCounts()', () => {
    it('should GET /counts/camera/{id}', () => {
      service.getCameraCounts('cam01').subscribe(res => {
        expect(res.camera_id).toBe('cam01');
      });

      httpMock.expectOne(`${base}/counts/camera/cam01`).flush({
        camera_id: 'cam01',
        today_loading: 10,
        today_unloading: 5,
        today_total: 15,
        active_session: null,
      });
    });
  });

  describe('getCountEvents()', () => {
    it('should GET /counts/events with default params', () => {
      service.getCountEvents().subscribe(events => {
        expect(events.length).toBe(1);
      });

      const req = httpMock.expectOne(r => r.url === `${base}/counts/events`);
      expect(req.request.params.get('limit')).toBe('100');
      expect(req.request.params.has('camera_id')).toBeFalse();
      req.flush({ events: [{ camera_id: 'cam01', track_id: 1, direction: 'loading', product_class: 'box', confidence: 0.9, timestamp: '2026-01-01T00:00:00Z', session_id: 's1' }] });
    });

    it('should pass optional camera_id and session_id params', () => {
      service.getCountEvents('cam01', 'session-abc', 50).subscribe();

      const req = httpMock.expectOne(r => r.url === `${base}/counts/events`);
      expect(req.request.params.get('camera_id')).toBe('cam01');
      expect(req.request.params.get('session_id')).toBe('session-abc');
      expect(req.request.params.get('limit')).toBe('50');
      req.flush({ events: [] });
    });
  });

  // ─── Sessions ─────────────────────────────────────────────────

  describe('getSessions()', () => {
    it('should GET /sessions with default params', () => {
      service.getSessions().subscribe(sessions => {
        expect(sessions).toEqual([]);
      });

      const req = httpMock.expectOne(r => r.url === `${base}/sessions`);
      expect(req.request.params.get('limit')).toBe('50');
      req.flush({ sessions: [] });
    });

    it('should pass status and camera_id filters', () => {
      service.getSessions('ACTIVE', 'cam02').subscribe();

      const req = httpMock.expectOne(r => r.url === `${base}/sessions`);
      expect(req.request.params.get('status')).toBe('ACTIVE');
      expect(req.request.params.get('camera_id')).toBe('cam02');
      req.flush({ sessions: [] });
    });
  });

  describe('getSessionDetails()', () => {
    it('should GET /sessions/{id} with events', () => {
      service.getSessionDetails('sess-123').subscribe(res => {
        expect(res.session_id).toBe('sess-123');
        expect(res.count_events.length).toBe(0);
      });

      httpMock.expectOne(`${base}/sessions/sess-123`).flush({
        session_id: 'sess-123',
        camera_id: 'cam01',
        status: 'COMPLETED',
        count_events: [],
        activity_events: [],
      });
    });
  });

  // ─── Metrics ──────────────────────────────────────────────────

  describe('getCameraMetrics()', () => {
    it('should GET /metrics/camera/{id}', () => {
      service.getCameraMetrics('cam01').subscribe(m => {
        expect(m.today_total).toBe(25);
      });

      httpMock.expectOne(`${base}/metrics/camera/cam01`).flush({
        camera_id: 'cam01',
        today_loading: 15,
        today_unloading: 10,
        today_total: 25,
      });
    });
  });

  describe('getPlantMetrics()', () => {
    it('should GET /metrics/plant', () => {
      service.getPlantMetrics().subscribe(m => {
        expect(m.active_cameras).toBe(3);
      });

      httpMock.expectOne(`${base}/metrics/plant`).flush({
        total_loading: 200,
        total_unloading: 100,
        total: 300,
        active_cameras: 3,
        active_sessions: 2,
      });
    });
  });

  // ─── Logs ─────────────────────────────────────────────────────

  describe('getLogs()', () => {
    it('should GET /logs with default limit', () => {
      service.getLogs().subscribe(logs => {
        expect(logs.length).toBe(1);
      });

      const req = httpMock.expectOne(r => r.url === `${base}/logs`);
      expect(req.request.params.get('limit')).toBe('100');
      req.flush({
        logs: [{ category: 'SYSTEM', severity: 'INFO', message: 'Started', timestamp: '2026-01-01T00:00:00Z' }],
      });
    });

    it('should pass all optional filter params', () => {
      service.getLogs(50, 'DETECTION', 'ERROR', 'cam01').subscribe();

      const req = httpMock.expectOne(r => r.url === `${base}/logs`);
      expect(req.request.params.get('limit')).toBe('50');
      expect(req.request.params.get('category')).toBe('DETECTION');
      expect(req.request.params.get('severity')).toBe('ERROR');
      expect(req.request.params.get('camera_id')).toBe('cam01');
      req.flush({ logs: [] });
    });

    it('should not include undefined optional params', () => {
      service.getLogs(100, undefined, undefined, undefined).subscribe();

      const req = httpMock.expectOne(r => r.url === `${base}/logs`);
      expect(req.request.params.has('category')).toBeFalse();
      expect(req.request.params.has('severity')).toBeFalse();
      expect(req.request.params.has('camera_id')).toBeFalse();
      req.flush({ logs: [] });
    });
  });

  // ─── Event Timeline ───────────────────────────────────────────

  describe('getEventTimeline()', () => {
    it('should GET /events/timeline with params', () => {
      service.getEventTimeline(20, 'cam01').subscribe(events => {
        expect(events).toEqual([]);
      });

      const req = httpMock.expectOne(r => r.url === `${base}/events/timeline`);
      expect(req.request.params.get('limit')).toBe('20');
      expect(req.request.params.get('camera_id')).toBe('cam01');
      req.flush({ events: [] });
    });
  });

  // ─── Reports ──────────────────────────────────────────────────

  describe('downloadReport()', () => {
    it('should GET /reports with format param and blob response', () => {
      service.downloadReport('csv', '2026-01-01', '2026-01-31', 'cam01').subscribe(blob => {
        expect(blob instanceof Blob).toBeTrue();
      });

      const req = httpMock.expectOne(r => r.url === `${base}/reports`);
      expect(req.request.params.get('format')).toBe('csv');
      expect(req.request.params.get('start_date')).toBe('2026-01-01');
      expect(req.request.params.get('end_date')).toBe('2026-01-31');
      expect(req.request.params.get('camera_id')).toBe('cam01');
      expect(req.request.responseType).toBe('blob');
      req.flush(new Blob(['csv,data'], { type: 'text/csv' }));
    });

    it('should not include undefined date/camera params', () => {
      service.downloadReport('pdf').subscribe();

      const req = httpMock.expectOne(r => r.url === `${base}/reports`);
      expect(req.request.params.get('format')).toBe('pdf');
      expect(req.request.params.has('start_date')).toBeFalse();
      expect(req.request.params.has('end_date')).toBeFalse();
      expect(req.request.params.has('camera_id')).toBeFalse();
      req.flush(new Blob());
    });
  });

  // ─── Stream URL ───────────────────────────────────────────────

  describe('getStreamUrl()', () => {
    it('should return MJPEG stream URL with camera id', () => {
      const url = service.getStreamUrl('cam01');
      expect(url).toContain('/stream/cam01.mjpeg');
    });

    it('should use environment.streamUrl when set', () => {
      const originalStreamUrl = environment.streamUrl;
      (environment as any).streamUrl = 'http://stream-server:8000';

      const url = service.getStreamUrl('cam02');
      expect(url).toBe('http://stream-server:8000/stream/cam02.mjpeg');

      (environment as any).streamUrl = originalStreamUrl;
    });

    it('should fall back to window.location.origin when streamUrl is empty', () => {
      const originalStreamUrl = environment.streamUrl;
      (environment as any).streamUrl = '';

      const url = service.getStreamUrl('cam01');
      expect(url).toBe(`${window.location.origin}/stream/cam01.mjpeg`);

      (environment as any).streamUrl = originalStreamUrl;
    });
  });
});
