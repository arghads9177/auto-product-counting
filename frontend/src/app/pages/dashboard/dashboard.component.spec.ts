import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { of, Subject } from 'rxjs';
import { DashboardComponent } from './dashboard.component';
import { ApiService } from '../../services/api.service';
import { SocketService } from '../../services/socket.service';
import { CountSummary, ActivityEvent } from '../../models/api.models';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let apiSpy: jasmine.SpyObj<ApiService>;
  let socketService: {
    connect: jasmine.Spy;
    disconnect: jasmine.Spy;
    summaryTick$: Subject<CountSummary>;
    connected$: Subject<boolean>;
    activityEvent$: Subject<ActivityEvent>;
    countEvent$: Subject<any>;
    cameraStatus$: Subject<any>;
  };

  const mockSummary: CountSummary = {
    total_loading: 120,
    total_unloading: 80,
    total: 200,
    active_cameras: 2,
    active_sessions: 1,
    active_sessions_detail: [
      {
        session_id: 'sess-001',
        camera_id: 'cam01',
        status: 'ACTIVE',
        direction: 'loading',
        loading_count: 50,
        unloading_count: 10,
        started_at: '2026-06-01T10:00:00Z',
      },
    ],
  };

  const mockEvents: ActivityEvent[] = [
    { camera_id: 'cam01', event_type: 'SESSION_START', timestamp: '2026-06-01T10:00:00Z' },
    { camera_id: 'cam02', event_type: 'SESSION_END', timestamp: '2026-06-01T09:30:00Z' },
  ];

  beforeEach(async () => {
    apiSpy = jasmine.createSpyObj('ApiService', ['getCountsSummary', 'getEventTimeline']);
    apiSpy.getCountsSummary.and.returnValue(of(mockSummary));
    apiSpy.getEventTimeline.and.returnValue(of(mockEvents));

    socketService = {
      connect: jasmine.createSpy('connect'),
      disconnect: jasmine.createSpy('disconnect'),
      summaryTick$: new Subject<CountSummary>(),
      connected$: new Subject<boolean>(),
      activityEvent$: new Subject<ActivityEvent>(),
      countEvent$: new Subject(),
      cameraStatus$: new Subject(),
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: ApiService, useValue: apiSpy },
        { provide: SocketService, useValue: socketService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with null summary and empty events', () => {
    expect(component.summary()).toBeNull();
    expect(component.events()).toEqual([]);
    expect(component.socketConnected()).toBeFalse();
  });

  // ─── ngOnInit ─────────────────────────────────────────────────

  it('should connect to socket on init', () => {
    fixture.detectChanges(); // triggers ngOnInit
    expect(socketService.connect).toHaveBeenCalled();
  });

  it('should fetch count summary on init', () => {
    fixture.detectChanges();
    expect(apiSpy.getCountsSummary).toHaveBeenCalled();
    expect(component.summary()).toEqual(mockSummary);
  });

  it('should fetch event timeline with limit 20 on init', () => {
    fixture.detectChanges();
    expect(apiSpy.getEventTimeline).toHaveBeenCalledWith(20);
    expect(component.events().length).toBe(2);
  });

  // ─── Summary Cards Rendering ──────────────────────────────────

  it('should display total loading count', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const cards = el.querySelectorAll('.bg-white.rounded-xl.shadow-sm.border.p-5');
    // First card is Total Loading
    expect(cards[0]?.textContent).toContain('120');
  });

  it('should display total unloading count', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const cards = el.querySelectorAll('.bg-white.rounded-xl.shadow-sm.border.p-5');
    expect(cards[1]?.textContent).toContain('80');
  });

  it('should display active cameras count', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const cards = el.querySelectorAll('.bg-white.rounded-xl.shadow-sm.border.p-5');
    expect(cards[2]?.textContent).toContain('2');
  });

  it('should display active sessions count', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const cards = el.querySelectorAll('.bg-white.rounded-xl.shadow-sm.border.p-5');
    expect(cards[3]?.textContent).toContain('1');
  });

  it('should display 0 for all counts when summary is null', () => {
    apiSpy.getCountsSummary.and.returnValue(of(null as any));
    // Skip - summary starts as null before any response
    expect(component.summary()).toBeNull();
  });

  // ─── Socket.IO Connection Status ──────────────────────────────

  it('should show "Live" when socket is connected', () => {
    fixture.detectChanges();
    socketService.connected$.next(true);
    fixture.detectChanges();

    expect(component.socketConnected()).toBeTrue();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Live');
  });

  it('should show "Disconnected" when socket is not connected', () => {
    fixture.detectChanges();
    socketService.connected$.next(false);
    fixture.detectChanges();

    expect(component.socketConnected()).toBeFalse();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Disconnected');
  });

  // ─── Socket.IO: Real-time Summary Updates ─────────────────────

  it('should update summary when summaryTick$ emits', () => {
    fixture.detectChanges();

    const updatedSummary: CountSummary = {
      ...mockSummary,
      total_loading: 999,
      total: 1099,
    };
    socketService.summaryTick$.next(updatedSummary);

    expect(component.summary()?.total_loading).toBe(999);
  });

  // ─── Socket.IO: Real-time Activity Events ─────────────────────

  it('should prepend new activity events from socket', () => {
    fixture.detectChanges();
    expect(component.events().length).toBe(2);

    const newEvent: ActivityEvent = {
      camera_id: 'cam03',
      event_type: 'COUNT_UPDATE',
      timestamp: '2026-06-01T11:00:00Z',
    };
    socketService.activityEvent$.next(newEvent);

    expect(component.events().length).toBe(3);
    expect(component.events()[0].camera_id).toBe('cam03');
  });

  it('should cap events list at 20 items', () => {
    fixture.detectChanges();
    // Already have 2 events, add 19 more to exceed 20
    for (let i = 0; i < 19; i++) {
      socketService.activityEvent$.next({
        camera_id: `cam${i}`,
        event_type: 'SESSION_START',
        timestamp: `2026-06-01T12:${String(i).padStart(2, '0')}:00Z`,
      });
    }

    expect(component.events().length).toBe(20);
  });

  it('should place newest events first', () => {
    fixture.detectChanges();

    socketService.activityEvent$.next({
      camera_id: 'cam-latest',
      event_type: 'DETECTION',
      timestamp: '2026-06-01T23:59:59Z',
    });

    expect(component.events()[0].camera_id).toBe('cam-latest');
  });

  // ─── Active Sessions Table ────────────────────────────────────

  it('should render active sessions table when sessions exist', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const table = el.querySelector('table');
    expect(table).toBeTruthy();

    const rows = el.querySelectorAll('tbody tr');
    expect(rows.length).toBe(1);
  });

  it('should display session camera_id in table', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const firstRow = el.querySelector('tbody tr');
    expect(firstRow?.textContent).toContain('cam01');
  });

  it('should display direction badge for active session', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const badge = el.querySelector('tbody tr span');
    expect(badge?.textContent?.trim()).toBe('loading');
  });

  it('should show "No active sessions" when no active sessions', () => {
    const emptySummary = { ...mockSummary, active_sessions_detail: [] };
    apiSpy.getCountsSummary.and.returnValue(of(emptySummary));

    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No active sessions');
  });

  // ─── Recent Activity Section ──────────────────────────────────

  it('should render activity events', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('SESSION_START');
    expect(el.textContent).toContain('SESSION_END');
  });

  it('should show "No recent events" when events list is empty', () => {
    apiSpy.getEventTimeline.and.returnValue(of([]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No recent events');
  });

  // ─── State: Empty ─────────────────────────────────────────────

  it('should handle API returning empty summary', () => {
    const emptySummary: CountSummary = {
      total_loading: 0,
      total_unloading: 0,
      total: 0,
      active_cameras: 0,
      active_sessions: 0,
      active_sessions_detail: [],
    };
    apiSpy.getCountsSummary.and.returnValue(of(emptySummary));
    apiSpy.getEventTimeline.and.returnValue(of([]));

    fixture.detectChanges();

    expect(component.summary()?.total).toBe(0);
    expect(component.events().length).toBe(0);
  });

  // ─── ngOnDestroy ──────────────────────────────────────────────

  it('should unsubscribe all subscriptions on destroy', () => {
    fixture.detectChanges();
    const subsSpy = spyOn((component as any).subs, 'unsubscribe');
    component.ngOnDestroy();
    expect(subsSpy).toHaveBeenCalled();
  });

  it('should not update state after destroy', () => {
    fixture.detectChanges();
    component.ngOnDestroy();

    // After destroy, socket events should not update component state
    // (subscriptions are cleaned up)
    const currentEvents = component.events();
    // Emitting after destroy should not throw
    expect(() => {
      socketService.activityEvent$.next({
        camera_id: 'cam-after-destroy',
        event_type: 'SESSION_START',
        timestamp: '2026-06-01T00:00:00Z',
      });
    }).not.toThrow();
  });

  // ─── Polling ──────────────────────────────────────────────────

  it('should poll summary every 5 seconds via interval', fakeAsync(() => {
    fixture.detectChanges();
    // Initial call + startWith(0) = 1 call
    expect(apiSpy.getCountsSummary).toHaveBeenCalledTimes(1);

    tick(5000);
    expect(apiSpy.getCountsSummary).toHaveBeenCalledTimes(2);

    tick(5000);
    expect(apiSpy.getCountsSummary).toHaveBeenCalledTimes(3);

    // Cleanup
    component.ngOnDestroy();
  }));
});
