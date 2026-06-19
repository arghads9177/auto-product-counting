import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError, Subject } from 'rxjs';
import { CamerasComponent } from './cameras.component';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { SocketService } from '../../services/socket.service';
import { Camera } from '../../models/api.models';

describe('CamerasComponent', () => {
  let component: CamerasComponent;
  let fixture: ComponentFixture<CamerasComponent>;
  let apiSpy: jasmine.SpyObj<ApiService>;
  let authSpy: jasmine.SpyObj<AuthService>;
  let socketService: {
    connect: jasmine.Spy;
    disconnect: jasmine.Spy;
    cameraStatus$: Subject<{ camera_id: string; status: string }>;
    countEvent$: Subject<any>;
    activityEvent$: Subject<any>;
    summaryTick$: Subject<any>;
    connected$: Subject<boolean>;
  };

  const mockCameras: Camera[] = [
    { camera_id: 'cam01', name: 'Dock Bay 1', status: 'RUNNING' },
    { camera_id: 'cam02', name: 'Dock Bay 2', status: 'STOPPED' },
  ];

  beforeEach(async () => {
    apiSpy = jasmine.createSpyObj('ApiService', [
      'listCameras',
      'addCamera',
      'startCamera',
      'stopCamera',
      'getStreamUrl',
    ]);
    apiSpy.listCameras.and.returnValue(of(mockCameras));
    apiSpy.getStreamUrl.and.callFake((id: string) => `http://localhost:8000/stream/${id}.mjpeg`);

    authSpy = jasmine.createSpyObj('AuthService', ['logout', 'getToken'], {
      userRole: jasmine.createSpy('userRole').and.returnValue('ADMIN'),
      user: jasmine.createSpy('user').and.returnValue({ username: 'admin', role: 'ADMIN' }),
      isLoggedIn: jasmine.createSpy('isLoggedIn').and.returnValue(true),
    });

    socketService = {
      connect: jasmine.createSpy('connect'),
      disconnect: jasmine.createSpy('disconnect'),
      cameraStatus$: new Subject(),
      countEvent$: new Subject(),
      activityEvent$: new Subject(),
      summaryTick$: new Subject(),
      connected$: new Subject(),
    };

    await TestBed.configureTestingModule({
      imports: [CamerasComponent],
      providers: [
        { provide: ApiService, useValue: apiSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: SocketService, useValue: socketService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CamerasComponent);
    component = fixture.componentInstance;
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty cameras and hidden add form', () => {
    expect(component.cameras()).toEqual([]);
    expect(component.showAdd()).toBeFalse();
    expect(component.addingCamera()).toBeFalse();
  });

  // ─── ngOnInit: Load Cameras ───────────────────────────────────

  it('should load cameras on init', () => {
    fixture.detectChanges();
    expect(apiSpy.listCameras).toHaveBeenCalled();
    expect(component.cameras().length).toBe(2);
  });

  it('should subscribe to camera status updates', () => {
    fixture.detectChanges();
    apiSpy.listCameras.calls.reset();

    // Emit a camera status change
    socketService.cameraStatus$.next({ camera_id: 'cam01', status: 'STOPPED' });

    expect(apiSpy.listCameras).toHaveBeenCalled();
  });

  // ─── Camera Grid Rendering ────────────────────────────────────

  it('should render camera cards for each camera', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const cards = el.querySelectorAll('.bg-white.rounded-xl.shadow-sm.border.overflow-hidden');
    expect(cards.length).toBe(2);
  });

  it('should display camera name and id', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Dock Bay 1');
    expect(el.textContent).toContain('cam01');
    expect(el.textContent).toContain('Dock Bay 2');
    expect(el.textContent).toContain('cam02');
  });

  it('should display MJPEG stream img for RUNNING cameras', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const imgs = el.querySelectorAll('img');
    // Only cam01 is RUNNING
    expect(imgs.length).toBe(1);
    expect(imgs[0].src).toContain('/stream/cam01.mjpeg');
  });

  it('should display "Camera offline" for STOPPED cameras', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Camera offline');
  });

  it('should display status badge on camera card', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('RUNNING');
    expect(el.textContent).toContain('STOPPED');
  });

  it('should show Start button for stopped cameras', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('button');
    const startBtn = Array.from(buttons).find(b => b.textContent?.trim() === 'Start');
    expect(startBtn).toBeTruthy();
  });

  it('should show Stop button for running cameras', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('button');
    const stopBtn = Array.from(buttons).find(b => b.textContent?.trim() === 'Stop');
    expect(stopBtn).toBeTruthy();
  });

  // ─── Empty State ──────────────────────────────────────────────

  it('should show empty state when no cameras registered', () => {
    apiSpy.listCameras.and.returnValue(of([]));
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No cameras registered');
    expect(el.textContent).toContain('Add a camera to get started');
  });

  // ─── Admin: Add Camera ────────────────────────────────────────

  it('should show "Add Camera" button for ADMIN users', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('button');
    const addBtn = Array.from(buttons).find(b => b.textContent?.trim() === 'Add Camera');
    expect(addBtn).toBeTruthy();
  });

  it('should hide "Add Camera" button for non-ADMIN users', () => {
    (authSpy.userRole as jasmine.Spy).and.returnValue('OPERATOR');
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('button');
    const addBtn = Array.from(buttons).find(b => b.textContent?.trim() === 'Add Camera');
    expect(addBtn).toBeFalsy();
  });

  it('should toggle add camera form on button click', () => {
    fixture.detectChanges();
    expect(component.showAdd()).toBeFalse();

    component.showAdd.set(true);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Add New Camera');
  });

  it('should display form fields for new camera', () => {
    fixture.detectChanges();
    component.showAdd.set(true);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const inputs = el.querySelectorAll('input');
    // There are 3 inputs: Camera ID, Name, RTSP URL
    // (plus other inputs in the DOM outside the form)
    expect(el.textContent).toContain('Camera ID');
    expect(el.textContent).toContain('RTSP URL');
  });

  // ─── Add Camera: Happy Path ───────────────────────────────────

  it('should call api.addCamera with correct params', () => {
    const newCam: Camera = { camera_id: 'cam03', name: 'Bay 3', status: 'STOPPED' };
    apiSpy.addCamera.and.returnValue(of(newCam));

    component.newCameraId = 'cam03';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.addCamera();

    expect(apiSpy.addCamera).toHaveBeenCalledWith('cam03', 'Bay 3', 'rtsp://localhost:8554/cam03');
  });

  it('should reset form and reload cameras after successful add', () => {
    apiSpy.addCamera.and.returnValue(of({ camera_id: 'cam03', name: 'Bay 3', status: 'STOPPED' }));
    apiSpy.listCameras.calls.reset();

    component.newCameraId = 'cam03';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.showAdd.set(true);
    component.addCamera();

    expect(component.newCameraId).toBe('');
    expect(component.newCameraName).toBe('');
    expect(component.newRtspUrl).toBe('');
    expect(component.showAdd()).toBeFalse();
    expect(component.addingCamera()).toBeFalse();
    expect(apiSpy.listCameras).toHaveBeenCalled();
  });

  // ─── Add Camera: Validation ───────────────────────────────────

  it('should not call api.addCamera when camera ID is empty', () => {
    component.newCameraId = '';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.addCamera();

    expect(apiSpy.addCamera).not.toHaveBeenCalled();
  });

  it('should not call api.addCamera when name is empty', () => {
    component.newCameraId = 'cam03';
    component.newCameraName = '';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.addCamera();

    expect(apiSpy.addCamera).not.toHaveBeenCalled();
  });

  it('should not call api.addCamera when RTSP URL is empty', () => {
    component.newCameraId = 'cam03';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = '';
    component.addCamera();

    expect(apiSpy.addCamera).not.toHaveBeenCalled();
  });

  // ─── Add Camera: Error Handling ───────────────────────────────

  it('should reset addingCamera flag on error', () => {
    apiSpy.addCamera.and.returnValue(throwError(() => ({ status: 409 })));

    component.newCameraId = 'cam03';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.addCamera();

    expect(component.addingCamera()).toBeFalse();
  });

  it('should not clear form fields on add error', () => {
    apiSpy.addCamera.and.returnValue(throwError(() => ({ status: 500 })));

    component.newCameraId = 'cam03';
    component.newCameraName = 'Bay 3';
    component.newRtspUrl = 'rtsp://localhost:8554/cam03';
    component.addCamera();

    expect(component.newCameraId).toBe('cam03');
    expect(component.newCameraName).toBe('Bay 3');
  });

  // ─── Start/Stop Camera ────────────────────────────────────────

  it('should call api.startCamera and reload cameras on success', () => {
    apiSpy.startCamera.and.returnValue(of({}));
    apiSpy.listCameras.calls.reset();

    component.startCamera('cam02');

    expect(apiSpy.startCamera).toHaveBeenCalledWith('cam02');
    expect(apiSpy.listCameras).toHaveBeenCalled();
  });

  it('should call api.stopCamera and reload cameras on success', () => {
    apiSpy.stopCamera.and.returnValue(of({}));
    apiSpy.listCameras.calls.reset();

    component.stopCamera('cam01');

    expect(apiSpy.stopCamera).toHaveBeenCalledWith('cam01');
    expect(apiSpy.listCameras).toHaveBeenCalled();
  });

  // ─── ngOnDestroy ──────────────────────────────────────────────

  it('should unsubscribe on destroy', () => {
    fixture.detectChanges();
    const subsSpy = spyOn((component as any).subs, 'unsubscribe');
    component.ngOnDestroy();
    expect(subsSpy).toHaveBeenCalled();
  });

  // ─── Realtime Camera Status ───────────────────────────────────

  it('should refresh camera list when cameraStatus$ emits', () => {
    fixture.detectChanges();
    apiSpy.listCameras.calls.reset();

    socketService.cameraStatus$.next({ camera_id: 'cam01', status: 'STOPPED' });

    expect(apiSpy.listCameras).toHaveBeenCalledTimes(1);
  });

  it('should handle multiple rapid status updates', () => {
    fixture.detectChanges();
    apiSpy.listCameras.calls.reset();

    socketService.cameraStatus$.next({ camera_id: 'cam01', status: 'STOPPED' });
    socketService.cameraStatus$.next({ camera_id: 'cam02', status: 'RUNNING' });
    socketService.cameraStatus$.next({ camera_id: 'cam01', status: 'RUNNING' });

    expect(apiSpy.listCameras).toHaveBeenCalledTimes(3);
  });

  // ─── Accessibility ────────────────────────────────────────────

  it('should have alt text on MJPEG stream images', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const img = el.querySelector('img') as HTMLImageElement;
    expect(img?.alt).toBe('Dock Bay 1');
  });

  it('should have lazy loading attribute on stream images', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const img = el.querySelector('img') as HTMLImageElement;
    expect(img?.loading).toBe('lazy');
  });
});
