import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['getToken']);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceSpy },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  // ─── Happy Path ───────────────────────────────────────────────

  it('should add Authorization header when token exists', () => {
    authServiceSpy.getToken.and.returnValue('my-jwt-token');

    httpClient.get('/api/test').subscribe();

    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-jwt-token');
    req.flush({});
  });

  it('should use the correct Bearer prefix format', () => {
    authServiceSpy.getToken.and.returnValue('abc123');

    httpClient.get('/api/cameras').subscribe();

    const req = httpMock.expectOne('/api/cameras');
    const authHeader = req.request.headers.get('Authorization');
    expect(authHeader).toMatch(/^Bearer .+/);
    req.flush({});
  });

  // ─── No Token ─────────────────────────────────────────────────

  it('should not add Authorization header when token is null', () => {
    authServiceSpy.getToken.and.returnValue(null);

    httpClient.get('/api/test').subscribe();

    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  // ─── Preserves existing headers ───────────────────────────────

  it('should preserve existing request headers when adding auth', () => {
    authServiceSpy.getToken.and.returnValue('token123');

    httpClient
      .get('/api/data', { headers: { 'X-Custom-Header': 'custom-value' } })
      .subscribe();

    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer token123');
    expect(req.request.headers.get('X-Custom-Header')).toBe('custom-value');
    req.flush({});
  });

  // ─── Different HTTP methods ───────────────────────────────────

  it('should add auth header to POST requests', () => {
    authServiceSpy.getToken.and.returnValue('token-post');

    httpClient.post('/api/cameras', { name: 'test' }).subscribe();

    const req = httpMock.expectOne('/api/cameras');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-post');
    req.flush({});
  });

  it('should add auth header to PUT requests', () => {
    authServiceSpy.getToken.and.returnValue('token-put');

    httpClient.put('/api/cameras/cam01/config', {}).subscribe();

    const req = httpMock.expectOne('/api/cameras/cam01/config');
    expect(req.request.method).toBe('PUT');
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-put');
    req.flush({});
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle token with special characters', () => {
    authServiceSpy.getToken.and.returnValue('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U');

    httpClient.get('/api/test').subscribe();

    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.get('Authorization')).toContain('Bearer eyJhbGciOiJIUzI1NiI');
    req.flush({});
  });

  it('should intercept multiple sequential requests', () => {
    authServiceSpy.getToken.and.returnValue('token-seq');

    httpClient.get('/api/cameras').subscribe();
    httpClient.get('/api/sessions').subscribe();

    const reqs = httpMock.match(() => true);
    expect(reqs.length).toBe(2);
    reqs.forEach(req => {
      expect(req.request.headers.get('Authorization')).toBe('Bearer token-seq');
      req.flush({});
    });
  });
});
