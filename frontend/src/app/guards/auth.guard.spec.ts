import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

describe('authGuard', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;
  const mockRoute = {} as ActivatedRouteSnapshot;
  const mockState = {} as RouterStateSnapshot;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['getToken'], {
      isLoggedIn: jasmine.createSpy('isLoggedIn'),
    });
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
  });

  // ─── Happy Path ───────────────────────────────────────────────

  it('should allow access when user is logged in', () => {
    (authServiceSpy.isLoggedIn as jasmine.Spy).and.returnValue(true);

    const result = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));

    expect(result).toBeTrue();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });

  // ─── Negative Path ────────────────────────────────────────────

  it('should deny access and redirect to /login when user is not logged in', () => {
    (authServiceSpy.isLoggedIn as jasmine.Spy).and.returnValue(false);

    const result = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));

    expect(result).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should redirect to /login only once per guard invocation', () => {
    (authServiceSpy.isLoggedIn as jasmine.Spy).and.returnValue(false);

    TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));

    expect(routerSpy.navigate).toHaveBeenCalledTimes(1);
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle the guard being invoked multiple times in sequence', () => {
    (authServiceSpy.isLoggedIn as jasmine.Spy).and.returnValues(false, true, false);

    const r1 = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));
    expect(r1).toBeFalse();

    const r2 = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));
    expect(r2).toBeTrue();

    const r3 = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));
    expect(r3).toBeFalse();

    // Navigate called twice (for the two false returns)
    expect(routerSpy.navigate).toHaveBeenCalledTimes(2);
  });
});
