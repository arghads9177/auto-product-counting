import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { SessionsComponent } from './sessions.component';
import { ApiService } from '../../services/api.service';
import { Session } from '../../models/api.models';

describe('SessionsComponent', () => {
  let component: SessionsComponent;
  let fixture: ComponentFixture<SessionsComponent>;
  let apiSpy: jasmine.SpyObj<ApiService>;

  const mockSessions: Session[] = [
    {
      session_id: 'abcdef123456789',
      camera_id: 'cam01',
      status: 'ACTIVE',
      direction: 'loading',
      loading_count: 42,
      unloading_count: 5,
      started_at: '2026-06-01T10:00:00Z',
    },
    {
      session_id: 'xyz987654321abc',
      camera_id: 'cam02',
      status: 'COMPLETED',
      direction: 'unloading',
      loading_count: 0,
      unloading_count: 30,
      started_at: '2026-05-31T08:00:00Z',
      ended_at: '2026-05-31T12:00:00Z',
    },
  ];

  beforeEach(async () => {
    apiSpy = jasmine.createSpyObj('ApiService', ['getSessions', 'getSessionDetails']);
    apiSpy.getSessions.and.returnValue(of(mockSessions));

    await TestBed.configureTestingModule({
      imports: [SessionsComponent],
      providers: [{ provide: ApiService, useValue: apiSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(SessionsComponent);
    component = fixture.componentInstance;
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty filters and no selected session', () => {
    expect(component.filterStatus).toBe('');
    expect(component.filterCamera).toBe('');
    expect(component.selectedSession()).toBeNull();
  });

  // ─── ngOnInit: Load Sessions ──────────────────────────────────

  it('should load sessions on init', () => {
    fixture.detectChanges();
    expect(apiSpy.getSessions).toHaveBeenCalledWith(undefined, undefined);
    expect(component.sessions().length).toBe(2);
  });

  // ─── Sessions Table Rendering ─────────────────────────────────

  it('should render session rows in the table', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);
  });

  it('should display truncated session ID', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    // Session ID is sliced to first 12 chars + "..."
    expect(el.textContent).toContain('abcdef123456...');
  });

  it('should display camera_id, status, direction, counts', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('cam01');
    expect(el.textContent).toContain('ACTIVE');
    expect(el.textContent).toContain('loading');
    expect(el.textContent).toContain('42');
  });

  it('should display dash for missing direction', () => {
    apiSpy.getSessions.and.returnValue(of([{
      session_id: 'nodirection123456',
      camera_id: 'cam03',
      status: 'ACTIVE',
    }]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    expect(rows[0]?.textContent).toContain('-');
  });

  it('should display dash for missing ended_at', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    // First session (ACTIVE) has no ended_at
    const cells = rows[0]?.querySelectorAll('td');
    const endedCell = cells?.[7]; // last column
    expect(endedCell?.textContent?.trim()).toBe('-');
  });

  it('should show "No sessions found" when list is empty', () => {
    apiSpy.getSessions.and.returnValue(of([]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No sessions found');
  });

  // ─── Status Badge Styling ─────────────────────────────────────

  it('should apply green styling to ACTIVE status badge', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const activeBadge = el.querySelector('.bg-green-100.text-green-700');
    expect(activeBadge).toBeTruthy();
    expect(activeBadge?.textContent?.trim()).toBe('ACTIVE');
  });

  it('should apply gray styling to COMPLETED status badge', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const completedBadge = el.querySelector('.bg-gray-100.text-gray-700');
    expect(completedBadge).toBeTruthy();
    expect(completedBadge?.textContent?.trim()).toBe('COMPLETED');
  });

  // ─── Filtering ────────────────────────────────────────────────

  it('should reload sessions with status filter', () => {
    fixture.detectChanges();
    apiSpy.getSessions.calls.reset();

    component.filterStatus = 'ACTIVE';
    component.loadSessions();

    expect(apiSpy.getSessions).toHaveBeenCalledWith('ACTIVE', undefined);
  });

  it('should reload sessions with camera filter', () => {
    fixture.detectChanges();
    apiSpy.getSessions.calls.reset();

    component.filterCamera = 'cam01';
    component.loadSessions();

    expect(apiSpy.getSessions).toHaveBeenCalledWith(undefined, 'cam01');
  });

  it('should reload sessions with both filters', () => {
    fixture.detectChanges();
    apiSpy.getSessions.calls.reset();

    component.filterStatus = 'COMPLETED';
    component.filterCamera = 'cam02';
    component.loadSessions();

    expect(apiSpy.getSessions).toHaveBeenCalledWith('COMPLETED', 'cam02');
  });

  it('should pass undefined for empty string filters', () => {
    fixture.detectChanges();
    apiSpy.getSessions.calls.reset();

    component.filterStatus = '';
    component.filterCamera = '';
    component.loadSessions();

    expect(apiSpy.getSessions).toHaveBeenCalledWith(undefined, undefined);
  });

  // ─── Session Detail Modal ─────────────────────────────────────

  it('should set selectedSession when a session row is clicked', () => {
    fixture.detectChanges();
    component.selectSession(mockSessions[0]);
    expect(component.selectedSession()).toEqual(mockSessions[0]);
  });

  it('should render modal when selectedSession is set', () => {
    fixture.detectChanges();
    component.selectedSession.set(mockSessions[0]);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const modal = el.querySelector('.fixed.inset-0');
    expect(modal).toBeTruthy();
    expect(el.textContent).toContain('Session Details');
    expect(el.textContent).toContain('abcdef123456789');
  });

  it('should not render modal when selectedSession is null', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const modal = el.querySelector('.fixed.inset-0');
    expect(modal).toBeNull();
  });

  it('should close modal when close button is clicked', () => {
    fixture.detectChanges();
    component.selectedSession.set(mockSessions[0]);
    fixture.detectChanges();

    component.selectedSession.set(null);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const modal = el.querySelector('.fixed.inset-0');
    expect(modal).toBeNull();
  });

  it('should display session details in modal', () => {
    fixture.detectChanges();
    component.selectedSession.set(mockSessions[0]);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const modal = el.querySelector('.fixed.inset-0');
    expect(modal?.textContent).toContain('cam01');
    expect(modal?.textContent).toContain('ACTIVE');
    expect(modal?.textContent).toContain('loading');
    expect(modal?.textContent).toContain('42');
    expect(modal?.textContent).toContain('5');
  });

  it('should display 0 for missing counts in modal', () => {
    const sessionNoCount: Session = {
      session_id: 'nocounts1234567',
      camera_id: 'cam03',
      status: 'ACTIVE',
    };
    component.selectedSession.set(sessionNoCount);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const modal = el.querySelector('.fixed.inset-0');
    expect(modal?.textContent).toContain('0');
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle sessions with zero counts', () => {
    apiSpy.getSessions.and.returnValue(of([{
      session_id: 'zerocounts12345',
      camera_id: 'cam01',
      status: 'COMPLETED',
      direction: 'loading',
      loading_count: 0,
      unloading_count: 0,
      started_at: '2026-01-01T00:00:00Z',
      ended_at: '2026-01-01T01:00:00Z',
    }]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('0');
  });

  // ─── Filter UI Elements ───────────────────────────────────────

  it('should render status filter dropdown with correct options', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const select = el.querySelector('select') as HTMLSelectElement;
    expect(select).toBeTruthy();

    const options = select.querySelectorAll('option');
    expect(options.length).toBe(3); // All, Active, Completed
    expect(options[0].value).toBe('');
    expect(options[1].value).toBe('ACTIVE');
    expect(options[2].value).toBe('COMPLETED');
  });

  it('should render camera ID filter input', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[placeholder="e.g. cam01"]') as HTMLInputElement;
    expect(input).toBeTruthy();
  });
});
