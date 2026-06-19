import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../services/auth.service';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty credentials', () => {
    expect(component.username).toBe('');
    expect(component.password).toBe('');
  });

  it('should initialize with loading false and empty error', () => {
    expect(component.loading()).toBeFalse();
    expect(component.error()).toBe('');
  });

  // ─── Template Rendering ───────────────────────────────────────

  it('should render the sign-in heading', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('Product Counter');
  });

  it('should render username and password inputs', () => {
    const el: HTMLElement = fixture.nativeElement;
    const usernameInput = el.querySelector('input#username') as HTMLInputElement;
    const passwordInput = el.querySelector('input#password') as HTMLInputElement;

    expect(usernameInput).toBeTruthy();
    expect(passwordInput).toBeTruthy();
    expect(passwordInput.type).toBe('password');
  });

  it('should render submit button with "Sign In" text', () => {
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.textContent?.trim()).toContain('Sign In');
  });

  it('should not display error message initially', () => {
    const el: HTMLElement = fixture.nativeElement;
    const errorDiv = el.querySelector('.bg-red-50');
    expect(errorDiv).toBeNull();
  });

  // ─── Happy Path: Successful Login ─────────────────────────────

  it('should call auth.login with credentials on form submit', () => {
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: 'admin', role: 'ADMIN' })
    );

    component.username = 'admin';
    component.password = 'secret';
    component.onSubmit();

    expect(authServiceSpy.login).toHaveBeenCalledWith({
      username: 'admin',
      password: 'secret',
    });
  });

  it('should navigate to /dashboard on successful login', () => {
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: 'admin', role: 'ADMIN' })
    );

    component.username = 'admin';
    component.password = 'pass';
    component.onSubmit();

    expect(routerSpy.navigate).toHaveBeenCalledWith(['/dashboard']);
  });

  it('should set loading to true during login and false after success', () => {
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: 'admin', role: 'ADMIN' })
    );

    component.username = 'admin';
    component.password = 'pass';

    // Cannot check intermediate loading state with sync observable,
    // but we can verify final state
    component.onSubmit();

    expect(component.loading()).toBeFalse();
  });

  it('should clear previous error on new submission', () => {
    component.error.set('Old error');
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: 'admin', role: 'ADMIN' })
    );

    component.username = 'admin';
    component.password = 'pass';
    component.onSubmit();

    expect(component.error()).toBe('');
  });

  // ─── Negative Path: Validation ────────────────────────────────

  it('should not call login when username is empty', () => {
    component.username = '';
    component.password = 'pass';
    component.onSubmit();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
  });

  it('should not call login when password is empty', () => {
    component.username = 'admin';
    component.password = '';
    component.onSubmit();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
  });

  it('should not call login when both fields are empty', () => {
    component.username = '';
    component.password = '';
    component.onSubmit();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
  });

  // ─── Negative Path: Server Errors ─────────────────────────────

  it('should display server error detail on 401', () => {
    authServiceSpy.login.and.returnValue(
      throwError(() => ({
        status: 401,
        error: { detail: 'Invalid credentials' },
      }))
    );

    component.username = 'wrong';
    component.password = 'wrong';
    component.onSubmit();

    expect(component.error()).toBe('Invalid credentials');
    expect(component.loading()).toBeFalse();
  });

  it('should display generic error when no detail in response', () => {
    authServiceSpy.login.and.returnValue(
      throwError(() => ({
        status: 500,
        error: {},
      }))
    );

    component.username = 'admin';
    component.password = 'pass';
    component.onSubmit();

    expect(component.error()).toBe('Login failed');
  });

  it('should display generic error for network errors', () => {
    authServiceSpy.login.and.returnValue(
      throwError(() => ({
        status: 0,
        error: null,
      }))
    );

    component.username = 'admin';
    component.password = 'pass';
    component.onSubmit();

    expect(component.error()).toBe('Login failed');
    expect(component.loading()).toBeFalse();
  });

  it('should render error message in the DOM when error signal is set', () => {
    authServiceSpy.login.and.returnValue(
      throwError(() => ({ error: { detail: 'Bad password' } }))
    );

    component.username = 'admin';
    component.password = 'bad';
    component.onSubmit();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const errorDiv = el.querySelector('.bg-red-50');
    expect(errorDiv).toBeTruthy();
    expect(errorDiv?.textContent?.trim()).toContain('Bad password');
  });

  // ─── UI State: Loading ────────────────────────────────────────

  it('should show "Signing in..." text on button while loading', () => {
    component.loading.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.textContent?.trim()).toContain('Signing in...');
    expect(button.disabled).toBeTrue();
  });

  it('should disable submit button while loading', () => {
    component.loading.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBeTrue();
  });

  it('should enable submit button when not loading', () => {
    component.loading.set(false);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(button.disabled).toBeFalse();
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle whitespace-only username as truthy and call login', () => {
    // The component checks !this.username, so whitespace-only passes validation
    // This is actually a potential bug - whitespace usernames would be sent to the server
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: '   ', role: 'ADMIN' })
    );

    component.username = '   ';
    component.password = 'pass';
    component.onSubmit();

    // Whitespace string is truthy, so login IS called
    expect(authServiceSpy.login).toHaveBeenCalled();
  });

  it('should handle rapid sequential submit calls', () => {
    authServiceSpy.login.and.returnValue(
      of({ access_token: 'tok', token_type: 'bearer', username: 'admin', role: 'ADMIN' })
    );

    component.username = 'admin';
    component.password = 'pass';
    component.onSubmit();
    component.onSubmit();
    component.onSubmit();

    expect(authServiceSpy.login).toHaveBeenCalledTimes(3);
  });

  // ─── Accessibility ────────────────────────────────────────────

  it('should have labels associated with inputs via for/id attributes', () => {
    const el: HTMLElement = fixture.nativeElement;
    const usernameLabel = el.querySelector('label[for="username"]');
    const passwordLabel = el.querySelector('label[for="password"]');
    const usernameInput = el.querySelector('input#username');
    const passwordInput = el.querySelector('input#password');

    expect(usernameLabel).toBeTruthy();
    expect(passwordLabel).toBeTruthy();
    expect(usernameInput).toBeTruthy();
    expect(passwordInput).toBeTruthy();
  });

  it('should have required attribute on both inputs', () => {
    const el: HTMLElement = fixture.nativeElement;
    const usernameInput = el.querySelector('input#username') as HTMLInputElement;
    const passwordInput = el.querySelector('input#password') as HTMLInputElement;

    expect(usernameInput.required).toBeTrue();
    expect(passwordInput.required).toBeTrue();
  });

  it('should use type="password" for password field', () => {
    const el: HTMLElement = fixture.nativeElement;
    const passwordInput = el.querySelector('input#password') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
  });

  it('should use type="text" for username field', () => {
    const el: HTMLElement = fixture.nativeElement;
    const usernameInput = el.querySelector('input#username') as HTMLInputElement;
    expect(usernameInput.type).toBe('text');
  });
});
