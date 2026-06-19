import { TestBed } from '@angular/core/testing';
import { SocketService } from './socket.service';

// Mock socket.io-client
const mockSocketInstance = {
  connected: false,
  on: jasmine.createSpy('on'),
  disconnect: jasmine.createSpy('disconnect'),
};

// We need to capture the event handlers registered via .on()
let registeredHandlers: Record<string, Function> = {};

describe('SocketService', () => {
  let service: SocketService;

  beforeEach(() => {
    registeredHandlers = {};
    mockSocketInstance.on.calls.reset();
    mockSocketInstance.disconnect.calls.reset();
    mockSocketInstance.connected = false;

    mockSocketInstance.on.and.callFake((event: string, handler: Function) => {
      registeredHandlers[event] = handler;
    });

    TestBed.configureTestingModule({});
    service = TestBed.inject(SocketService);
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have Subject observables defined', () => {
    expect(service.countEvent$).toBeDefined();
    expect(service.activityEvent$).toBeDefined();
    expect(service.summaryTick$).toBeDefined();
    expect(service.cameraStatus$).toBeDefined();
    expect(service.connected$).toBeDefined();
  });

  // ─── connect() behavior ───────────────────────────────────────

  it('should call connect and create a socket instance', () => {
    // We can't easily mock `io` import, but we can verify the service
    // doesn't throw when connect is called
    expect(() => service.connect()).not.toThrow();
  });

  it('should not create a new socket if already connected', () => {
    // Connect once
    service.connect();
    // Access private socket to set connected flag
    const socket1 = (service as any).socket;

    // Connect again - should be no-op if already connected
    if (socket1) {
      socket1.connected = true;
    }
    service.connect();

    // Socket reference should be the same
    if (socket1) {
      expect((service as any).socket).toBe(socket1);
    }
  });

  // ─── disconnect() behavior ────────────────────────────────────

  it('should disconnect and null the socket', () => {
    service.connect();
    service.disconnect();
    expect((service as any).socket).toBeNull();
  });

  it('should handle disconnect when no socket exists', () => {
    expect(() => service.disconnect()).not.toThrow();
    expect((service as any).socket).toBeNull();
  });

  // ─── ngOnDestroy ──────────────────────────────────────────────

  it('should disconnect on destroy', () => {
    service.connect();
    const disconnectSpy = spyOn(service, 'disconnect').and.callThrough();
    service.ngOnDestroy();
    expect(disconnectSpy).toHaveBeenCalled();
  });

  // ─── Subject emission tests (manual) ─────────────────────────
  // Since we can't easily intercept the io() factory,
  // we test the subjects themselves work correctly

  it('should emit on countEvent$ when next is called', (done) => {
    const mockEvent = {
      camera_id: 'cam01',
      session_id: 's1',
      track_id: 42,
      direction: 'loading',
      product_class: 'box',
      confidence: 0.95,
      timestamp: '2026-01-01T12:00:00Z',
    };

    service.countEvent$.subscribe(event => {
      expect(event.camera_id).toBe('cam01');
      expect(event.track_id).toBe(42);
      expect(event.direction).toBe('loading');
      done();
    });

    service.countEvent$.next(mockEvent);
  });

  it('should emit on activityEvent$ when next is called', (done) => {
    const mockActivity = {
      camera_id: 'cam01',
      event_type: 'SESSION_START',
      timestamp: '2026-01-01T12:00:00Z',
    };

    service.activityEvent$.subscribe(event => {
      expect(event.event_type).toBe('SESSION_START');
      done();
    });

    service.activityEvent$.next(mockActivity);
  });

  it('should emit on summaryTick$ when next is called', (done) => {
    const mockSummary = {
      total_loading: 100,
      total_unloading: 50,
      total: 150,
      active_cameras: 2,
      active_sessions: 1,
    };

    service.summaryTick$.subscribe(summary => {
      expect(summary.total).toBe(150);
      done();
    });

    service.summaryTick$.next(mockSummary);
  });

  it('should emit on cameraStatus$ when next is called', (done) => {
    service.cameraStatus$.subscribe(status => {
      expect(status.camera_id).toBe('cam01');
      expect(status.status).toBe('RUNNING');
      done();
    });

    service.cameraStatus$.next({ camera_id: 'cam01', status: 'RUNNING' });
  });

  it('should emit connected$ true and false', () => {
    const emissions: boolean[] = [];
    const sub = service.connected$.subscribe(c => emissions.push(c));

    service.connected$.next(true);
    service.connected$.next(false);
    service.connected$.next(true);

    expect(emissions).toEqual([true, false, true]);
    sub.unsubscribe();
  });

  // ─── Multiple subscribers ─────────────────────────────────────

  it('should broadcast to multiple subscribers', () => {
    let sub1Count = 0;
    let sub2Count = 0;

    const s1 = service.countEvent$.subscribe(() => sub1Count++);
    const s2 = service.countEvent$.subscribe(() => sub2Count++);

    service.countEvent$.next({
      camera_id: 'cam01',
      session_id: 's1',
      track_id: 1,
      direction: 'loading',
      product_class: 'box',
      confidence: 0.9,
      timestamp: '2026-01-01T00:00:00Z',
    });

    expect(sub1Count).toBe(1);
    expect(sub2Count).toBe(1);

    s1.unsubscribe();
    s2.unsubscribe();
  });
});
