import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { LayoutComponent } from './layout.component';
import { AuthService } from '../../services/auth.service';

describe('LayoutComponent', () => {
  let component: LayoutComponent;
  let fixture: ComponentFixture<LayoutComponent>;
  let authSpy: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', ['logout', 'getToken'], {
      user: jasmine.createSpy('user').and.returnValue({ username: 'admin', role: 'ADMIN' }),
      isLoggedIn: jasmine.createSpy('isLoggedIn').and.returnValue(true),
      userRole: jasmine.createSpy('userRole').and.returnValue('ADMIN'),
    });

    await TestBed.configureTestingModule({
      imports: [LayoutComponent, RouterTestingModule],
      providers: [{ provide: AuthService, useValue: authSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(LayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ─── Component Creation ───────────────────────────────────────

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // ─── Sidebar Rendering ────────────────────────────────────────

  it('should render the application title', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('Product Counter');
  });

  it('should render the subtitle', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Warehouse Monitoring');
  });

  it('should render all 5 navigation items', () => {
    const el: HTMLElement = fixture.nativeElement;
    const navLinks = el.querySelectorAll('nav a');
    expect(navLinks.length).toBe(5);
  });

  it('should have correct navigation labels', () => {
    const el: HTMLElement = fixture.nativeElement;
    const navLinks = el.querySelectorAll('nav a');
    const labels = Array.from(navLinks).map(link => link.textContent?.trim());

    // Labels include icon emojis prepended, so use partial matching
    expect(labels.some(l => l?.includes('Dashboard'))).toBeTrue();
    expect(labels.some(l => l?.includes('Cameras'))).toBeTrue();
    expect(labels.some(l => l?.includes('Sessions'))).toBeTrue();
    expect(labels.some(l => l?.includes('Reports'))).toBeTrue();
    expect(labels.some(l => l?.includes('System Logs'))).toBeTrue();
  });

  it('should define 5 nav items with correct paths', () => {
    expect(component.navItems.length).toBe(5);
    expect(component.navItems[0].path).toBe('/dashboard');
    expect(component.navItems[1].path).toBe('/cameras');
    expect(component.navItems[2].path).toBe('/sessions');
    expect(component.navItems[3].path).toBe('/reports');
    expect(component.navItems[4].path).toBe('/logs');
  });

  it('should have routerLink attribute on nav links', () => {
    const el: HTMLElement = fixture.nativeElement;
    const navLinks = el.querySelectorAll('nav a');
    navLinks.forEach(link => {
      expect(link.hasAttribute('ng-reflect-router-link') || link.getAttribute('href')).toBeTruthy();
    });
  });

  // ─── User Info ────────────────────────────────────────────────

  it('should display current username', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('admin');
  });

  it('should display user role badge', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('ADMIN');
  });

  // ─── Logout ───────────────────────────────────────────────────

  it('should render sign out button', () => {
    const el: HTMLElement = fixture.nativeElement;
    const logoutBtn = Array.from(el.querySelectorAll('button'))
      .find(b => b.textContent?.trim() === 'Sign out');
    expect(logoutBtn).toBeTruthy();
  });

  it('should call auth.logout() when sign out button is clicked', () => {
    const el: HTMLElement = fixture.nativeElement;
    const logoutBtn = Array.from(el.querySelectorAll('button'))
      .find(b => b.textContent?.trim() === 'Sign out') as HTMLButtonElement;

    logoutBtn.click();
    expect(authSpy.logout).toHaveBeenCalled();
  });

  // ─── Router Outlet ────────────────────────────────────────────

  it('should contain a router-outlet', () => {
    const el: HTMLElement = fixture.nativeElement;
    const outlet = el.querySelector('router-outlet');
    expect(outlet).toBeTruthy();
  });

  // ─── Layout Structure ─────────────────────────────────────────

  it('should have flex layout with sidebar and main', () => {
    const el: HTMLElement = fixture.nativeElement;
    const flexContainer = el.querySelector('.flex.h-screen');
    expect(flexContainer).toBeTruthy();

    const aside = el.querySelector('aside');
    expect(aside).toBeTruthy();

    const main = el.querySelector('main');
    expect(main).toBeTruthy();
  });

  it('should have sidebar with fixed width class', () => {
    const el: HTMLElement = fixture.nativeElement;
    const aside = el.querySelector('aside');
    expect(aside?.classList.contains('w-64')).toBeTrue();
  });

  it('should have main content area with overflow-auto', () => {
    const el: HTMLElement = fixture.nativeElement;
    const main = el.querySelector('main');
    expect(main?.classList.contains('overflow-auto')).toBeTrue();
  });

  // ─── Edge Cases ───────────────────────────────────────────────

  it('should handle null user gracefully', () => {
    (authSpy.user as jasmine.Spy).and.returnValue(null);
    fixture.detectChanges();
    // Should not throw
    expect(component).toBeTruthy();
  });

  it('should display nav items with icons', () => {
    component.navItems.forEach(item => {
      expect(item.icon).toBeTruthy();
      expect(item.icon.length).toBeGreaterThan(0);
    });
  });
});
