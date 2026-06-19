import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { LogsComponent } from './logs.component';
import { ApiService } from '../../services/api.service';
import { SystemLog } from '../../models/api.models';

describe('LogsComponent', () => {
  let component: LogsComponent;
  let fixture: ComponentFixture<LogsComponent>;
  let apiSpy: jasmine.SpyObj<ApiService>;

  const mockLogs: SystemLog[] = [
    {
      category: 'SYSTEM',
      severity: 'INFO',
      message: 'Camera cam01 started successfully',
      camera_id: 'cam01',
      timestamp: '2026-06-01T10:00:00Z',
    },
    {
      category: 'DETECTION',
      severity: 'WARNING',
      message: 'Low confidence detection',
      camera_id: 'cam02',
      timestamp: '2026-06-01T10:05:00Z',
    },
    {
      category: 'SESSION',
      severity: 'ERROR',
      message: 'Session timeout exceeded',
      timestamp: '2026-06-01T10:10:00Z',
    },
  ];

  beforeEach(async () => {
    apiSpy = jasmine.createSpyObj('ApiService', ['getLogs']);
    apiSpy.getLogs.and.returnValue(of(mockLogs));

    await TestBed.configureTestingModule({
      imports: [LogsComponent],
      providers: [{ provide: ApiService, useValue: apiSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(LogsComponent);
    component = fixture.componentInstance;
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty filters', () => {
    expect(component.filterSeverity).toBe('');
    expect(component.filterCategory).toBe('');
    expect(component.filterCamera).toBe('');
  });

  // ─── ngOnInit: Load Logs ──────────────────────────────────────

  it('should load logs on init', () => {
    fixture.detectChanges();
    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, undefined, undefined, undefined);
    expect(component.logs().length).toBe(3);
  });

  // ─── Table Rendering ──────────────────────────────────────────

  it('should render heading', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h2')?.textContent).toContain('System Logs');
  });

  it('should render table with correct headers', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const headers = el.querySelectorAll('thead th');
    expect(headers.length).toBe(5);
    expect(headers[0].textContent).toContain('Time');
    expect(headers[1].textContent).toContain('Severity');
    expect(headers[2].textContent).toContain('Category');
    expect(headers[3].textContent).toContain('Camera');
    expect(headers[4].textContent).toContain('Message');
  });

  it('should render log rows', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    expect(rows.length).toBe(3);
  });

  it('should display log message text', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Camera cam01 started successfully');
    expect(el.textContent).toContain('Low confidence detection');
    expect(el.textContent).toContain('Session timeout exceeded');
  });

  it('should display dash for log without camera_id', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    // Third log has no camera_id
    const cells = rows[2]?.querySelectorAll('td');
    expect(cells?.[3]?.textContent?.trim()).toBe('-');
  });

  // ─── Severity Badge Styling ───────────────────────────────────

  it('should apply blue styling to INFO severity badge', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const infoBadge = el.querySelector('.bg-blue-100.text-blue-700');
    expect(infoBadge).toBeTruthy();
    expect(infoBadge?.textContent?.trim()).toBe('INFO');
  });

  it('should apply yellow styling to WARNING severity badge', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const warnBadge = el.querySelector('.bg-yellow-100.text-yellow-700');
    expect(warnBadge).toBeTruthy();
    expect(warnBadge?.textContent?.trim()).toBe('WARNING');
  });

  it('should apply red styling to ERROR severity badge', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const errorBadge = el.querySelector('.bg-red-100.text-red-700');
    expect(errorBadge).toBeTruthy();
    expect(errorBadge?.textContent?.trim()).toBe('ERROR');
  });

  // ─── Empty State ──────────────────────────────────────────────

  it('should show "No logs found" when logs list is empty', () => {
    apiSpy.getLogs.and.returnValue(of([]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No logs found');
  });

  // ─── Filtering ────────────────────────────────────────────────

  it('should reload logs with severity filter', () => {
    fixture.detectChanges();
    apiSpy.getLogs.calls.reset();

    component.filterSeverity = 'ERROR';
    component.loadLogs();

    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, undefined, 'ERROR', undefined);
  });

  it('should reload logs with category filter', () => {
    fixture.detectChanges();
    apiSpy.getLogs.calls.reset();

    component.filterCategory = 'DETECTION';
    component.loadLogs();

    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, 'DETECTION', undefined, undefined);
  });

  it('should reload logs with camera filter', () => {
    fixture.detectChanges();
    apiSpy.getLogs.calls.reset();

    component.filterCamera = 'cam01';
    component.loadLogs();

    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, undefined, undefined, 'cam01');
  });

  it('should reload logs with all filters combined', () => {
    fixture.detectChanges();
    apiSpy.getLogs.calls.reset();

    component.filterSeverity = 'WARNING';
    component.filterCategory = 'TRACKING';
    component.filterCamera = 'cam02';
    component.loadLogs();

    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, 'TRACKING', 'WARNING', 'cam02');
  });

  it('should pass undefined for empty string filters', () => {
    fixture.detectChanges();
    apiSpy.getLogs.calls.reset();

    component.filterSeverity = '';
    component.filterCategory = '';
    component.filterCamera = '';
    component.loadLogs();

    expect(apiSpy.getLogs).toHaveBeenCalledWith(100, undefined, undefined, undefined);
  });

  // ─── Filter UI Elements ───────────────────────────────────────

  it('should render severity filter with correct options', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const selects = el.querySelectorAll('select');

    // First select is severity
    const severitySelect = selects[0];
    const options = severitySelect.querySelectorAll('option');
    expect(options.length).toBe(4); // All, Info, Warning, Error
    expect(options[0].value).toBe('');
    expect(options[1].value).toBe('INFO');
    expect(options[2].value).toBe('WARNING');
    expect(options[3].value).toBe('ERROR');
  });

  it('should render category filter with correct options', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const selects = el.querySelectorAll('select');

    // Second select is category
    const categorySelect = selects[1];
    const options = categorySelect.querySelectorAll('option');
    expect(options.length).toBe(5); // All, System, Detection, Tracking, Session
    expect(options[1].value).toBe('SYSTEM');
    expect(options[2].value).toBe('DETECTION');
    expect(options[3].value).toBe('TRACKING');
    expect(options[4].value).toBe('SESSION');
  });

  it('should render camera ID filter input', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const input = el.querySelector('input[placeholder="e.g. cam01"]') as HTMLInputElement;
    expect(input).toBeTruthy();
  });

  // ─── Filter labels (Accessibility) ────────────────────────────

  it('should have labels for all filter controls', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const labels = el.querySelectorAll('label');
    const labelTexts = Array.from(labels).map(l => l.textContent?.trim());
    expect(labelTexts).toContain('Severity');
    expect(labelTexts).toContain('Category');
    expect(labelTexts).toContain('Camera ID');
  });
});
