import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';
import { LoginResponse } from '../models/api.models';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockLoginResponse: LoginResponse = {
    access_token: 'jwt-token-abc123',
    token_type: 'bearer',
    username: 'admin',
    role: 'ADMIN',
  };

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Router, useValue: routerSpy },
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  // ─── Happy Path ───────────────────────────────────────────────

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should return isLoggedIn false when no user in localStorage', () => {
    expect(service.isLoggedIn()).toBeFalse();
  });

  it('should return user as null when no user in localStorage', () => {
    expect(service.user()).toBeNull();
  });

  it('should return userRole as empty string when no user', () => {
    expect(service.userRole()).toBe('');
  });

  it('should POST credentials to /auth/login and store token + user on success', () => {
    service.login({ username: 'admin', password: 'secret' }).subscribe(res => {
      expect(res.access_token).toBe('jwt-token-abc123');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ username: 'admin', password: 'secret' });
    req.flush(mockLoginResponse);

    expect(localStorage.getItem('auth_token')).toBe('jwt-token-abc123');
    expect(JSON.parse(localStorage.getItem('auth_user')!)).toEqual({
      username: 'admin',
      role: 'ADMIN',
    });
    expect(service.isLoggedIn()).toBeTrue();
    expect(service.user()?.username).toBe('admin');
    expect(service.userRole()).toBe('ADMIN');
  });

  it('should update signals reactively after successful login', () => {
    expect(service.isLoggedIn()).toBeFalse();

    service.login({ username: 'admin', password: 'pass' }).subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/login`).flush(mockLoginResponse);

    expect(service.isLoggedIn()).toBeTrue();
    expect(service.user()?.username).toBe('admin');
    expect(service.userRole()).toBe('ADMIN');
  });

  it('should clear token, user, and navigate to /login on logout', () => {
    // Setup: first login
    service.login({ username: 'admin', password: 'pass' }).subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/login`).flush(mockLoginResponse);
    expect(service.isLoggedIn()).toBeTrue();

    service.logout();

    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(localStorage.getItem('auth_user')).toBeNull();
    expect(service.isLoggedIn()).toBeFalse();
    expect(service.user()).toBeNull();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should return token from getToken()', () => {
    localStorage.setItem('auth_token', 'my-jwt-token');
    expect(service.getToken()).toBe('my-jwt-token');
  });

  it('should return null from getToken() when no token stored', () => {
    expect(service.getToken()).toBeNull();
  });

  // ─── State Restoration (page refresh) ─────────────────────────

  it('should restore user from localStorage on construction', () => {
    localStorage.setItem('auth_user', JSON.stringify({ username: 'bob', role: 'OPERATOR' }));

    // Re-create service to trigger constructor
    const freshService = new AuthService(
      TestBed.inject(HttpTestingController) as any,
      routerSpy
    );
    // We need to use TestBed for proper DI, so test via a fresh TestBed instead
    TestBed.resetTestingModule();
    localStorage.setItem('auth_user', JSON.stringify({ username: 'bob', role: 'OPERATOR' }));
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Router, useValue: routerSpy },
      ],
    });
    const restoredService = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);

    expect(restoredService.isLoggedIn()).toBeTrue();
    expect(restoredService.user()?.username).toBe('bob');
    expect(restoredService.userRole()).toBe('OPERATOR');
  });

  // ─── Negative Path ────────────────────────────────────────────

  it('should propagate HTTP error on failed login without setting token', () => {
    let errorCaught = false;
    service.login({ username: 'wrong', password: 'wrong' }).subscribe({
      error: (err) => {
        errorCaught = true;
        expect(err.status).toBe(401);
      },
    });

    httpMock
      .expectOne(`${environment.apiUrl}/auth/login`)
      .flush({ detail: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });

    expect(errorCaught).toBeTrue();
    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(service.isLoggedIn()).toBeFalse();
  });

  it('should handle 500 server error on login', () => {
    let errorStatus = 0;
    service.login({ username: 'admin', password: 'pass' }).subscribe({
      error: (err) => { errorStatus = err.status; },
    });

    httpMock
      .expectOne(`${environment.apiUrl}/auth/login`)
      .flush('Server error', { status: 500, statusText: 'Internal Server Error' });

    expect(errorStatus).toBe(500);
    expect(service.isLoggedIn()).toBeFalse();
  });

  it('should handle network error on login', () => {
    let errorCaught = false;
    service.login({ username: 'admin', password: 'pass' }).subscribe({
      error: () => { errorCaught = true; },
    });

    httpMock
      .expectOne(`${environment.apiUrl}/auth/login`)
      .error(new ProgressEvent('Network error'));

    expect(errorCaught).toBeTrue();
    expect(service.isLoggedIn()).toBeFalse();
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle corrupted JSON in localStorage gracefully', () => {
    localStorage.setItem('auth_user', 'not-valid-json{{{');

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Router, useValue: routerSpy },
      ],
    });
    const svc = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);

    expect(svc.isLoggedIn()).toBeFalse();
    expect(svc.user()).toBeNull();
  });

  it('should handle empty string in localStorage for user', () => {
    localStorage.setItem('auth_user', '');

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Router, useValue: routerSpy },
      ],
    });
    const svc = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);

    expect(svc.isLoggedIn()).toBeFalse();
  });

  it('should allow multiple login/logout cycles', () => {
    // First login
    service.login({ username: 'admin', password: 'pass' }).subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/login`).flush(mockLoginResponse);
    expect(service.isLoggedIn()).toBeTrue();

    // Logout
    service.logout();
    expect(service.isLoggedIn()).toBeFalse();

    // Second login
    service.login({ username: 'operator', password: 'pass2' }).subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/login`).flush({
      ...mockLoginResponse,
      username: 'operator',
      role: 'OPERATOR',
    });
    expect(service.isLoggedIn()).toBeTrue();
    expect(service.user()?.username).toBe('operator');
  });

  it('should handle logout when already logged out without error', () => {
    expect(service.isLoggedIn()).toBeFalse();
    expect(() => service.logout()).not.toThrow();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });
});
